# 스마트 홈 로봇 AI 파트 전체 로드맵

이 문서는 프로젝트가 끝날 때까지 AI 담당자가 밟아나갈 전체 개발 여정(Roadmap)입니다.

## 📐 운영 구조 메모
- `server_ai`: 추천 AI + STT 전용 서비스로 운영
- 배포 기준은 **일반 서버(Docker / Jenkins)** 와 **GPU 서버(`server_ai` 단독 운영)** 로 분리하는 방향을 우선 채택

## 🏁 Phase 0: 프로젝트 기획 및 환경 세팅 (현재 완료)
- [x] 요구사항(MVP/API) 분석 및 AI 역할 정의
- [x] 각 기능별(데이터분석, STT) 아키텍처 및 기술 스택 확정
- [x] 모듈별 단독 테스트가 가능한 마이크로 뼈대 코드(Prototype) 작성 및 가상환경 세팅

---



## 🧠 Phase 2: IoT 데이터 기반 추천 AI 시스템 구현 (핵심 MVP)
*목표: 수집된 센서 데이터를 바탕으로 스마트 홈 자동화 규칙 추천하기*
*배치 원칙: `server_ai` 독립 서비스에서 백엔드 호출 기반으로 운영*
- [x] 메인 서버 DB와 AI 전용 서버(`FastAPI`) 간 데이터 통신망(Stateless API) 요구사항/규격 구축 완료
- [x] 백엔드 환경변수 / HTTP 클라이언트 기준으로 GPU 서버 AI 주소 연동(`backend_integration_proposal.md`) 방안 수립 완료
- [x] 통계/Rule/패턴 기반 모델로 1차 추천 (`api/event/ai-suggestions`, `api/schedule`) 시스템 납품 및 0.2초 내 응답 E2E 점검 완료
- [x] *(고도화)* Scikit-learn / LSTM(딥러닝) 활용 다중 머신러닝 이상 탐지 및 시계열 스케줄 예측 백그라운드 자동화(MLOps) 구축 완료
- [ ] 로봇 대시보드(FrontEnd) 화면에 AI 추천 결과가 최종적으로 올바르게 렌더링되는지 연동 확인 모니터링

---

## 🎙️ Phase 3: 자연어 음성 제어 인터페이스 (확장 기능)
*목표: "거실로 와서 공기청정기 틀어" 라는 사람의 말을 로봇이 이해하도록 만들기*
*배치 원칙: `server_ai` 독립 서비스에서 STT / 파서 API로 운영*
- [x] OpenAI `Whisper` 모델 작동 및 정확도 테스트 (완료)
- [x] 전송 측(웹/클라이언트)의 오디오 입력을 AI 파서 엔진까지 전달하고 JSON 로직으로 가공 반환하는 Multipart E2E 테스트 통과 (`test_client.py`)
- [x] `stt_parser.py` 고도화 (부정어/복합 명령/공백 변이 예외 처리 완료)
- [x] **[완료]** AI Hub 카투홈 데이터 1GB 기반 Whisper-small 파인튜닝 완료
  - `eval_cer 1.48%`, 벤치마크 정확도 **9/9 (100%)** 달성 (2026-03-19)
  - `stt/preprocess_data.py`, `stt/finetune_whisper.py` 스크립트 완성
  - 결과: `docs/shared/stt_benchmark_results.md` 문서화
- [x] **[완료]** `stt/main.py`에서 파인튜닝 모델(`v2_full`) 자동 로드 지원
- [x] **[완료]** STT 응답을 백엔드 계약에 맞춰 `roomId` 기반으로 변환하는 구조 구현
  - startup 시 `GET /api/room/name` 호출 → 방 이름 맵 캐싱
  - 백엔드 미연동 시 시연용 fallback 맵 유지
- [x] **[완료]** GPU 서버에서 실제 `/api/stt/transcribe` 응답 검증
  - `test_client.py` 기준 샘플 음성 업로드 결과 `roomId=1`, `module=air_purifier`, `state=on` 확인
- [x] **[완료]** STT 운영 점검용 헬스체크 추가
  - `GET /api/stt/health`에서 `device`, `model_path`, `room_map_source` 확인 가능
- [x] **[완료]** FastAPI `startup` -> `lifespan` 전환 및 임시 파일 처리 안정화
- [x] **[완료]** 20GB급 full raw 재학습 및 `v2_full` 검증 완료
  - GPU 서버 `metadata.csv` 기준 **128,468개 샘플** 학습 완료
  - 최종 학습 결과: `eval_cer 1.02%`, `eval_loss 0.0146`
  - 동일 조건 비교 벤치마크 결과: `base 77.8% (7/9)` vs `v2_full 100.0% (9/9)`
  - `stt_benchmark.py --compare` 기준으로 시연 모델을 `v2_full`로 확정
- [x] **[완료]** LSTM 추천 모델 1일 주기 Background 자동 재학습 파이프라인 구축 완료 (Cron/PM2 차단 환경 돌파)
- [x] **[완료]** GPU 다중 서버(추천 API, STT API, 자동학습 데몬) 원클릭 통합 구동 런북(`start_all_servers.sh`) 구축
- [x] **[완료]** 파인튜닝 모델 백업 및 최종 모델 보존 전략 실행 완료 (개인 드라이브 공유 및 tarball 로컬 백업 파이프라인 구성)
- [x] **[완료]** 백엔드 `GET /api/room/name` 응답 부재 시 방어하는 Fallback 맵핑 로직 작동 E2E 검증 ("거실" -> `roomId=1`)
- [ ] 치환된 JSON 명령어가 실제 주행 파트나 기기 제어 로직으로 흘러가 실물 로봇이 동작하는지 H/W 통합 테스트

---

## 🏆 Phase 4: 최종 최적화 및 문서화 (현재 완료)
- [x] **[완료]** 로봇 탑재 컴퓨터 리소스(CPU/GPU) 환경에 맞춘 모델 경량화(TensorRT, ONNX Export 등) 검토
- [x] Jenkins 기준 일반 서버(CI/CD) / GPU 서버 분리 배포 파이프라인 아키텍처 수립 완료
- [x] **[완료]** 최종 프로젝트 구조 리팩토링 및 도메인 기반 계층화 (`api/`, `scripts/`, `data/`, `tests/`)
- [x] **[완료]** 포트폴리오 산출물 병합 및 최종 발표 준비
- [x] 공유 문서(`docs/shared/`) 카테고리별 재분류 및 API 쓰레기 파일 정리 완료
