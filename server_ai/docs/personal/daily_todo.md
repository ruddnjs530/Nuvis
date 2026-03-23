# 📝 오늘의 할 일 (Daily To-Do List)

> **담당:** AI 서버 (`server_ai`) 개발 및 백엔드 연동 협업 기록  
> 이 문서는 매일 아침 전날 작업 내역을 체크하고, 오늘의 목표를 갱신하는 일일 업무 로깅 문서입니다.

---

## 📦 아카이브 — 2026-03-19
**[목표] GPU 서버 동기화 문제 해결 + Whisper 파인튜닝 completion + 추천 시스템 AI 고도화**

### ✅ 완료한 작업 (Done)

#### 🛠️ 환경 세팅 & Git 관리
- [x] GPU 서버 `git pull` Divergent branches 오류 해결 (`git reset --hard`)
- [x] GPU 서버에서 `ai/feat/recomendation` 브랜치 체크아웃 및 트래킹 설정
- [x] GPU 서버 venv 세팅 및 `requirements.txt` 패키지 설치 완료
- [x] `.gitignore` 개선: `docs/personal/` 제거, `stt/data/`, `stt/model/` 추가
- [x] `stt/data/.gitkeep`으로 폴더 구조 Git 유지 처리
- [x] 루트 폴더의 중복 `mock_payload.json` 삭제 및 `recommendation/` 내 데이터로 단일화

#### 🤖 AI 서버 고도화 (STT + Recommendation)
- [x] **Whisper 파인튜닝 완료 (CER 1.48%, 100% 정확도)**
  - `stt/stt_benchmark.py` 9/9 합격 및 `docs/shared/stt_benchmark_results.md` 공유
- [x] **추천 시스템 Phase 1: 컨텍스트 기반 동적 임계값 구현**
  - 시간대(취침/활동/귀가 등)별 유저 행동 분리 분석 → 상황 맞춤형 임계값 자동 추천
- [x] **추천 시스템 Phase 2: 머신러닝 예측 모델 도입**
  - `RandomForestClassifier`를 활용한 기기 작동 확률 예측 모델 (`ml_model.py`)
- [x] **GPU 가속 시계열 예측 모델 프로토타입 완료**
  - PyTorch 기반 **LSTM** 구조 설계 및 GPU(`cuda`) 학습 파이프라인 구축 (`gpu_lstm_model.py`)
- [x] **GPU 활용 전략 로드맵 수립** (`docs/recommendation_upgrade_plan.md`, `gpu_recommendation_strategy.md`)
  - 로컬 LLM 연동(Speaky 설명형 AI) 및 비전(YOLO) 융합 멀티모달 설계안 정립

---

## 📦 아카이브 — 2026-03-20
**[목표] STT 20GB 학습 환경 최적화 + LSTM 주기성 로직 고도화 + 개인 문서 역할 정립**

### ✅ 완료한 작업 (Done)

#### 🤖 STT & 파인튜닝 (20GB 준비)
- [x] **STT API (`stt/main.py`) 리팩토링 및 고도화**
  - HuggingFace Transformers 기반으로 전환, 파인튜닝 모델(`v2_full`) 자동 로드 로직 구현
- [x] **20GB 데이터셋 학습 설정 업데이트**
  - `MAX_STEPS` 상향(10,000), 모델 저장 경로 `v2_full` 분리 적용
- [x] **대용량 데이터 업로드 가이드 작성**
  - 로컬 환경 압축(zip) 및 GPU 서버 전송(`scp`) 프로세스 최적화 및 `walkthrough.md` 배포
- [x] **STT 방 이름 -> `roomId` 연동 구조 구현**
  - `stt/main.py` startup 시 백엔드 `GET /api/room/name` 호출 후 방 이름 맵 캐싱
  - `stt/stt_parser.py` 반환 형식을 `target_room`에서 `roomId` 중심으로 변경
  - 백엔드 API 실패 시 fallback 하드코딩 맵으로 대체되도록 예외 처리 적용
- [x] **백엔드 협업용 STT 연동 요청 문서 작성**
  - `docs/shared/stt_room_id_backend_request.md` 작성 및 팀 채팅 공유용 요약본 정리
- [x] **벤치마크 스크립트 `v2_full` 우선 검증 구조 반영**
  - `stt/stt_benchmark.py`가 `v2_full -> whisper-smarthome -> base` 순서로 모델을 선택하도록 수정

