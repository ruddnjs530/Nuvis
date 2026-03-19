# 📝 개발 일지 (Development Log)

> **담당:** AI 서버 (`server_ai`) 중심 작업 기록, 백엔드 연동 이슈 포함  
> 형식: 날짜별로 작업 내용, 이슈 & 해결, 다음 작업 예정을 기록합니다.

---

## 📅 2026-03-19

### ⚙️ GPU 서버 개발환경 정비 & Git 관리 고도화

**작업 내용:**
- GPU 서버 브랜치를 `master`에서 `ai/feat/recomendation`으로 전환하여 작업 브랜치 일원화.
- `.gitignore` 개선: `docs/personal/` 추적 해제, `stt/data/*`, `stt/model/` 추가 → 데이터/모델 파일 Git 제외 처리.
- `stt/data/.gitkeep`으로 빈 폴더 구조 Git 유지 패턴 정착.

### 🤖 Whisper 파인튜닝 전체 파이프라인 구축 및 완료

**작업 내용:**
- **데이터 확보:** AI Hub 카투홈(Car2Home) 데이터셋 1GB(약 3,978샘플) 확보, GPU 서버 `stt/data/`에 업로드.
- **전처리 스크립트 작성 (`stt/preprocess_data.py`):**
  - 48kHz WAV → 16kHz 변환 (Whisper 요구사항)
  - AI Hub JSON 라벨파일에서 `전사정보.LabelText` 추출
  - `QualityStatus: Good` 필터링 후 `metadata.csv` 생성
- **파인튜닝 스크립트 작성 (`stt/finetune_whisper.py`):**
  - `datasets.map()` 멀티프로세싱 데드락 이슈 → PyTorch 커스텀 Dataset으로 완전 우회 해결
  - CUDA multi-GPU peer mapping 오류 → `CUDA_VISIBLE_DEVICES=5` 단일 GPU 지정 해결
  - `transformers 5.x` API 변경(`tokenizer` → `processing_class`) 대응
- **파인튜닝 결과 (Tesla V100-PCIE-32GB, ~9분 20초):**
  - `eval_cer: 1.48%` — CER 5% 이하 우수 기준 대비 압도적 달성
  - `eval_loss: 0.0743`
- **벤치마크 결과:**
  - `stt/stt_benchmark.py` 실행 → **9/9 (100%) 정확도** 달성
  - 부정어(`켜지마`), 복합 명령(`거실 말고 안방`), 공백 변이(`내방`↔`내 방`) 모두 완벽 처리
  - STT 오인식(`보일락`)도 파서가 복원하는 강인성 확인
- **결과 문서화:** `docs/shared/stt_benchmark_results.md` 공식 작성

**다음 작업 예정:**
- GPU 서버 파인튜닝 모델 백업 (HuggingFace Hub 또는 구글 드라이브)
- `stt/main.py`에 파인튜닝 모델 경로 연동
- GPU 서버 API 서버 실행 및 백엔드 팀 엔드포인트 공유

---

## 📅 2026-03-17

### 🧠 추천 시스템 고도화 및 라이프스타일 분석 적용

**작업 내용:**
- 스케줄 추천 알고리즘을 단순 시간 빈도 기반에서 **라이프스타일 클러스터링(평일/주말, 수면/기상/일과/저녁)** 기반으로 개선함.
- `generate_mock_data.py`를 업데이트하여 백엔드 API 계약에 맞는 JSON 페이로드를 생성하고, 세 가지 라이프스타일 패턴(퇴근 후 공기청정기, 수면 중 가습기, 주말 대청소 제습기)을 시뮬레이션하도록 구현함.
- `test_client.py`에서 JSON 페이로드를 읽어와 STT와 이벤트/스케줄 추천 엔드포인트 모두를 테스트하도록 통신 모듈을 강화함.
- 반환된 NumPy 타입을 `int`, `float`, `str` 등 순수 파이썬 타입으로 명시적 변환(Casting)하여 FastAPI JSON 직렬화 오류를 해결함.

