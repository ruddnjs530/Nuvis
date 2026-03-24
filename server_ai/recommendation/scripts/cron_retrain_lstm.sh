#!/bin/bash

# ========================================================
# LSTM 모델 자동 재학습 스크립트 (Cron Job 용)
# ========================================================
# 주기적인 모델 업데이트를 위해 crontab 등에 등록하여 사용합니다.
# 예시 (매일 새벽 3시에 실행):
# 0 3 * * * /path/to/server_ai/recommendation/cron_retrain_lstm.sh
# ========================================================

# 1. 서버 환경에 맞게 프로젝트 경로 수정 (GPU 서버 기준 경로로 통일)
PROJECT_DIR="/home/j-j14b110/smart_home_ai/server_ai"
VENV_DIR="$PROJECT_DIR/venv"
TARGET_SCRIPT="$PROJECT_DIR/recommendation/scripts/gpu_lstm_model.py"
LOG_DIR="$PROJECT_DIR/recommendation/logs"

# 로그 디렉토리가 없으면 생성
mkdir -p "$LOG_DIR"

# 로그 파일 이름 설정 (시간 기반)
LOG_FILE="$LOG_DIR/retrain_$(date +%Y%m%d_%H%M%S).log"

echo "========================================" >> "$LOG_FILE"
echo "시작 시간: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "LSTM 모델 재학습을 시작합니다." >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 2. 가상환경 활성화
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    echo "가상환경 활성화 완료: $VENV_DIR" >> "$LOG_FILE"
else
    echo "[경고] 가상환경 활성화 스크립트($VENV_DIR/bin/activate)를 찾을 수 없습니다." >> "$LOG_FILE"
    echo "Python 경로 등을 확인해주세요." >> "$LOG_FILE"
    # exit 1을 하지 않고 기본 python 명령어가 시스템 PATH에 의존하여 돌 수 있도록 둡니다.
fi

# 3. 학습 스크립트 실행
# gpu_lstm_model.py 내에서 CUDA 사용 여부를 자동 판별하여 학습(save_path 포함)을 수행
python "$TARGET_SCRIPT" >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "========================================" >> "$LOG_FILE"
    echo "✅ 재학습 성공적으로 완료됨 (모델 저장됨): $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
else
    echo "========================================" >> "$LOG_FILE"
    echo "❌ 재학습 중 오류 발생: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
fi

# 4. 로그 정리 (30일 이상 지난 로그 자동 삭제)
find "$LOG_DIR" -name "retrain_*.log" -type f -mtime +30 -exec rm {} \;
echo "오래된 로그 파일 정리 완료." >> "$LOG_FILE"
