# 스마트 홈 프로젝트 배포 전략 정리 (백엔드 / 인프라 공유용)

> 작성 대상: 백엔드 담당자, 인프라 담당자
> 목적: `server_ai`를 GPU 서버에서 분리 운영하면서도, 전체 서비스는 정상 배포 가능한지 빠르게 공유하기 위한 문서

---

## 1. 결론

현재 프로젝트는 **분리 배포 방식**으로 운영하는 것이 가장 현실적입니다.

- **일반 서버**
  - 프론트엔드
  - 백엔드 메인 서버
  - DB
  - 위 구성은 Docker / Docker Compose 기반 배포
- **GPU 서버**
  - `server_ai` (추천 AI + STT)
  - GPU가 필요한 추론을 담당
  - PM2로 백그라운드 프로세스 관리
- **Jenkins**
  - 배포 자동화 오케스트레이션 담당
  - 일반 서버와 GPU 서버에 각각 다른 방식으로 배포 가능

즉, **"전체를 한 서버에서 통합 Compose로 띄우는 구조"가 아니라**,  
**"메인 서비스는 일반 서버, AI 서비스는 GPU 서버"** 로 나누어 운영하는 구조입니다.

---

## 2. 왜 분리 배포가 필요한가?

`server_ai`는 현재 구조상 백엔드가 HTTP로 호출하는 **독립 AI 서비스**입니다.
또한 STT는 Whisper 기반 추론이 포함되어 있어, 일반 서버보다 GPU 서버에서 운영하는 편이 안정적입니다.

정리하면:

- 추천 AI / STT는 백엔드 내부 모듈이 아니라 **외부 AI API 서버**
- 백엔드는 AI 서버를 **HTTP 클라이언트**로 호출
- GPU 자원이 필요한 추론은 **GPU 서버에서 분리 운영**하는 것이 자연스러움

따라서 AI를 같은 Docker Compose에 억지로 묶는 것보다, **서버는 분리하고 API로 연동**하는 편이 현재 구조와 잘 맞습니다.

---

## 3. 권장 배포 구조

```text
[사용자]
   ↓
[Frontend]
   ↓
[Backend Server + DB]  --------------------------.
   |                                              |
   | HTTP Request                                 | HTTP Response
   '-----> [GPU Server: server_ai (FastAPI)] <----'
```

### 3.1 일반 서버에서 담당하는 것

- 프론트엔드 서비스
- 백엔드 메인 서버
- 데이터베이스
- 필요 시 리버스 프록시(Nginx 등)
- 위 서비스들의 Docker / Docker Compose 운영

### 3.2 GPU 서버에서 담당하는 것

- 추천 AI API 서버
- STT API 서버
- 추후 필요 시 모델 캐시/가중치 보관

---

## 4. 서버별 실행 방식

### 4.1 일반 서버

일반 서버는 기존 계획대로 프론트엔드 / 백엔드 / DB를 Docker 기반으로 띄우면 됩니다.

예시:

- `frontend`
- `backend`
- `database`

이 세 서비스는 같은 Docker 네트워크 안에서 통신하고,  
백엔드는 외부의 GPU 서버 AI API를 호출합니다.

### 4.2 GPU 서버

GPU 서버의 `server_ai`는 PM2 프로세스 관리자로 운영합니다.

#### PM2 프로세스 관리자로 실행

PM2를 사용하여 각 AI 서비스를 백그라운드에서 안정적으로 운영하는 방식입니다.

**사전 준비 (최초 1회)**

```bash
# Node.js 설치 후 PM2 글로벌 설치
npm install -g pm2
```

**서비스 실행**

```bash
# 추천 AI 서비스 실행
cd my_project/server_ai/recommendation
pm2 start main.py --name "ai-rec" --interpreter python

# STT 서비스 실행
cd my_project/server_ai/stt
pm2 start main.py --name "ai-stt" --interpreter python
```

**유용한 PM2 명령어**

```bash
pm2 list          # 실행 중인 프로세스 목록 확인
pm2 logs          # 실시간 로그 확인
pm2 restart all   # 전체 재시작
pm2 stop all      # 전체 중지
pm2 save          # 현재 프로세스 목록 저장 (재부팅 대응)
pm2 startup       # 서버 재부팅 시 자동 시작 등록
```

장점:

- 터미널 창 없이 백그라운드 실행 가능
- 오류 발생 시 자동 재시작
- 서버 재부팅 시에도 자동 복구 가능 (`pm2 startup` + `pm2 save`)
- 여러 서비스의 로그를 한곳에서 관리 가능

