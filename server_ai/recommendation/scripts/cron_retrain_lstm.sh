#!/bin/bash

# ========================================================
# [교육용 주석] LSTM 모델 자동 재학습 스크립트 (Cron Job/단발성 실행 용)
# ========================================================
# 1. 역할: 
#    - 이 스크립트가 실행될 때마다 파이썬 가상환경을 세팅하고, 
#    - 파이썬 학습 코드(gpu_lstm_model.py)를 실행하여 LSTM 모델을 갱신합니다.
#    - 데몬 스크립트나 crontab(리눅스 작업 스케줄러)에서 주기적으로 이 파일을 호출합니다.
# ========================================================

# 1. 경로 설정 (GPU 서버 기준 절대 경로 통일)
# 백그라운드 실행 환경에서는 $PATH 같은 환경변수나 현재 위치가 보장되지 않아 에러를 방지하고자 절대 경로를 사용합니다.
PROJECT_DIR="/home/j-j14b110/smart_home_ai/server_ai"
VENV_DIR="$PROJECT_DIR/venv"
TARGET_SCRIPT="$PROJECT_DIR/recommendation/scripts/gpu_lstm_model.py"
LOG_DIR="$PROJECT_DIR/recommendation/logs"

# 로그 디렉토리가 없으면 생성
# mkdir의 -p 옵션은 필요한 경우 부모 디렉토리까지 한번에 생성하며, 디렉토리가 이미 존재해도 에러가 나지 않게 합니다.
mkdir -p "$LOG_DIR"

# 로그 파일 이름 설정
# `date +%Y%m%d_%H%M%S` 명령어는 '20260325_083000' 같은 현재 시간 문자열을 만듭니다.
# 결과적으로 학습이 일어날 때마다 시간별로 로그 파일이 분리되어 저장됩니다.
LOG_FILE="$LOG_DIR/retrain_$(date +%Y%m%d_%H%M%S).log"

# >> 연산자는 파일의 끝에 내용(텍스트)을 추가(append)하는 기능입니다. 
# (> 기호를 하나만 쓰면 기존 내용을 전부 지우고 덮어쓰게 됩니다.)
echo "========================================" >> "$LOG_FILE"
echo "시작 시간: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "LSTM 모델 재학습을 시작합니다." >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 2. 가상환경 활성화
# 파이썬 모델 스크립트가 필요한 라이브러리(PyTorch, Pandas 등)를 사용하기 위해 venv를 먼저 켜주는 작업입니다.
if [ -f "$VENV_DIR/bin/activate" ]; then
    # source 명령어는 다른 스크립트(가상환경 활성화 스크립트)의 내용을 가져와 지금 터미널 환경에 바로 적용시킵니다.
    source "$VENV_DIR/bin/activate"
    echo "가상환경 활성화 완료: $VENV_DIR" >> "$LOG_FILE"
else
    # 가상환경이 없더라도, 시스템 전역 Python을 사용할 수도 있으므로 에러 로그만 남기고 일단 진행하게 합니다.
    echo "[경고] 가상환경 활성화 스크립트($VENV_DIR/bin/activate)를 찾을 수 없습니다." >> "$LOG_FILE"
    echo "Python 경로 등을 확인해주세요." >> "$LOG_FILE"
fi

# 3. 학습 스크립트 실행
# 실제 파이썬 코드를 실행하여 LSTM 모델을 재학습합니다.
# '>> "$LOG_FILE" 2>&1' 구문의 뜻:
# 파이썬 스크립트에서 발생하는 일반 출력(stdout: 1)과 에러 출력(stderr: 2)을 모두 LOG_FILE 한 곳에 기록하라는 명령입니다.
python "$TARGET_SCRIPT" >> "$LOG_FILE" 2>&1

# $? 는 바로 직전에 실행된 명령어(여기서는 python 구동)의 종료 상태코드(Exit Status)를 담고 있는 특별한 변수입니다.
# 파이썬 스크립트가 성공적으로 끝났다면 상태코드가 0이 되고, 중간에 에러가 났다면 0이 아닌 값이 됩니다.
if [ $? -eq 0 ]; then
    echo "========================================" >> "$LOG_FILE"
    echo "✅ 재학습 성공적으로 완료됨 (모델 저장됨): $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
else
    echo "========================================" >> "$LOG_FILE"
    echo "❌ 재학습 중 오류 발생: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
fi

# 4. 로그 정리
# 로그 파일이 무한정 쌓이면 서버의 디스크 용량을 차지하므로, 너무 오래된 파일은 정기적으로 지워줍니다.
# -name "retrain_*.log" : 대상 파일 이름 패턴
# -type f : 파일(디렉토리 말고)만 찾으라는 뜻
# -mtime +30 : 내용이 수정된 지 30일이 지난 파일을 찾음
# -exec rm {} \; : 찾은 각 파일( {} 로 표시됨 )을 대상으로 rm(삭제) 명령어를 실행함
find "$LOG_DIR" -name "retrain_*.log" -type f -mtime +30 -exec rm {} \;
echo "오래된 로그 파일 정리 완료." >> "$LOG_FILE"