**다음 작업 예정:**
- 실제 메인 백엔드(Spring)와 통신 포트 및 라우팅 연결 점검

### 🎙️ STT 자연어 파싱 고도화 및 인식률 극대화

**작업 내용:**
- `stt_parser.py`를 개선하여 부정어("말고", "아니고", "켜지마" 등)를 정규식(Regex)으로 필터링하고 정확한 대상 기기와 방 이름만 타겟팅하도록 고도화함.
- `stt_parser.py` 단어 매핑 시 STT 엔진의 띄어쓰기 변수("내 방" vs "내방")를 해결하기 위해, 원본 문장과 공백을 제거한 문장 모두에서 키워드를 매칭하는 예외 처리 로직을 추가함.
- STT 파이프라인에서 Whisper 모델 엔진 추론 시 `initial_prompt` 기능을 활용하여 로봇 제어 도메인 특화 단어(`공기청정기`, `가습기`, `켜지마` 등) 강제 주입으로 고유명사 인식률 상승 적용함.
- `stt_benchmark.py` 스크립트를 통해 부정어/복합 명령 테스트 케이스를 벤치마크 셋에 추가 등록.

**다음 작업 예정:**
- GPU 환경에서 ffmpeg 연동 후 테스트 재수행 및 STT 파서의 다중 인텐트 처리 확대 (추후)

---

## 📅 2026-03-16

### 🧭 모노레포 구조 정리

**작업 내용:**

- AI 파트 내부 기능을 역할 기준으로 다시 구분함.
  - `server_ai`: 추천 AI + STT 전용 서비스
  - `YOLO`: ROS2 카메라 토픽 기반 비전 노드로 분류
- 백엔드/인프라 담당자와 공유할 구조 기준을 문서 기준으로 정리함.
- 현재 저장소에는 `server_ai/vision/` 프로토타입이 남아 있지만, **최종 모노레포 배치 기준에서는 `ros2_ws` 측 비전 패키지로 재배치 예정**이라는 원칙을 확정함.
- 루트 README, AI README, 개인 문서, 배포 가이드에 위 구조 결정을 반영함.

**이슈 & 해결:**
- *이슈*: AI가 `scheduler` 내부 기능인지, 별도 서비스인지, YOLO까지 같은 범주로 묶어야 하는지 팀 내 해석 여지가 있었음.
- *해결*: 추천 AI/STT는 백엔드가 호출하는 독립 `server_ai` 서비스로 두고, YOLO는 언어와 무관하게 ROS2 런타임에 더 가까운 비전 노드로 정리하여 문서 기준을 통일함.

**다음 작업 예정:**
- 실제 모노레포 루트(`S14P21B110`)에 `server_ai` 디렉토리 생성 후 `recommendation`, `stt` 이관
- YOLO의 `ros2_ws` 재배치 시점은 추후 통합 규격 확정 후 별도 진행

### 🚀 배포 전략 및 협업 문서 정리

**작업 내용:**

- GPU 서버에 `server_ai/`만 부분 복제하는 `git sparse-checkout` 방식이 실제 운영 구조와 충돌하지 않는지 재검토함.
- "일반 서버는 Docker / GPU 서버는 AI 단독 실행" 구조가 가능한지 질문 흐름을 정리하고, 분리 배포가 현재 아키텍처와 가장 잘 맞는다는 결론을 문서 기준으로 명문화함.
- 특히 Jenkins를 사용할 경우에도 배포 대상 서버가 둘로 나뉠 수 있으며,
  - 일반 서버: 프론트 / 백엔드 / DB Docker 배포
  - GPU 서버: `server_ai` 최신화 후 AI 서버 재시작
  방식으로 충분히 자동화 가능하다는 기준을 정리함.
- 백엔드 / 인프라 담당자에게 바로 전달할 수 있도록
  `docs/shared/deployment_strategy_for_backend_and_infra.md` 문서를 신규 작성함.

