#!/bin/bash

# ========================================================
# LSTM 모델 백그라운드 무한 루프 재학습 스크립트 (Cron 대안)
# ========================================================
# 사용 방법: GPU 서버에서 아래 명령어로 백그라운드 실행을 띄워두세요.
# nohup bash daemon_retrain_lstm.sh > daemon_retrain.log 2>&1 &
# ========================================================

PROJECT_DIR="/home/j-j14b110/smart_home_ai/server_ai"
CRON_SCRIPT="$PROJECT_DIR/recommendation/scripts/cron_retrain_lstm.sh"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 백그라운드 LSTM 학습 데몬을 시작합니다."

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 재학습 스크립트 트리거"
    
    # 이전에 만들어둔 1회성 실행 스크립트(cron_retrain_lstm.sh) 호출
    bash "$CRON_SCRIPT"
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 트리거 완료. 다음 학습까지 24시간을 대기합니다..."
    
    # 24시간(86400초) 동안 대기 (컨테이너가 종료될 때까지 무한 회전)
    sleep 86400
done
