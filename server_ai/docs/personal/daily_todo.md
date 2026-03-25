# 📝 오늘의 할 일 (Daily To-Do List)

> **담당:** AI 서버 (`server_ai`) 개발 및 백엔드 연동 협업 기록  
> **기준일:** 2026-03-23  
> 이 문서는 "지금 당장 남은 일"과 "최근 완료한 흐름"을 빠르게 확인하기 위한 작업 보드입니다.

---

## 🎯 현재 우선순위

### 1. 학습 운영 정리
- [x] 20GB 학습 산출물 1차 운영 문서화
  - `docs/shared/stt_training_operations_guide.md`에 보존 대상 파일, GPU 서버 후속 절차, 브랜치 재정렬 순서 정리
  - `v2_full`, `stt_train.log`, `metadata.csv`, 벤치마크 문서를 핵심 산출물로 정리
- [x] GPU 서버 백업 패키징 스크립트 추가
  - `stt/package_stt_artifacts.sh`로 모델/로그/메타데이터/문서를 tarball로 묶을 수 있게 정리
- [x] GPU 서버 최신 브랜치 기준 서비스 재검증 및 로컬 백업 패키지 재생성
  - `curl /api/stt/health`, `python test_client.py` 재실행으로 최신 브랜치 반영 후 정상 동작 확인
  - `stt/artifacts/stt_backup_20260323_111736.tar.gz` 생성 완료
- [x] 파인튜닝 모델 외부 백업 전략 확정
  - 개인 구글 드라이브 업로드 및 팀원 공유 완료
  - `v2_full` 최종 보존 위치 확정 (개인 구글 드라이브)
- [ ] 단일 GPU(5번) 학습 효율 최적화 실험 (후순위 보류)
  - `eval/save` 주기 조정
  - `batch size` 상향 가능 여부 점검
  - 데이터 로딩/검증 병목 분석

### 2. 백엔드 실제 연동
- [x] 백엔드 MR(`be/ai-connect` -> `be-main`) 구현 범위 코드 1차 확인 완료
- [x] 백엔드 API 미연동 시 `stt/main.py`의 Fallback 매핑 방어 로직 작동 검증 완료 (Crash 방지)
- [x] 서버 9000/9001 분리 후 `test_client.py` 활용 E2E(End-To-End) 클라이언트 통신 응답 테스트 완수
- [x] 추후 백엔드 `GET /api/room/name` 본코드(`master`) 병합 시 라이브 데이터 연결 최종 모니터링 (연동 전구조/Fallback 점검 완수)

### 3. STT 운영 안정화
- [x] FastAPI `startup` -> `lifespan` 전환
- [x] 업로드 오디오를 메모리에서 우선 디코딩하고, 필요 시에만 임시 파일로 fallback 하도록 최적화
- [x] 실제 `/api/stt/transcribe` 응답 확인
  - `roomId=1`, `module=air_purifier`, `state=on`
- [x] `GET /api/stt/health` 추가 및 GPU 서버 응답 확인
  - `device=cuda`
  - `model_path=v2_full`
  - `room_map_source=fallback`
- [x] STT 실서버 추론 1차 병목 분석 정리
  - 현재 병목은 모델 로드보다 `파일 저장 -> librosa.load -> feature extraction` 구간에 가까운 것으로 판단
- [x] STT 실서버 추론 1차 최적화 적용
  - 업로드 오디오를 메모리에서 먼저 디코딩해 디스크 I/O를 줄이고, 미지원 포맷만 임시 파일 fallback 처리
- [ ] STT 실서버 추론 2차 최적화 검토 (후순위)
  - 오디오 전처리 경량화
  - 동시 요청 처리 정책 정리
- [x] 남아 있는 generation warning(`SuppressTokens...`) 정리 필요 여부 확인
  - 현재는 Whisper generation config 기반 중복 suppress processor 경고로 보고, 정확도 영향이 없어 보류
  - decoding 정책 변경으로 경고를 없애는 것은 정확도 리스크가 있어 당장 적용하지 않음