**이슈 & 해결:**
- *이슈*: "모노레포 + Docker + GPU 서버 + Jenkins"를 같이 쓰면 AI까지 하나의 통합 Compose에 넣어야 하는지, 아니면 AI를 별도 서버에서 돌려도 배포로 볼 수 있는지 해석이 혼재됨.
- *해결*: Docker는 패키징/실행 방식이고, 배포는 대상 서버 구조와 별개라는 기준으로 정리함. 따라서 일반 서버는 Docker/Jenkins, GPU 서버는 `server_ai` 단독 운영(또는 GPU Docker)으로 분리하고, 백엔드는 HTTP로 AI 서버를 호출하는 구조를 공식화함.

**다음 작업 예정:**
- 백엔드 / 인프라 담당자에게 `backend_integration_proposal.md`와 신규 배포 전략 문서 전달
- GPU 서버에서 `git_sparse_guide.md` 기준으로 `server_ai` 부분 복제 및 실제 실행 검증
- `recommendation` mock 데이터 / 테스트 클라이언트와 현재 API 계약 간 불일치 정리

---

## 📅 2026-03-13

### 🤖 AI 서버

**작업 내용:**

#### 🛡️ AI 서버 안전장치(Safety Guard) 적용 — `recommendation/main.py` 개선

기존 아키텍처(Stateless Data Passing) 방식의 잠재적 취약점 2가지를 파악하고, 코드 레벨에서 직접 보완함.

- **페이로드 상한선 적용 (`MAX_RECORDS = 500`):**
  - 메인 서버가 수천 건의 이력 데이터를 한 번에 전송할 경우 AI 서버 메모리 및 처리 속도 저하 가능성 확인.
  - `sensor_data[-MAX_RECORDS:]` 슬라이싱으로 최신 500건만 분석에 사용하도록 처리. 500건 초과 수신 시 서버 로그에 Warning 기록.
  - 어차피 최신 데이터가 패턴 분석에 더 유효하므로 분석 품질에 영향 없음.

- **기기별 분석 타임아웃 및 격리된 예외 처리 (`ANALYSIS_TIMEOUT = 5.0초`):**
  - 기존 코드는 기기 1개 분석 중 오류 발생 시 전체 API 요청이 실패하는 구조.
  - `asyncio.wait_for` + `asyncio.to_thread` 조합으로 기기별 독립적인 타임아웃 적용.
  - 공기청정기 분석이 타임아웃 나도 가습기·제습기 결과는 정상 반환 → 장애 전파 차단.
  - 타임아웃 및 오류 발생 시 사용자에게 명확한 `fallback` 메시지 반환.

- **로깅 체계 추가:**
  - `import logging` 적용, 요청/오류/경고 레벨별 서버 로그 기록 시작.

**이슈 & 해결:**
- *이슈*: Stateless Data Passing 방식은 대량 이력 전달 시 페이로드 크기 문제와 AI 서버 장애가 메인 서버로 전파되는 문제가 잠재되어 있었음.
- *해결*: 상한선(MAX_RECORDS)과 타임아웃(ANALYSIS_TIMEOUT) 두 상수를 파일 최상단에 분리 선언하여, 운영 중 튜닝이 필요할 때 코드 한 줄만 수정해도 되는 구조로 개선.

### 🔵 백엔드 서버

**작업 내용:**
- `server_backend/` 폴더 구조 초기 세팅
- 공용 docs/ 폴더 구성 확인 (ERD, MVP, API 명세서, 시스템 아키텍처)
- AI 팀 연동 제안서(`backend_integration_proposal.md`) 검토 시작
- `docs/personal/` 통합 — AI 서버 + 백엔드 서버 1인 담당으로 개인 문서 일원화

**다음 작업 예정:**
- 백엔드팀 `ROOM_CONDITIONS_HISTORY` / `MODULE_CONTROL_LOGS` 테이블 추가 반영
- GPU 서버에서 `git_sparse_guide.md` 가이드대로 `server_ai/` 폴더 클론 작동 여부 직접 검증
- 스케줄 추천 기능 (`analyze_schedule_patterns`) 실제 코드 구현

---

## 📅 2026-03-12

### 🤖 AI 서버

**작업 내용:**

