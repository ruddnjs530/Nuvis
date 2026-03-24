# STT 학습 운영 정리 가이드

> 작성 대상: AI 담당자, GPU 서버 운영자
> 목적: `v2_full` 학습 이후 어떤 산출물을 보존하고, GPU 서버에서 어떤 순서로 확인/정리할지 빠르게 공유하기 위한 문서

---

## 1. 현재 기준 결론

- 현재 시연 기준 STT 운영 조합은 `v2_full + parser 보정 + roomId 변환`입니다.
- 20GB 재학습 결과 기준 최종 모델은 `stt/api/model/v2_full/`입니다.
- 동일 조건 비교 벤치마크 결과는 `base 77.8% (7/9)`, `v2_full 100.0% (9/9)`입니다.
- GPU 서버 실서버 API 스모크 테스트 기준으로도 `/api/stt/transcribe` 응답이 정상 동작함을 확인했습니다.

---

## 2. 학습 결과 요약

### 2.1 20GB 재학습 결과

| 항목 | 값 |
|---|---|
| 전처리 메타데이터 | `128,468개 샘플` |
| 학습 데이터 | `115,621개` |
| 검증 데이터 | `12,847개` |
| 최종 검증 CER | `1.02%` |
| 최종 검증 Loss | `0.0146` |
| 최종 학습 Loss | `0.03998` |
| 총 학습 시간 | `약 16시간 39분` |
| 최종 모델 | `stt/model/v2_full/` |

### 2.2 운영 확정 기준

- 시연 기준 모델: `stt/api/model/v2_full/`
- 실서버 API 포트: `9001`
- 현재 room map source: 백엔드 미연동 상태에서는 `fallback`
- 추후 백엔드 `GET /api/room/name` 연동 후 `room_map_source=backend` 확인 예정

---

## 3. 보존 대상 산출물

### 3.1 반드시 보존할 항목

| 구분 | 경로 | 설명 |
|---|---|---|
| 최종 모델 | `stt/api/model/v2_full/` | 시연 기준 운영 모델 |
| 학습 로그 | `stt/api/stt_train.log` | 학습 완료 시점 기록, 장애 추적용 |
| 전처리 메타데이터 | `stt/data/processed/metadata.csv` | 어떤 데이터로 학습했는지 추적하는 기준 |
| 벤치마크 결과 | `docs/shared/stt/stt_benchmark_results.md` | `base` vs `v2_full` 비교 결과 |
| 운영 기록 | `docs/personal/dev_log.md` | 작업 흐름과 판단 근거 |

### 3.2 선택 보존 항목

| 구분 | 경로 | 설명 |
|---|---|---|
| 중간 체크포인트 | `stt/api/model/v2_full/checkpoint-*` | 재시작/재현 목적이면 유지, 용량 절약 시 제거 검토 |
| 테스트 오디오 | `stt/tests/test_audio/` | 벤치마크 및 API 스모크 테스트 재현용 |

---

## 4. GPU 서버 운영 체크리스트

### 4.1 학습 완료 직후

1. 학습 로그 끝부분 확인

```bash
# 서버 재배치 후 API 실행 확인
tail -n 50 stt/api/stt_train.log
ls stt/api/model/v2_full
python stt/tests/stt_benchmark.py --compare

# 실서버 API 기동 상태 확인
bash start_all_servers.sh
curl http://127.0.0.1:9001/api/stt/health
```

### 4.2 코드 브랜치 재정렬

GPU 서버는 같은 작업 브랜치를 계속 사용하므로, 학습/검증이 끝난 뒤에는 일반 `git pull`보다 아래 순서로 동기화하는 편이 안전합니다.

```bash
git status
git fetch origin
git checkout ai/feat/recomendation
git reset --hard origin/ai/feat/recomendation
```

주의:

- `git status`에서 추적 중인 수정 파일이 있으면 먼저 확인합니다.
- `.gitignore` 대상 산출물은 보통 그대로 남고, Git이 추적하는 코드 파일만 원격 기준으로 맞춰집니다.

---

## 5. 백업 전략 메모

현재 상태:

- 최종 모델은 GPU 서버 `stt/model/v2_full/`에 보관 중
- 외부 백업(HuggingFace Hub, 별도 드라이브)은 아직 미완료
- GPU 서버에서 백업 묶음을 만들기 위한 스크립트 `stt/package_stt_artifacts.sh` 추가
- 최신 브랜치 기준 재검증 후 로컬 백업 패키지 `stt/artifacts/stt_backup_20260323_111736.tar.gz` 생성 완료

권장 순서:

1. GPU 서버 최종 모델 디렉터리 무결성 확인
2. 외부 백업 대상 선정
   - `v2_full/`
   - `stt_train.log`
   - `docs/shared/stt_benchmark_results.md`
3. 백업 위치 확정
   - HuggingFace Hub 비공개 저장소
   - 팀 공유 드라이브
   - 별도 내부 보관 경로 중 택 1

### 5.1 로컬 백업 패키지 생성

GPU 서버에서 아래 명령으로 백업용 tarball을 생성할 수 있습니다.

```bash
bash stt/package_stt_artifacts.sh
```

기본 출력 위치:

- `stt/artifacts/stt_backup_<timestamp>.tar.gz`

포함 항목:

- `stt/model/v2_full/`
- `stt/data/processed/metadata.csv`
- `stt_train.log` (존재 시)
- `docs/shared/stt_benchmark_results.md`
- `docs/shared/stt_training_operations_guide.md`
- `manifest.txt` (브랜치/커밋 정보 포함)

### 5.2 2026-03-23 최신 생성 예시

- 생성 파일: `stt/artifacts/stt_backup_20260323_111736.tar.gz`
- 생성 전 확인:
  - `curl http://127.0.0.1:9001/api/stt/health`
  - `python test_client.py`
- 생성 후 확인:

```bash
ls stt/artifacts
```

현재 미결정 항목:

- 외부 백업 위치 최종 확정
- checkpoint 디렉터리 유지 여부

---

## 6. 다음 우선순위

1. 백엔드 `GET /api/room/name` 실제 응답 기준 연동 테스트
2. `v2_full` 외부 백업 위치 확정
3. 단일 GPU 학습 효율 최적화 실험
4. STT 실서버 2차 추론 최적화는 후순위로 검토