- [x] 헬스체크 응답을 운영 문서/배포 스크립트에 연결할지 검토
  - `README.md`, `deployment_strategy_for_backend_and_infra.md`에 `curl /api/stt/health` 점검 흐름 반영

### 4. 추천 시스템 후속
- [x] LSTM 리트레이닝 Cron Job GPU 서버 등록 및 테스트 (컨테이너 제약으로 Daemon 봇 형태 스크립트로 구축 완료)

---

## ✅ 최근 완료

### 2026-03-25 (오늘)
- [x] **[Feature]** 프로젝트 전반 보안 미들웨어 동적 설계 및 적용 완료
  - FastAPI 계층에 `BaseHTTPMiddleware` 주입하여 백엔드 수정 없는 마이크로서비스 무중단 자체 방어 구축
  - `ALLOWED_BACKEND_IPS` 환경변수 연동을 통한 인가 IP Whitelisting (12-Factor App)
  - 악의적인 파일 용량 공격(10MB) 차단으로 서버 메모리 폭발(OOM) 완벽 보호
  - Rate Limiting 300/min 차단으로 DDoS 방어 로직 완수
- [x] **[Documentation]** AI 서버 컴포넌트 전체 소스코드 리팩토링 및 교육용 주석 전면 삽입 완료
  - STT, Recommendation 메인 서버, 쉘 배포 스크립트, 통합 테스트 코드의 작동 원리를 전부 라인단위로 문서화
- [x] `.env.example` 동기화 및 각종 개인 포트폴리오/로드맵/DevLog 기록 완료

### 2026-03-24
- [x] **[Refactor]** GPU 서버 프로젝트 구조 전면 계층화 및 도메인 기반 폴더링
  - `api/`, `scripts/`, `data/`, `tests/` 폴더 기반 역할 분리
  - `start_all_servers.sh` 및 모든 파이썬 스크립트 상대 경로 전수 보정 및 검증
  - 공유 문서(`docs/shared/`) 인프라/디자인/STT/연동 카테고리별 재분류 및 API 쓰레기 파일 정리
- [x] LSTM 모델 백그라운드 리트레이닝 자동화 구축 완료
- [x] 컨테이너 제약 극복용 통합 런북(`start_all_servers.sh`) 실전 가동 및 E2E 테스트 성공
- [x] 비전 AI(YOLO) 관련 코드 및 문서 흔적 완전 제거 (Focus On core AI)
- [x] LSTM 모델 백그라운드 리트레이닝 자동화 구축
  - 컨테이너 환경의 `crontab` 사용 불가 제약을 우회하기 위해 `daemon_retrain_lstm.sh` 무한 루프 봇 작성
  - 24시간마다 주기적으로 모델을 재학습하고 이전 로그를 30일 주기로 정리하도록 구현
- [x] AI 서버 런북(`startup_guide.md`) 작성
  - 추천 API 로딩 가이드(`recommendation/startup_guide.md`, 포트 9000)
  - STT API 로딩 가이드(`stt/startup_guide.md`, 포트 9001)
  - README.md 포트 번호 오기재 정정 및 통합 운영 스크립트 작성
- [x] 컨테이너 제약 극복용 `start_all_servers.sh` 쉘 스크립트 기반 PM2 패스(Bypass) 런북 완성
- [x] AI 서버 GPU 100% 실증 E2E 테스트(단일 스크립트 가동 후 `test_client.py`) 완수
  - 추천 서버 9000 응답 0.2초 달성 및 STT 파서 보정 로직("공기청소기" -> `air_purifier`) 테스트 검증
  - 방 이름 미존재 백엔드 에러 시 Fallback 방어 로직 점검 완료

### 2026-03-23
- [x] 20GB `v2_full` 학습 완료 로그 확인
  - `eval_cer: 1.02%`
  - `eval_loss: 0.0146`
  - `train_loss: 0.03998`
  - 총 학습 시간 약 16시간 39분
- [x] `base` vs `v2_full` 동일 조건 비교 벤치마크 실행
  - `base`: `77.8% (7/9)`
  - `v2_full`: `100.0% (9/9)`
