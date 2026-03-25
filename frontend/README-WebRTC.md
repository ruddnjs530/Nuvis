# 🎥 스마트홈 로봇 WebRTC 연동 가이드 (Frontend)

이 문서는 스마트홈 환경에서 돌아다니는 유니티(Unity) 로봇의 **카메라 시점 영상**을 프론트엔드(React/웹)에 초저지연 실시간으로 띄우기 위한 **WebRTC 시그널링 연동 방법**을 설명합니다.

---

## 1. 📖 아키텍처 개요

WebRTC는 P2P(Peer-to-Peer) 영상 스트리밍 기술로, 유니티 로봇과 사용자 웹 브라우저가 직접 통신합니다. 하지만 두 기기가 서를 찾기 위해서는 중간에서 연락처(SDP, ICE)를 교환해 줄 중계소가 필요하며, 이를 **'시그널링 서버(Signaling Server)'**라고 부릅니다.

- **Unity 방식**: Unity 공식 패키지인 `RenderStreaming`의 기본 통신 방식인 **HttpSignaling(폴링)** 방식을 채택했습니다.
- **Backend 방식**: 웹소켓(`ws://`) 충돌 및 포트 개방 이슈를 없애기 위해, 순수 **REST API(HTTP)** 형태로 시그널링 서버를 백엔드에 내장했습니다. (`/api/signaling` 경로 사용)

---

## 2. 📡 시그널링 API 엔드포인트 명세서

프론트엔드는 다음의 API들을 1~2초 간격으로 `Polling`(주기적 GET 요청)하면서 유니티와 연락처를 교환해야 합니다.

### 2.1 세션 관리
1. `PUT /api/signaling`
   - **기능:** WebRTC 전체 세션 방(Room) 생성
   - **응답:** `{ "sessionId": "UUID문자열" }`
2. `PUT /api/signaling/connection`
   - **기능:** 내 기기의 고유 연결 ID 생성
   - **헤더:** `Session-Id: 발급받은 sessionId`
   - **응답:** `{ "connectionId": "UUID문자열" }`
3. `DELETE /api/signaling`
   - **기능:** 영상 통화 종료 시 세션 파기
   - **헤더:** `Session-Id: 발급받은 sessionId`

### 2.2 메세지 폴링 (Offer, Answer, Candidate)
위에서 얻은 `Session-Id`를 헤더에 넣고, 상대방의 데이터가 있는지 지속적으로 확인합니다. 
> `fromtime` 쿼리는 마지막으로 응답을 확인한 시간(UTC 밀리초)입니다. 누락된 데이터만 받아오기 위해 활용합니다.

- **Offer (영상 제안서)**
  - `POST /api/signaling/offer` : 내 Offer를 업로드 (Body: `{ "connectionId": "내ID", "sdp": "...", "type": "offer" }`)
  - `GET /api/signaling/offer?fromtime=0` : 상대방이 올린 Offer 목록 다운로드
- **Answer (영상 수락서)**
  - `POST /api/signaling/answer` : 내 Answer 업로드 (Body 형태는 Offer와 동일)
  - `GET /api/signaling/answer?fromtime=...` : 상대방의 Answer 목록 다운로드
- **ICE Candidate (네트워크 경로)**
  - `POST /api/signaling/candidate` : 내 ICE 후보군 업로드
  - `GET /api/signaling/candidate?fromtime=...` : 상대방 ICE 후보군 다운로드

---

## 3. 💻 프론트엔드 연동 순서 (Step-by-Step)

WebRTC의 기본인 `RTCPeerConnection` API를 이용해 P2P를 맺는 순서입니다.

### Step 1. 연결 객체 생성
```javascript
// 구글 공개 STUN 서버를 사용하여 내 공인 주소를 찾게 함
const peerConnection = new RTCPeerConnection({
  iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
});

// 영상 트랙(비디오)이 들어오면 HTML Video 에 연결
peerConnection.ontrack = (event) => {
  const videoElem = document.getElementById("robot-video");
  videoElem.srcObject = event.streams[0];
  videoElem.play();
};
```

