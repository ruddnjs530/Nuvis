#!/bin/bash

# ==============================================================================
# [교육용 주석] 전체 AI 서버 백그라운드 구동 스크립트 (Integration Runner)
# ==============================================================================
# 역할: 보통 Node.js 서버에선 PM2 같은 도구를 쓰지만, 파이썬 기반 GPU 컨테이너 
#       OS 환경 시스템에서는 간편하고 가장 튼튼한 리눅스 내장 `nohup`과 `&` 조합을 주로 사용하여 
#       추천 API, STT API, 그리고 데몬 자동화 봇을 단 한 번의 커맨드로 모두 백그라운드에 띄웁니다.
# ==============================================================================

# 프로젝트 최상단 루트 경로 찾기 유틸
# dirname 명령어를 통해 파일이 있는 위치를 찾고 거길 절대경로(pwd)로 변환해 프로젝트 폴더를 확정 짓습니다.
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
echo "🚀 AI 서비스 백그라운드 구동을 시작합니다. (경로: $PROJECT_DIR)"

# ─────────────────────────────────────────
# 1. 추천(Recommendation) API 서버 구동 (포트 9000)
# ─────────────────────────────────────────
# nohup: SSH 터미널 창을 꺼도 프로그램이 죽지 않고 뒷단에 살아있게 만드는 리눅스 마법
# > rec_server.log: 콘솔에 파바박 찍히는 출력을 로그 파일로 전환/우회하여 저장시킴
# 2>&1: 표준 에러 로그(stderr: 2)도 일반 로그 기록지(stdout: 1)가 가는 로그 파일 한 곳으로 합침
# &: 이 구문의 프로세스 실행 완료를 기다리지 않고 바로 넘겨버려 백그라운드에서 병렬처리 되도록 분리시킴
echo "👉 1. 추천(Recommendation) API 서버 시작 중..."
nohup $PROJECT_DIR/venv/bin/python $PROJECT_DIR/recommendation/api/main.py > $PROJECT_DIR/recommendation/rec_server.log 2>&1 &

# ─────────────────────────────────────────
# 2. STT (음성 인식) API 서버 구동 (포트 9001)
# ─────────────────────────────────────────
echo "👉 2. STT (음성 인식) API 서버 시작 중..."
nohup $PROJECT_DIR/venv/bin/python $PROJECT_DIR/stt/api/main.py > $PROJECT_DIR/stt/stt_server.log 2>&1 &

# ─────────────────────────────────────────
# 3. 24시간 자동 재학습 봇 (Daemon) 구동
# ─────────────────────────────────────────
# 무한루프를 돌며 하루에 한 번씩 파이토치 학습 코드를 돌려주는 쉘 스크립트 실행
echo "👉 3. LSTM 배경 재학습 자동화 봇(Daemon) 시작 중..."
nohup bash $PROJECT_DIR/recommendation/scripts/daemon_retrain_lstm.sh > $PROJECT_DIR/recommendation/daemon_retrain_main.log 2>&1 &

echo ""
echo "✅ 모든 프로세스가 백그라운드에 등록되었습니다!"
echo "서버를 멈추고 싶다면 'pkill -f stt/api/main.py' 등 프로세스 강제 킬(Kill) 기법을 사용하세요."
