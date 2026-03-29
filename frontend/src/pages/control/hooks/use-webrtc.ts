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
    let answerTimer: ReturnType<typeof setTimeout>;
    let candidateTimer: ReturnType<typeof setTimeout>;
    let activeConnectionId: string | null = null;

    const startWebRTC = async () => {
      try {
        // 1. 서버에 새로운 커넥션 ID 발급 요청 (리액트가 주도)
        const { connectionId } = await webrtcApi.createConnection(sessionId).catch((err) => {
          setErrorMsg('시뮬레이터 세션을 찾을 수 없습니다.');
          throw err;
        });
        if (isUnmounted)
          return;
        activeConnectionId = connectionId;

        // 2. PeerConnection 생성
        const pc = new RTCPeerConnection({
          iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
        });
        pcRef.current = pc;

        // 영상 트랙 수신 시 비디오에 연결
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
          }
        };

        // 3. 리액트의 통신 경로(Candidate)를 서버로 전송
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

        // 4. 아주 중요: Offer 생성 전, 영상을 '받기만' 하겠다고 명시
        // 이걸 안 하면 리액트가 빈 Offer를 보내버려서 유니티가 영상을 안 줘.
        pc.addTransceiver('video', { direction: 'recvonly' });

        // 5. Offer 생성 및 Local 세팅
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        if (!offer.sdp)
          throw new Error('SDP 생성 실패');

        // 6. 생성한 Offer를 서버에 전송 (유니티가 이걸 보게 됨)
        await webrtcApi.sendOffer(sessionId, { connectionId: activeConnectionId, sdp: offer.sdp });

        // 7. 유니티가 내 노크에 응답(Answer)을 줬는지 주기적으로 확인
        const pollAnswer = async (lastTime: number) => {
          if (isUnmounted)
            return;
          try {
            const { answers } = await webrtcApi.getAnswers(sessionId, lastTime);
            const currentTime = Date.now();

            // 내 connectionId에 맞는 Answer 찾기
            const targetAnswer = answers?.find(a => a.connectionId === activeConnectionId);

            if (targetAnswer) {
              // 유니티의 응답을 찾았으면 Remote에 세팅
              await pc.setRemoteDescription(new RTCSessionDescription({ type: 'answer', sdp: targetAnswer.sdp }));

              // Answer를 받았으니 이제 Candidate 정보 교환 시작
              pollCandidate(0);
            }
            else {
              answerTimer = setTimeout(pollAnswer, 1000, currentTime);
            }
          }
          catch (err) {
            console.error('Answer Polling Error:', err);
            answerTimer = setTimeout(pollAnswer, 1000, lastTime);
          }
        };

        // 8. 유니티의 Candidate를 가져오기
        const pollCandidate = async (lastTime: number) => {
          if (isUnmounted || !activeConnectionId)
            return;
          try {
            const { candidates } = await webrtcApi.getCandidates(sessionId, lastTime);
            const currentTime = Date.now();

            const targetCandidatesData = candidates?.find(c => c.connectionId === activeConnectionId);

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

        // 최초 실행: Answer 대기 시작
        pollAnswer(0);
      }
      catch {
        if (!errorMsg)
          setErrorMsg('WebRTC 초기화 중 오류가 발생했습니다.');
      }
    };

    startWebRTC();

    return () => {
      isUnmounted = true;
      clearTimeout(answerTimer);
      clearTimeout(candidateTimer);
      pcRef.current?.close();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  return { videoRef, isConnected, errorMsg };
}
