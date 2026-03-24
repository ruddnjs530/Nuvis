#!/bin/bash

# ==============================================================================
# GPU 컨테이너 환경을 위해 PM2 대신 사용하는 통합 실행 스크립트 (nohup 기반)
# ==============================================================================

# 프로젝트 루트 경로 찾기
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
echo "🚀 AI 서비스 백그라운드 구동을 시작합니다. (경로: $PROJECT_DIR)"

# 1. 추천 API 서버 구동 (포트 9000)
echo "👉 1. 추천(Recommendation) API 서버 시작 중..."
nohup $PROJECT_DIR/venv/bin/python $PROJECT_DIR/recommendation/api/main.py > $PROJECT_DIR/recommendation/rec_server.log 2>&1 &

# 2. STT API 서버 구동 (포트 9001)
echo "👉 2. STT (음성 인식) API 서버 시작 중..."
nohup $PROJECT_DIR/venv/bin/python $PROJECT_DIR/stt/api/main.py > $PROJECT_DIR/stt/stt_server.log 2>&1 &

# 3. 24시간 자동 재학습 봇 구동
echo "👉 3. LSTM 배경 재학습 자동화 봇(Daemon) 시작 중..."
nohup bash $PROJECT_DIR/recommendation/scripts/daemon_retrain_lstm.sh > $PROJECT_DIR/recommendation/daemon_retrain_main.log 2>&1 &

echo ""
echo "✅ 모든 프로세스가 백그라운드에 등록되었습니다!"
echo "서버를 멈추고 싶다면 'pkill -f stt/api/main.py' 등 강제 종료를 사용하세요."
