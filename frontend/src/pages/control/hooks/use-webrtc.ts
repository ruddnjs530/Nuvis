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

        const { connectionId } = await webrtcApi.createConnection(sessionId).catch((err) => {
          setErrorMsg('시뮬레이터를 먼저 연결해 주세요.');
          throw err;
        });

        if (isUnmounted)
          return;

        pc.onicecandidate = (event) => {
          if (event.candidate) {
            webrtcApi.sendCandidate(sessionId, {
              connectionId,
              candidate: event.candidate.candidate,
              sdpMLineIndex: event.candidate.sdpMLineIndex,
              sdpMid: event.candidate.sdpMid,
            }).catch(console.error);
          }
        };

        const pollOffer = async (lastTime: number) => {
          if (isUnmounted)
            return;
          try {
            const { offers } = await webrtcApi.getOffers(sessionId, lastTime);
            const currentTime = Date.now();
            const myOffer = offers.find(o => o.connectionId === connectionId);

            if (myOffer) {
              await pc.setRemoteDescription(new RTCSessionDescription({ type: 'offer', sdp: myOffer.sdp }));
              const answer = await pc.createAnswer();
              await pc.setLocalDescription(answer);

              // 추가된 부분: sdp가 없는 경우를 방어하는 타입 가드
              if (!answer.sdp) {
                throw new Error('SDP 생성에 실패했습니다.');
              }

              // 이제 TypeScript가 answer.sdp를 확실한 string으로 인식해
              await webrtcApi.sendAnswer(sessionId, { connectionId, sdp: answer.sdp });

              pollCandidate(0);
            }
            else {
              offerTimer = setTimeout(pollOffer, 1000, currentTime);
            }
          }
          catch (err) {
            console.error('Offer Polling Error:', err);
            offerTimer = setTimeout(pollOffer, 1000, lastTime);
          }
        };

        const pollCandidate = async (lastTime: number) => {
          if (isUnmounted)
            return;
          try {
            const { candidates } = await webrtcApi.getCandidates(sessionId, lastTime);
            const currentTime = Date.now();
            const myCandidatesData = candidates.find(c => c.connectionId === connectionId);

            if (myCandidatesData && myCandidatesData.candidates) {
              for (const cand of myCandidatesData.candidates) {
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

        pollOffer(0);
      }
      catch {
        setErrorMsg('WebRTC 초기화 중 오류가 발생했습니다.');
      }
    };

    startWebRTC();

    return () => {
      isUnmounted = true;
      clearTimeout(offerTimer);
      clearTimeout(candidateTimer);
      pcRef.current?.close();
    };
  }, [sessionId]);

  return { videoRef, isConnected, errorMsg };
}