#### 📈 추천 시스템 (LSTM 고도화)
- [x] **LSTM 모델 시계열 데이터 생성 로직 보강**
  - `sin/cos` 주기적 인코딩 및 주말 여부 특징 추가 → 시간대별 행동 예측력 강화
  - 공기청정기/가습기/제습기 3개 기기 동시 예측(Multi-label) 구조 구현
- [x] **로컬 환경 학습 및 모델 검증 완료**
  - `recommendation/model/lstm_device_model.pth` 저장 및 데이터 참조 경로 자동화

#### 🏗️ 문서 및 역할 관리
- [x] **개인 포트폴리오(`portfolio.md`) 역할 재정의**
  - 백엔드 개발 삭제 → AI Engineer & ROS2 Vision Developer 집중
- [x] **전체 README.md 및 개발 일지(`dev_log.md`) 작업 내역 동기화**
- [x] **분리 커밋 및 원격 저장소(`ai/feat/recomendation`) 푸시 완료**

#### 🚀 GPU 서버 실행 및 모니터링
- [x] **20GB급 전처리 결과 확인**
  - `stt/data/processed/metadata.csv` 기준 총 128,468개 샘플 확인
- [x] **Tesla V100 5번 GPU 기준 장기 학습 프로세스 기동**
  - `CUDA_VISIBLE_DEVICES=5`로 백그라운드 학습 시작 및 로그 모니터링 환경 구성
- [x] **JupyterHub 세션 제약 검토**
  - 세션 누적 시간과 예상 학습 시간을 대조하여 24시간 내 완주 가능성 점검

### 🔴 내일 할 일 (Next) — 2026-03-21

#### 🤖 AI 서버 (모니터링 & 연동)
- [ ] **[필수] GPU 서버 20GB 파인튜닝 완료 여부 및 최종 로그 확인**
- [ ] **[필수] `v2_full` 기준 STT 벤치마크 재실행 및 성능 수치 정리**
- [ ] **[연동] 백엔드 팀 `GET /api/room/name` 응답 기준으로 STT roomId 변환 실제 연동 테스트**
- [ ] **[최적화] 단일 GPU(5번) 효율 향상 검토**
  - `eval/save` 주기 조정으로 wall-clock time 단축 가능 여부 확인
  - VRAM 사용량 기준 `batch size` 상향 가능 여부 점검
  - 데이터 로딩/검증 병목 여부 확인 후 loader 최적화 후보 정리
- [ ] **[최적화] STT 실서버 추론 성능 개선 방안 조사**
  - 실제 `stt/main.py` 운영 시 응답시간 병목 구간 분석
  - 모델 로딩 방식, 오디오 전처리, 동시 요청 처리 방식 개선 후보 정리
  - 필요 시 경량 모델/배치 추론/ONNX·TensorRT 전환 가능성 검토
- [ ] **[자동화] LSTM 리트레이닝 Cron Job GPU 서버 등록 및 테스트**
- [ ] **[문서] 학습 결과 확정 후 `dev_log.md`, `portfolio.md`, `ai_roadmap.md` 최종 업데이트**

---

## 📦 아카이브 — 2026-03-16
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

#### 🤖 AI 서버 (진행 중인 핵심 마일스톤)
- [x] **[작업 완료]** 추천(Recommendation) 시스템 생활 패턴 기반 알고리즘 고도화
- [x] **[작업 완료]** STT 모델 고유명사 프롬프트 튜닝 및 명령어 파서 예외 처리 고도화
- [ ] **[작업 예정]** 프론트엔드/메인서버(Spring Boot) 연동 라우팅 뚫기 및 REST 통신 테스트
- [x] `recommendation/` mock 데이터 컬럼명과 실제 API 계약(`air_purifier_on`) 일치시키기
- [x] `test_client.py`를 현재 `POST /api/event/ai-suggestions` 계약에 맞게 수정
- [x] GPU 서버에서 `git_sparse_guide.md` 기준으로 `server_ai/` 부분 복제 및 실행 검증
- [x] **[작업 완료]** 로컬 머신에서 수정한 STT 공백 예외 처리("내 방" vs "내방") 및 문서 업데이트를 Git에 커밋 및 푸시
- [x] **[작업 완료]** 추천 시스템 고도화: `ml_model.py`의 Isolation Forest (이상 탐지 머신러닝) 모델을 `main.py` API에 통합하여 '위기 감지형 알림(예: 급격한 미세먼지 증가)' 추천 로직 추가

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