---

## 5. Jenkins 기준 권장 배포 흐름

Jenkins를 사용하더라도, **배포 대상이 둘로 나뉘는 것**은 전혀 문제되지 않습니다.

핵심은 Jenkins가 "한 서버에 모두 배포"하는 도구가 아니라,  
**필요한 서버들에 각각 맞는 명령을 실행해주는 자동화 도구**라는 점입니다.

### 5.1 권장 구조

- **Job 1. 메인 서비스 배포**
  - 대상: 일반 서버
  - 내용: 프론트엔드 / 백엔드 / DB 관련 Docker 배포
- **Job 2. AI 서비스 배포**
  - 대상: GPU 서버
  - 내용: `server_ai` 최신화 후 AI 서비스 재시작 (9000, 9001 포트)

### 5.2 예시 배포 흐름

```text
Git Push
  ↓
Jenkins Pipeline
  ├─ 일반 서버: Docker Compose 배포
  └─ GPU 서버: SSH 접속 → server_ai 최신화 → AI 서버 재시작
```

### 5.3 GPU 서버 배포 시 Jenkins가 할 수 있는 일

Jenkins가 GPU 서버에 SSH로 접속해서 아래 흐름을 수행합니다.

1. 지정 브랜치 pull
2. `server_ai/` 최신화
3. 가상환경 활성화 또는 의존성 반영
4. PM2로 AI 서비스 재시작 (`pm2 restart ai-rec ai-stt`)
5. STT 헬스체크로 기동 상태 확인 (`curl http://127.0.0.1:9001/api/stt/health`)

### 5.4 STT 운영 확인 포인트

배포 후 최소 확인 기준:

```sh
curl http://127.0.0.1:9001/api/stt/health
```

응답에서 아래를 확인합니다.

- `status=ok`
- `device=cuda`
- `model_path`가 기대한 모델 경로인지
- `room_map_source`가 환경에 따라 `fallback` 또는 `backend`인지

---

## 6. Git Sparse-Checkout의 역할

GPU 서버에는 모노레포 전체가 아니라 **`server_ai/`만 부분 복제**해도 됩니다.

이 방식의 목적은:

- GPU 서버에 불필요한 프론트/백엔드 코드까지 올리지 않기
- AI 코드만 빠르게 동기화하기
- GPU 서버를 `AI 전용 실행 환경`으로 유지하기

즉, GPU 서버는 **배포 대상 전체를 담는 서버가 아니라, AI 서비스만 올리는 별도 실행 서버**로 이해하면 됩니다.

---

## 7. 백엔드에서 준비해야 할 사항

### 7.1 AI 서버 주소를 환경변수로 분리

백엔드는 GPU 서버의 AI API 주소를 환경변수로 관리해야 합니다.

예시:

```env
AI_RECOMMENDATION_BASE_URL=http://GPU_SERVER_IP:9000
AI_STT_BASE_URL=http://GPU_SERVER_IP:9001
```

### 7.2 AI 호출 시 필수 처리

- HTTP timeout 설정
- 예외 발생 시 fallback 응답 처리
- AI 서버 장애가 메인 서비스 장애로 전파되지 않도록 격리

권장:

- Read timeout: 30초 이상
- AI 실패 시 사용자에게 안내 메시지 반환

### 7.3 데이터 전달 방식 유지

AI 서버는 DB에 직접 접근하지 않고,  
백엔드가 최근 이력 데이터를 조회한 뒤 JSON으로 전달합니다.

즉, 백엔드가 해야 할 역할은:

- 최근 14일치 센서 로그 조회
- 모듈 제어 로그 조회
- AI 요청용 JSON 생성
- AI 응답을 사용자 제안 또는 자동화 로직에 반영

---

## 8. 인프라에서 준비해야 할 사항

### 8.1 네트워크

- 백엔드 서버에서 GPU 서버의 AI 포트 접근 가능해야 함
- 최소 필요 포트:
  - `9000` 추천 AI API
  - `9001` STT API

내부망 / 방화벽 / 보안그룹 정책에 따라 아래를 확인해야 합니다.

- 백엔드 서버 -> GPU 서버 outbound 허용
- GPU 서버 -> AI 포트 inbound 허용

### 8.2 프로세스 유지

GPU 서버에서 AI 서버가 꺼지지 않도록 **PM2**를 사용하여 프로세스를 관리합니다.

**권장 도구: PM2**