#### 🤝 AI ↔ 백엔드 연동 아키텍처 설계 및 제안서 작성
- **연동 방식 확정:** AI 서버는 DB 직접 접근 없이, 메인 서버가 데이터를 전달하는 **Stateless API (Data Passing)** 방식으로 최종 결정.
- **MVP 추천 흐름 설계:** 메인 서버 → AI 서버 `POST /api/v1/event/ai-suggestions` → 분석 결과 반환 → 사용자 수락/거절(Human-in-the-loop) 전체 파이프라인 구체화.
- **ERD 검토 및 수정 요청 정리:** `ROOM_CONDITIONS` 테이블이 현재값 1건만 보관하는 덮어쓰기 구조임을 파악. AI 패턴 분석에 필요한 시계열 이력 테이블 2개 (`ROOM_CONDITIONS_HISTORY`, `MODULE_CONTROL_LOGS`) 추가를 공식 요청.
- **다중 기기 확장성 검증:** `MODULES.type`, `EVENTS.action_module_type` 등이 VARCHAR로 설계되어 공기청정기/가습기/제습기 등 모든 기기 타입에 동일한 AI 로직 재사용 가능함을 확인.
- **완전 자동화 시나리오 추가 제안:** MVP 안정화 후 2차 고도화용 '100% 자율 제어' 흐름 및 안전장치(Auto-Fallback, Conflict Resolution) 설계 가이드 문서화.
- **산출물:** `docs/shared/backend_integration_proposal.md` 기준 문서 작성 및 공유.

#### 🖥️ GPU 서버 모노레포 동기화 전략 수립
- **문제 파악:** GPU 서버(JupyterHub 웹 환경)는 외부 SSH/SFTP 포트 차단으로 이전 SFTP 동기화 방식 사용 불가.
- **해결책 결정:** `git sparse-checkout` 방식으로 모노레포 전체가 아닌 `server_ai/` 폴더만 GPU 서버에 클론하는 방식 채택.
- **가이드 문서 작성:** `docs/shared/git_sparse_guide.md` 신규 작성.

**이슈 & 해결:**
- *이슈*: 백엔드 ERD에 AI 분석에 필요한 시계열 이력 데이터가 누적되지 않는 구조.
- *해결*: 2개의 이력 테이블 추가를 제안하는 `backend_integration_proposal.md` 작성 후 공유.
- *이슈*: GPU 서버 웹 환경에서 포트 차단으로 SFTP 접근 불가.
- *해결*: Git HTTP 프로토콜 기반 `sparse-checkout` 방식으로 전환.

---

## 📅 2026-03-10

### 🤖 AI 서버

**작업 내용:**
- 프로젝트 MVP 및 API 명세서 분석 완료
- 주행 제어 파트와 겹치는 자율주행(SLAM, Nav2) 내용 롤백 후 순수 AI 아키텍처 재정립
- **Phase 1 (비전):** ROS2 카메라 토픽 기반 YOLO 객체 인식 프레임워크 베이스 노드 구현 (`server_ai/vision/yolo_node.py`)
- **Phase 2 (추천 AI):** 가상 IoT 데이터(CSV) 생성 스크립트 작성 및 Pandas 통계 기반 임계값 이상 탐지 추천 로직 `FastAPI` 서버 구현 완료 (`server_ai/recommendation/`)
- **Phase 3 (STT):** OpenAI Whisper 베이스 STT 변환 파이프라인 및 자연어-로봇 제어 명령어(JSON) 매핑 파서 구현 (`server_ai/stt/stt_parser.py`, `whisper_test.py`)
- Python 가상환경(`venv`) 구축 및 패키지 설치.

**이슈 & 해결:**
- *이슈*: 현재 시뮬레이터 환경 및 ROS2 통신 규격이 확정되지 않음.
- *해결*: ROS2 통신이 없어도 단독으로 실행되고 검증할 수 있도록 AI 핵심 로직(YOLO 추론, Pandas 통계 모델, Whisper STT)들을 모두 분리된 프로토타입 형태로 모듈화.

---

<!-- 아래에 날짜별로 계속 추가하세요 -->
