FROM python:3.10-slim

# 필요한 리눅스 패키지 설치 (OpenCV, Whisper 등 C++ 라이브러리 빌드에 필요)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 파이썬 패키지 먼저 복사 후 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 나머지 소스코드 전부 복사
COPY . .

# AI STT 서버가 동작할 포트 개방
EXPOSE 8001

# STT 서버 실행 명령어 (main.py 경로에 맞춰서 실행)
CMD ["python", "stt/main.py"]