- 오류 발생 시 자동 재시작
- 서버 재부팅 후 자동 복구 (`pm2 startup` + `pm2 save`)
- 로그 통합 관리
- GPU Docker 환경 없이도 안정적 운영 가능

```bash
# 최초 설정 (서버 재부팅 시 자동 시작 등록)
pm2 startup
pm2 save
```



### 8.3 도메인 / 주소 관리

최소한 아래 중 하나는 고정되어야 합니다.

- GPU 서버의 고정 IP
- 내부 DNS 이름
- Reverse Proxy 기반 도메인

백엔드는 이 주소를 기준으로 AI 서버를 호출합니다.

### 8.4 Jenkins 배포 준비

Jenkins를 사용할 경우 아래 항목도 함께 준비되어야 합니다.

- Jenkins -> 일반 서버 배포 권한
- Jenkins -> GPU 서버 SSH 접속 권한
- 배포용 SSH Key / Credential 등록
- 서버별 환경변수 관리 분리
- 서버별 재시작 명령 분리

권장:

- 일반 서버 배포 Job과 GPU 서버 배포 Job을 분리
- 롤백 시에도 서버별로 독립 복구 가능하게 구성
- AI 서버 배포 실패가 메인 서비스 배포 실패로 바로 번지지 않게 분리

---

## 9. Jenkins 사용 시 권장 파이프라인 예시

아래처럼 한 Pipeline 안에서 단계를 나누거나, 아예 Job을 분리할 수 있습니다.

### 예시 A. Job 분리형

- `deploy-main-services`
  - 프론트 / 백엔드 / DB 배포
- `deploy-ai-services`
  - GPU 서버의 `server_ai` 배포

장점:

- 장애 원인 추적이 쉬움
- AI만 재배포하기 편함
- GPU 서버 이슈가 일반 서버 배포에 영향 덜 줌

### 예시 B. Pipeline 통합형

1. 코드 체크아웃
2. 테스트
3. 일반 서버 Docker 배포
4. GPU 서버 AI 배포
5. 헬스체크

이 경우에도 **실행 대상 서버는 분리**된다는 점은 동일합니다.

---

## 10. 현재 기준 권장안

현재 프로젝트 상황에서는 아래 방식을 권장합니다.

### 권장안

- **일반 서버**
  - 프론트엔드 / 백엔드 / DB를 Docker Compose로 운영
- **GPU 서버**
  - `server_ai`만 `sparse-checkout`으로 가져옴
  - 추천 API / STT API를 **PM2**로 백그라운드 실행 및 관리
  - `pm2 startup` + `pm2 save`로 서버 재부팅 대응
- **Jenkins**
  - 일반 서버용 배포 Job
  - GPU 서버용 배포 Job (`pm2 restart`로 AI 서비스 재시작)
  - 또는 하나의 Pipeline 안에서 두 서버를 순차 배포
- **백엔드**
  - GPU 서버 AI API를 HTTP로 호출
  - timeout / fallback 포함

이 방식의 장점:

- AI의 GPU 의존성을 일반 서버 배포와 분리 가능
- 인프라 문제 발생 시 원인 분리가 쉬움
- 현재 문서화된 `Stateless API` 구조와 가장 잘 맞음

---

## 11. 추후 확장 가능 방향

향후 인프라가 안정화되면 아래와 같은 확장도 가능합니다.

### 선택지. 추천 AI만 일반 서버로 이동

- 추천 AI는 CPU 부하가 낮으면 일반 서버 Compose에 편입
- STT만 GPU 서버에 남기는 하이브리드 구조 가능

---

## 12. 최종 정리

**질문:** "배포를 한꺼번에 하지 않고, 백엔드는 일반 서버 Docker / AI는 GPU 서버 분리 운영이 가능한가?"

**답:** 가능합니다. 그리고 현재 프로젝트 구조에서는 그 방식이 가장 현실적입니다.

실무적으로는 아래처럼 이해하면 됩니다.

- 백엔드/프론트: 일반 서버에서 Docker 배포
- AI 서버: GPU 서버에서 별도 운영
- 양쪽 연결: HTTP API 호출
- Jenkins: 두 서버에 각각 맞는 방식으로 배포 자동화

즉, **분리 배포는 예외적인 방식이 아니라, 현재 AI 요구사항(GPU, 독립 API 구조)에 잘 맞는 정상적인 배포 전략**입니다.

---

## 13. 함께 보면 좋은 문서

- `backend_integration_proposal.md`
- `git_sparse_guide.md`