### Step 2. 세션 발급 받기
```javascript
// 1. 방 만들기 (또는 유니티가 만든 방 번호를 공유받기)
const res = await fetch('/api/signaling', { method: 'PUT' });
const { sessionId } = await res.json();

// 2. 내 고유 ID 만들기
const connRes = await fetch('/api/signaling/connection', {
  method: 'PUT',
  headers: { 'Session-Id': sessionId }
});
const { connectionId } = await connRes.json();
```

### Step 3. 지속적 Polling (상대방 데이터 확인)
자바스크립트의 `setInterval`을 이용해 유니티가 보낸 Offer와 ICE Candidate를 받아옵니다.
```javascript
let lastTime = 0;

setInterval(async () => {
    // 1. 유니티가 보낸 Offer 찾기
    const offRes = await fetch(`/api/signaling/offer?fromtime=${lastTime}`, {
        headers: { 'Session-Id': sessionId }
    });
    const offData = await offRes.json();
    
    // 만약 새로운 Offer가 있다면?
    if (offData.offers && offData.offers.length > 0) {
        const offer = offData.offers[0];
        
        // 내 PC에 상대방 정보 셋팅
        await peerConnection.setRemoteDescription({ type: 'offer', sdp: offer.sdp });
        
        // 나는 Answer(수락서) 생성해서 셋팅
        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);

        // 내 Answer를 유니티가 보도록 업로드
        await fetch('/api/signaling/answer', {
            method: 'POST',
            headers: { 'Session-Id': sessionId, 'Content-Type': 'application/json' },
            body: JSON.stringify({
                connectionId: connectionId,
                sdp: answer.sdp,
                type: 'answer'
            })
        });
    }

    // 2. 유니티가 보낸 빙글빙글 도는 네트워크 주소(ICE) 찾아서 적용하기
    const iceRes = await fetch(`/api/signaling/candidate?fromtime=${lastTime}`, {
        headers: { 'Session-Id': sessionId }
    });
    const iceData = await iceRes.json();
    iceData.candidates.forEach(container => {
        container.candidates.forEach(cand => {
            peerConnection.addIceCandidate(new RTCIceCandidate({
                candidate: cand.candidate,
                sdpMid: cand.sdpMid,
                sdpMLineIndex: cand.sdpMLineIndex
            }));
        });
    });

    // 시간 최신화
    lastTime = Date.now();
}, 2000); // 2초 주기
```

### Step 4. 내 네트워크 주소(ICE) 업로드
내 브라우저가 네트워크 환경 데이터를 찾아내면 백엔드에 올려서 유니티가 가져가게 합니다.
```javascript
peerConnection.onicecandidate = async (event) => {
  if (event.candidate) {
    await fetch('/api/signaling/candidate', {
        method: 'POST',
        headers: { 'Session-Id': sessionId, 'Content-Type': 'application/json' },
        body: JSON.stringify({
            connectionId: connectionId,
            candidate: event.candidate.candidate,
            sdpMid: event.candidate.sdpMid,
            sdpMLineIndex: event.candidate.sdpMLineIndex
        })
    });
  }
};
```

---

## 4. 🥇 라이브러리를 활용한 초간단 연동 방법 (권장)

위처럼 1~2초마다 Polling하는 것을 일일이 구현하기 귀찮다면, Unity 측에서 웹 구동을 위해 공식 배포한 **자바스크립트용 NPM 패키지**를 사용하시면 됩니다.

1. NPM 설치: `npm install @unity/webrtc` (사내망이나 프로젝트 환경에 따라 달라질 수 있음)
2. **`URL` 셋팅**: `webrtc` 라이브러리의 Signaling Server 주소를 `http://백엔드주소/api` (또는 Nginx 프록시)로만 맞춰주면 내부적으로 알아서 폴링하고, 알아서 `<video>` 태그에 영상을 꽂아줍니다!

### 도커(Docker) 환경 주의사항
- 도커를 쓰신다면 `3000`번 포트가 막혀 있습니다. 프론트엔드의 Nginx 라우팅(`frontend/nginx.conf`) 파일에서 다음과 같이 포워딩이 열려있어야 합니다.
```nginx
location /signaling/ {
    proxy_pass http://backend:3000;
    proxy_set_header Host $host;
}
```
위 규칙이 성립되어야 프론트가 쏘는 `/api/signaling/...` 요청이 올바르게 중계서버에 닿을 수 있습니다.
