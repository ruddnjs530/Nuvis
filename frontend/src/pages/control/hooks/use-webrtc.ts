import { useEffect, useRef, useState } from 'react';
import { webrtcApi } from '../api/api';

export function useWebRTC(sessionId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);

  useEffect(() => {
    if (!sessionId)
      return;

    let isUnmounted = false;
    let offerTimer: ReturnType<typeof setTimeout>;
    let candidateTimer: ReturnType<typeof setTimeout>;

    // 유니티가 발급한 커넥션 ID를 저장할 변수
    let activeConnectionId: string | null = null;

    const startWebRTC = async () => {
      try {
        const pc = new RTCPeerConnection({
          iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
        });
        pcRef.current = pc;

        pc.ontrack = (event) => {
          if (videoRef.current && event.streams[0]) {
            videoRef.current.srcObject = event.streams[0];
          }
        };

        pc.oniceconnectionstatechange = () => {
          if (pc.iceConnectionState === 'disconnected' || pc.iceConnectionState === 'failed') {
            setIsConnected(false);
            setErrorMsg('WebRTC 연결이 끊어졌습니다.');
          }
          else if (pc.iceConnectionState === 'connected') {
            setIsConnected(true);
            setErrorMsg(null);
            clearTimeout(candidateTimer);
          }
        };

        // 내 네트워크 경로가 발견되면 유니티의 Connection ID를 타겟으로 전송
        pc.onicecandidate = (event) => {
          if (event.candidate && activeConnectionId) {
            webrtcApi.sendCandidate(sessionId, {
              connectionId: activeConnectionId,
              candidate: event.candidate.candidate,
              sdpMLineIndex: event.candidate.sdpMLineIndex,
              sdpMid: event.candidate.sdpMid,
            }).catch(console.error);
          }
        };

        // 유니티가 올린 Offer 찾기
        const pollOffer = async (lastTime: number) => {
          if (isUnmounted)
            return;
          try {
            const { offers } = await webrtcApi.getOffers(sessionId, lastTime);
            const currentTime = Date.now();

            // 배열에 Offer가 하나라도 들어왔다면 가장 최신 것을 선택
            if (offers && offers.length > 0) {
              const targetOffer = offers.at(-1)!;

              // 핵심: 유니티가 만든 커넥션 ID를 리액트가 그대로 흡수함
              activeConnectionId = targetOffer.connectionId;

              await pc.setRemoteDescription(new RTCSessionDescription({ type: 'offer', sdp: targetOffer.sdp }));
              const answer = await pc.createAnswer();
              await pc.setLocalDescription(answer);

              if (!answer.sdp)
                throw new Error('SDP 생성 실패');

              // 유니티의 커넥션 ID를 달아서 Answer 전송
              await webrtcApi.sendAnswer(sessionId, {
                connectionId: activeConnectionId,
                sdp: answer.sdp,
              });

              // Answer 전송 후 유니티의 Candidate 정보 폴링 시작
              pollCandidate(0);
            }
            else {
              // 배열이 비어있으면 1초 뒤 다시 시도
              offerTimer = setTimeout(pollOffer, 1000, currentTime);
            }
          }
          catch (err) {
            console.error('Offer Polling Error:', err);
            offerTimer = setTimeout(pollOffer, 1000, lastTime);
          }
        };

        // 유니티의 Candidate 가져오기
        const pollCandidate = async (lastTime: number) => {
          if (isUnmounted || !activeConnectionId)
            return;
          try {
            const { candidates } = await webrtcApi.getCandidates(sessionId, lastTime);
            const currentTime = Date.now();

            // 유니티의 커넥션 ID와 일치하는 데이터만 추출
            const targetCandidatesData = candidates.find(c => c.connectionId === activeConnectionId);

            if (targetCandidatesData && targetCandidatesData.candidates) {
              for (const cand of targetCandidatesData.candidates) {
                await pc.addIceCandidate(new RTCIceCandidate({
                  candidate: cand.candidate,
                  sdpMLineIndex: cand.sdpMLineIndex,
                  sdpMid: cand.sdpMid,
                }));
              }
            }

            if (pc.iceConnectionState !== 'connected') {
              candidateTimer = setTimeout(pollCandidate, 1000, currentTime);
            }
          }
          catch (err) {
            console.error('Candidate Polling Error:', err);
            candidateTimer = setTimeout(pollCandidate, 1000, lastTime);
          }
        };

        // 최초 실행: Offer 폴링 시작
        pollOffer(0);
      }
      catch {
        if (!errorMsg) {
          setErrorMsg('WebRTC 초기화 중 오류가 발생했습니다.');
        }
      }
    };

    startWebRTC();

    return () => {
      isUnmounted = true;
      clearTimeout(offerTimer);
      clearTimeout(candidateTimer);
      pcRef.current?.close();
    };
  }, [errorMsg, sessionId]);

  return { videoRef, isConnected, errorMsg };
}
