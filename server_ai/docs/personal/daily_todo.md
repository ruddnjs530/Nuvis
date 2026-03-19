# 📝 오늘의 할 일 (Daily To-Do List)

> **담당:** AI 서버 (`server_ai`) 중심 작업 기록, 백엔드 연동 작업 포함  
> 이 문서는 매일 아침 전날 작업 내역을 체크하고, 오늘의 목표를 갱신하는 일일 업무 로깅 문서입니다.

---

## 🕒 2026-03-16 (현재)
**[목표] 모노레포 역할 경계 정리 + 문서 기준 통일 + 배포 전략 공유안 정리**

### ✅ 완료한 작업 (Done)

#### 🏗️ 구조 정리
- [x] `server_ai`를 추천 AI + STT 전용 서비스로 분리하는 방향 확정
- [x] YOLO는 현재 프로토타입 기록은 유지하되, 최종 배치는 `ros2_ws` 측 비전 패키지로 재정리하기로 결정
- [x] AI가 `scheduler` 내부 모듈이 아니라 백엔드가 호출하는 독립 서비스라는 기준 정리

#### 🗂️ 문서 반영
- [x] 루트 `README.md` 설명 업데이트
- [x] `server_ai/README.md` 책임 범위 설명 업데이트
- [x] `dev_log.md`, `portfolio.md`, `ai_roadmap.md`, `backend_integration_proposal.md`에 구조 결정 사항 반영
- [x] `docker_deployment_guide.md`에 AI API 서버 / ROS2 비전 노드 분리 기준 반영

#### 🚀 배포 / 운영 전략 정리
- [x] GPU 서버에서 `server_ai`만 부분 복제하는 `git sparse-checkout` 운영 방식 재검토
- [x] 일반 서버(Docker) + GPU 서버(`server_ai`) 분리 배포 구조 타당성 정리
- [x] Jenkins 사용 시 일반 서버와 GPU 서버를 분리 배포할 수 있는 흐름 정리
- [x] 백엔드 / 인프라 공유용 `deployment_strategy_for_backend_and_infra.md` 신규 작성

### 🔴 다음 할 일 (Next)

#### 🤖 AI 서버
- [ ] `recommendation/` mock 데이터 컬럼명과 실제 API 계약(`air_purifier_on`) 일치시키기
- [ ] `test_client.py`를 현재 `POST /api/event/ai-suggestions` 계약에 맞게 수정
- [ ] GPU 서버에서 `git_sparse_guide.md` 기준으로 `server_ai/` 부분 복제 및 실행 검증

#### 🔵 백엔드 / 인프라 협업
- [ ] `backend_integration_proposal.md`와 `deployment_strategy_for_backend_and_infra.md` 전달
- [ ] AI 서버 주소 / Timeout / Fallback / Jenkins 배포 방식 합의

#### 🤖 YOLO / ROS2
- [ ] `server_ai/vision/` 프로토타입을 기준으로 추후 `ros2_ws` 측 패키지 구조안 확정
- [ ] YOLO 재배치 시점은 ROS2 통합 규격 정리 후 결정

---

## 🕒 2026-03-13 (현재)
**[목표] AI 안전장치 적용 + 백엔드 초기 세팅 + 문서 구조 정리**

### ✅ 완료한 작업 (Done)

#### 🤖 AI 서버
- [x] `recommendation/main.py` 페이로드 상한선(`MAX_RECORDS=500`) 적용
- [x] 기기별 독립 타임아웃(`ANALYSIS_TIMEOUT=5.0`) + asyncio Fallback 처리
- [x] 로깅 체계(`import logging`) 추가

#### 🔵 백엔드 서버
- [x] `server_backend/` 폴더 초기 구조 생성
- [x] 공용 docs/ 구성 확인

#### 🗂️ 문서 구조 정리
- [x] 모노레포 루트 `docs/` 공용 허브 생성
- [x] 공용 문서 이동 (ERD, MVP, API 명세서, 아키텍처, Docker 가이드, 자동화 논의)
- [x] `backend_request_to_backend_team.md` → `backend_integration_proposal.md` 리네임
- [x] `server_ai/README.md` 링크 업데이트
- [x] `server_ai/docs/personal/` 통합 정리

### 🔴 내일 할 일 (To-Do for Tomorrow)

#### 🤖 AI 서버
- [ ] 스케줄 추천 기능 실제 코드 구현 (`recommendation/main.py`에 `analyze_schedule_patterns()` 함수 및 엔드포인트 추가)
- [ ] `generate_mock_data.py` 보강 — 저녁 19시 시간 패턴이 포함된 Mock 데이터 생성 로직 추가
- [ ] GPU 서버에서 `docs/shared/git_sparse_guide.md` 가이드대로 `server_ai/` 폴더 클론 작동 여부 직접 검증

#### 🔵 백엔드 서버
- [ ] 기술 스택 확정 및 프로젝트 초기 세팅
- [ ] `ROOM_CONDITIONS_HISTORY` 테이블 추가 (AI 팀 요청)
- [ ] `MODULE_CONTROL_LOGS` 테이블 추가 (AI 팀 요청)
- [ ] AI 서버 HTTP 클라이언트 모듈 뼈대 구현 (Timeout 30초, Fallback 처리 포함)

---

## 📦 아카이브 — 2026-03-12
**[목표] AI-백엔드 연동 설계 확정 및 GPU 서버 개발 환경 정비**

### ✅ 완료한 작업 (Done)
- [x] AI ↔ 백엔드 연동 방식 확정 (Stateless API / Data Passing 방식)
- [x] MVP 추천 파이프라인 전체 흐름 구체화 (Human-in-the-loop)
- [x] ERD 검토 및 시계열 이력 테이블 2개 공식 추가 요청
  - `ROOM_CONDITIONS_HISTORY` (센서 이력 누적)
  - `MODULE_CONTROL_LOGS` (기기 조작 로그)
- [x] 다중 기기 타입 확장성 검증 (공기청정기/가습기/제습기 동일 로직 재사용 가능 확인)
- [x] 완전 자동화(2차 고도화) 시나리오 및 안전장치 설계 가이드 문서화
- [x] `backend_integration_proposal.md` 연동 제안서 작성 완료
- [x] GPU 서버 SFTP 접속 불가 원인 파악 (웹 환경 포트 차단)
- [x] `git sparse-checkout` 방식으로 모노레포 동기화 전략 전환 결정
- [x] `docs/shared/git_sparse_guide.md` GPU 서버 연동 가이드 신규 작성

---

## 📦 아카이브 — 2026-03-10
**[목표] AI 파트 초기 설계 및 프로토타입 뼈대 구축 완료하기**

### ✅ 완료한 작업 (Done)
- [x] MVP 및 API 명세서 기반 프로젝트 전체 구조 파악
- [x] AI 파트 역할 분리 및 명명 (SLAM/주행 제외, 비전/추천/STT에 집중)
- [x] ROS2 YOLO 비전 노드 베이스 구성 (`yolo_node.py`)
- [x] 가상 스마트 홈 IoT 환경 데이터 생성 모듈 제작 (`generate_mock_data.py`)
- [x] Pandas 통계 기반 추천 알고리즘 FastAPI 서버 생성 (`main.py`)
- [x] Whisper 모델 파이프라인 및 STT 명령어 파서 구축 (`stt_parser.py`, `whisper_test.py`)
- [x] AI 초기 설계 문서 및 로드맵 문서화
- [x] 파이썬 가상환경(`venv`) 패키지 셋업
