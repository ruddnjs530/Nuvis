# STT 시스템 (GPU 서버) 재부팅/시작 시 가이드

GPU 서버 전원이 꺼졌다가 켜지거나, 컨테이너가 재시작되었을 때 STT(음성 인식 및 파싱) API 서버를 백그라운드로 띄워두기 위한 가이드입니다.

---

## 1. STT API 서버 백그라운드 가동

Whisper 모델 렌더링 및 음성 처리를 담당하는 FastAPI 서버(`main.py`)를 `9001` 포트에서 백그라운드로 실행합니다.

### 🚀 실행 방법 (통합 스크립트 권장)

GPU 머신 환경 제약으로 인해 `PM2` 대신 최상위 폴더에 마련된 **`start_all_servers.sh`** 스크립트 하나로 추천 서버와 함께 통합 가동하실 것을 권장합니다.

```bash
# PM2 없이 모든 서버 1초 구동 스크립트
cd /home/j-j14b110/smart_home_ai/server_ai
bash start_all_servers.sh
```

### ✅ 개별 가동 및 정상 확인

만약 STT 파트만 단독으로 켜고 싶다면 아래 `nohup` 명령을 사용하세요.
```bash
nohup /home/j-j14b110/smart_home_ai/server_ai/venv/bin/python /home/j-j14b110/smart_home_ai/server_ai/stt/api/main.py > /home/j-j14b110/smart_home_ai/server_ai/stt/stt_server.log 2>&1 &
```

서버 정상 작동 확인을 위해 실시간 로그 포착:
```bash
tail -f /home/j-j14b110/smart_home_ai/server_ai/stt/stt_server.log
```
*(Application startup complete. 문구가 뜨면 성공입니다.)*

2. **API 헬스체크 (스모크 테스트)**
   FastAPI가 완전히 뜬 것을 확인했다면, 실제 헬스체크 API를 호출해 봅니다.
   ```bash
   curl http://127.0.0.1:9001/api/stt/health
   ```
   **정상 응답 예시:** `{"device":"cuda","model_path":"v2_full","room_map_source":"fallback"}`

---

## 2. 주의 사항
- `v2_full` 모델 로드 과정에서 시간이 수 분 정도 소요될 수 있습니다. `curl` 헬스체크 응답이 오지 않는다면 `tail -f` 로 로그를 살피며 모델 로드율을 확인해 주세요.
- 로그 파일(`stt_server.log`)의 용량이 지나치게 커지면 주기적으로 직접 지워주시거나 `> /dev/null` 처리를 고려합니다.
