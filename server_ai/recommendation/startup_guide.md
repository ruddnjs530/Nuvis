# 추천 시스템 (GPU 서버) 재부팅/시작 시 가이드

GPU 서버나 도커 컨테이너, 주피터 환경 등이 예기치 않게 종료된 후 다시 켜졌을 때, 추천 AI 모델과 관련된 프로세스가 정상적으로 24시간 동작하기 위해 **수동으로 가동해주어야 하는 항목들을 정리한 문서**입니다.

---

## 1. LSTM 주기적 자동 재학습(Retraining) 봇 가동

크론(Cron) 등의 시스템 스케줄러 권한이 막혀 있는 환경에 대응하기 위해, 무한 루프로 24시간마다 대기 및 재실행을 반복하는 백그라운드 봇 스크립트를 사용합니다. 서버가 꺼졌다 켜지면 무조건 이 명령어를 한 번 치고 나가야 합니다.

### 🚀 실행 방법 (통합 스크립트 권장)

가장 간단하고 권장되는 방법은 최상위 폴더에 있는 **`start_all_servers.sh`** 통합 스크립트를 한 번 실행하는 것입니다. 
(이 스크립트는 PM2 설치 없이 추천 API, STT API, 자동학습 데몬 봇을 한 번에 구동해줍니다.)

```bash
cd /home/j-j14b110/smart_home_ai/server_ai
bash start_all_servers.sh
```

---

### ✅ 개별 가동 및 로그 확인 (수동 조작 시)

만약 봇 스크립트만 단독으로 실행해야 한다면 기존 `nohup`을 활용합니다.

```bash
nohup bash /home/j-j14b110/smart_home_ai/server_ai/recommendation/scripts/daemon_retrain_lstm.sh > /home/j-j14b110/smart_home_ai/server_ai/recommendation/daemon_retrain_main.log 2>&1 &
```

로그 파일 실시간 확인:
```bash
tail -f /home/j-j14b110/smart_home_ai/server_ai/recommendation/daemon_retrain_main.log
```
> `[2026-03-24 15:30:00] 백그라운드 LSTM 학습 데몬을 시작합니다.`

---

## 2. 추천 연동 API 서버 단독 가동 (수동)

메인 API 서버(`9000` 포트)만 켜고 싶을 때:

```bash
nohup /home/j-j14b110/smart_home_ai/server_ai/venv/bin/python /home/j-j14b110/smart_home_ai/server_ai/recommendation/api/main.py > /home/j-j14b110/smart_home_ai/server_ai/recommendation/rec_server.log 2>&1 &
```

---

## 3. 원클릭 1초 전체 서버 복구 (요약)
GPU 서버가 뻗었다가 켜졌을 땐 묻지도 따지지도 않고 아래 명령어로 3개 프로세스를 부활시키세요!
```bash
cd /home/j-j14b110/smart_home_ai/server_ai
bash start_all_servers.sh
```