- [x] 시연 기준 모델을 `v2_full`로 확정
- [x] STT parser alias 보정 추가
  - `공기청소기`, `공기 천장기`, `공기 천천히` -> `공기청정기`
  - `가스 불`, `가스 기` -> `가습기`
- [x] `켜지 마` 형태 부정 표현 처리 강화
- [x] `stt_benchmark.py --compare` 비교 옵션 추가
- [x] GPU 서버에서 실제 `/api/stt/transcribe` 응답 확인
  - `roomId=1`, `module=air_purifier`, `state=on`
- [x] `test_client.py`가 실제 샘플 음성을 우선 사용하도록 정리
- [x] FastAPI `startup` -> `lifespan` 전환
- [x] `NamedTemporaryFile` 기반 업로드 처리로 임시 파일 충돌 위험 완화
- [x] `GET /api/stt/health` 추가 및 GPU 서버 응답 확인
  - `device=cuda`
  - `model_path=v2_full`
  - `room_map_source=fallback`
- [x] 공유 문서 및 개인 문서 최신 결과 반영
- [x] GPU 서버 브랜치를 최신 `ai/feat/recomendation` 기준으로 재동기화
- [x] 최신 브랜치 기준 헬스체크 / API 스모크 테스트 재확인
- [x] 최신 기준 백업 패키지 재생성
  - `stt_backup_20260323_111736.tar.gz`
- [x] 백엔드 MR(`be/ai-connect` -> `be-main`) 구현 범위 확인
  - `origin/be-main`에는 `GET /api/room/name` 및 추천 호출 로직이 들어간 흔적 확인
  - `origin/master`에는 아직 미반영이라 실제 공통 기준 브랜치는 아님

### 2026-03-20
- [x] `stt/main.py` 리팩토링 및 `v2_full` 자동 로드 구조 반영
- [x] 20GB 학습 설정 적용
  - `MAX_STEPS=10000`
  - 저장 경로 `stt/model/v2_full`
- [x] STT 방 이름 -> `roomId` 변환 구조 구현
- [x] 백엔드 협업용 `stt_room_id_backend_request.md` 작성
- [x] GPU 서버 학습 기동 및 모니터링 체계 구성

### 2026-03-19
- [x] 1GB Whisper 파인튜닝 완료
  - `eval_cer: 1.48%`
  - 벤치마크 `9/9`
- [x] `preprocess_data.py`, `finetune_whisper.py`, `stt_benchmark.py` 파이프라인 구축
- [x] 추천 시스템 RandomForest / LSTM 프로토타입 고도화

---

## 📦 아카이브 요약

### 2026-03-16
- `server_ai`를 추천 AI + STT 전용 서비스로 정리
- YOLO는 최종적으로 `ros2_ws` 비전 패키지로 분리하는 방향 확정
- 일반 서버(Docker/Jenkins)와 GPU 서버(`server_ai`) 분리 배포 전략 문서화

### 2026-03-13
- 추천 API 안전장치 적용
  - `MAX_RECORDS`
  - 기기별 timeout
  - fallback/logging
- 공용 문서 구조 정리 및 backend integration proposal 정비

### 2026-03-12
- AI ↔ 백엔드 `Stateless API / Data Passing` 연동 방향 확정
- `backend_integration_proposal.md`, `git_sparse_guide.md` 작성

### 2026-03-10
- AI 프로토타입 뼈대 구축
  - 추천 FastAPI
  - STT parser / whisper test
  - YOLO node 초안

---

## 메모

- 현재 STT 시연 기준 조합은 `v2_full + parser 보정 + roomId 변환`
- 실서버 API와 벤치마크 기준 모두 정상 확인 완료
- 학습 운영 기준 문서는 `docs/shared/stt_training_operations_guide.md`를 기준으로 관리
- 다음 핵심 병목은 "백엔드 실제 연동"과 "모델 외부 백업" 쪽
- 백엔드 MR 구현은 `be-main`에서 확인했지만, `master` 기준 재확인 전까지는 연동 완료로 판단하지 않음
