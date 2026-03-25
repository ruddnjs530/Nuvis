import { useEffect, useRef, useState } from 'react';

// 시그널링 서버와 주고받을 메시지 타입 (백엔드 통신 스펙에 맞춰 수정 필요)
interface SignalingMessage {
  type: 'offer' | 'answer' | 'candidate';
  sdp?: RTCSessionDescriptionInit;
  candidate?: RTCIceCandidateInit;
}

export function useWebRTC(signalingUrl: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // 실제 서버 주소가 설정되지 않은 경우 (UI 작업 단계를 위해) 실행 방지
    if (!signalingUrl)
      return;

    try {
      const ws = new WebSocket(signalingUrl);
      wsRef.current = ws;

      // 1. WebRTC PeerConnection 생성
      // 구글 퍼블릭 STUN 서버 사용 (ICE Candidate 수집용)
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
      });
      pcRef.current = pc;

      // 2. 외부에서 수신된 미디어 트랙을 비디오 태그에 연결
      pc.ontrack = (event) => {
        if (videoRef.current && event.streams[0]) {
          videoRef.current.srcObject = event.streams[0];
          // 트랙이 들어오면 화면이 나왔다고 간주
          setIsConnected(true);
        }
      };

      // 3. ICE 상태 변경 감지 및 UI 업데이트
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

      // 4. 내 네트워크 주소(ICE)가 파악되면 시그널링 서버를 통해 상대방에게 전달
      pc.onicecandidate = (event) => {
        if (event.candidate && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'candidate', candidate: event.candidate }));
        }
      };

      // 5. 시그널링 서버 연결 성공 시 핸들러
      ws.onopen = () => {
        setErrorMsg(null);

        // [클라이언트가 먼저 Offer를 보내는 구조일 경우 활성화]
        /*
        pc.createOffer().then(offer => {
           pc.setLocalDescription(offer);
           ws.send(JSON.stringify({ type: 'offer', sdp: offer }));
        });
        */
      };

      // 6. 시그널링 서버로부터 메시지(Offer, Answer, Candidate) 수신 시 핸들러
      ws.onmessage = async (event) => {
        try {
          const message: SignalingMessage = JSON.parse(event.data);

          // 유니티 쪽에서 먼저 Offer를 보냈을 경우
          if (message.type === 'offer' && message.sdp) {
            await pc.setRemoteDescription(new RTCSessionDescription(message.sdp));
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);
            ws.send(JSON.stringify({ type: 'answer', sdp: answer }));
          }
          // 내가 보낸 Offer에 대한 Answer를 받았을 경우
          else if (message.type === 'answer' && message.sdp) {
            await pc.setRemoteDescription(new RTCSessionDescription(message.sdp));
          }
          // 상대방의 네트워크 주소(ICE)를 받았을 경우 등록
          else if (message.type === 'candidate' && message.candidate) {
            await pc.addIceCandidate(new RTCIceCandidate(message.candidate));
          }
        }
        catch (err) {
          console.error('Signaling message parsing failed:', err);
        }
      };

      ws.onerror = () => {
        setErrorMsg('시그널링 서버 연결에 실패했습니다.');
        setIsConnected(false);
      };

      ws.onclose = () => {
        setIsConnected(false);
      };

      // 컴포넌트 언마운트 시 자원 정리 (메모리 누수 방지)
      return () => {
        pc.close();
        ws.close();
      };
    }
    catch (err: any) {
      const timer = setTimeout(setErrorMsg, 0, err.message);
      return () => clearTimeout(timer);
    }
  }, [signalingUrl]);

  return { videoRef, isConnected, errorMsg };
}
