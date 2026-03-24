# 🐳 모노레포에서의 AI 파트 도커(Docker) 배포 가이드

현재 `server_ai` 폴더는 추후 프론트엔드, 백엔드 메인 서버와 함께 하나의 거대한 저장소(Monorepo)로 통합될 예정입니다.
이에 대비하여 AI 파트를 도커 컨테이너로 띄우고 배포할 때 고려해야 할 핵심 정보들을 미리 정리한 가이드입니다.

> **2026-03-16 구조 결정 메모:** 최종 모노레포 기준으로 `server_ai`는 추천 AI와 STT 전용 서비스로 분리하고, YOLO 비전 노드는 `ros2_ws` 측 ROS2 패키지/컨테이너로 별도 운영하는 방향으로 정리했습니다. 아래 내용은 그 기준에 맞춰 업데이트했습니다.

---

## 🏗️ 1. 아키텍처 및 컨테이너 분리 전략

AI 파트는 내부적으로 크게 두 가지 성격의 애플리케이션으로 나뉩니다.
이를 모두 하나의 도커 이미지(통짜)로 만들면 이미지가 과도하게 무거워질 수 있으므로, **용도별로 멀티 컨테이너(Multi-Container) 구성**을 고려하는 것이 좋습니다.

1.  **AI API 서버 컨테이너 (`FastAPI` + `Pandas` + `Whisper`)**
    *   **역할**: Phase 2(추천 시스템)와 Phase 3(STT 자연어 파싱)를 서빙하는 REST API 전용 컨테이너.
    *   **특징**: 메인 서머(`Spring` 또는 `NestJS` 등)와 같은 네트워크로 묶여서 JSON 통신만 주고받습니다. ROS2가 굳이 필요 없습니다.
    *   **베이스 이미지**: 가벼운 `python:3.10-slim` 권장.
    *   **의존성 기준**: `requirements.txt` 중심 관리

2.  **ROS2 비전 노드 컨테이너 (`ROS2 Foxy/Humble` + `YOLOv8`)**
    *   **역할**: 시뮬레이터 또는 로봇 실물에서 카메라 토픽을 받아오고 YOLO 객체 인식을 수행하는 특수 목적형 컨테이너.
    *   **배치 위치**: 최종 모노레포에서는 `server_ai`가 아니라 `ros2_ws` 기반 패키지/컨테이너로 분리 운영.
    *   **특징**: 파이썬 환경뿐만 아니라 `ros-foxy-ros-base` 등 거대한 ROS2 코어 라이브러리와 C++ 의존성이 모두 설치되어야 합니다.
    *   **베이스 이미지**: `osrf/ros:foxy-desktop` 혹은 `ubuntu:20.04` 환경 권장.
    *   **의존성 기준**: `ultralytics`, `opencv-python` 외에 `rclpy`, `sensor_msgs`, `cv_bridge` 등 ROS2 의존성을 시스템 레벨에서 함께 준비

---

## 📝 2. Dockerfile 설계 시 핵심 주의사항

### 가. `requirements.txt` 관리
해당 파트에서 외부 패키지를 얼마나 쓰는지 명확하게 추출되어 있어야 도커 빌드가 가벼워집니다. 현존하는 파이썬 라이브러리 목록을 `requirements.txt`로 만들어 관리해야 합니다.
다만 이 프로젝트는 **`pip` 설치 항목과 ROS2 별도 의존성**을 구분해서 봐야 합니다.

#### `pip` 설치 항목

- `fastapi`
- `uvicorn`
- `pandas`
- `numpy`
- `requests`
- `scikit-learn`
- `openai-whisper`
- `python-multipart`
- `ultralytics`
- `opencv-python`

위 항목은 추천 AI / STT 컨테이너 또는 일반 파이썬 환경에서 `pip install -r requirements.txt` 로 관리합니다.

#### ROS2 별도 의존성

아래 항목은 일반 `requirements.txt`에만 넣어서는 해결되지 않으며, ROS2 베이스 이미지 또는 ROS2 시스템 패키지 설치가 필요합니다.

- `rclpy`
- `sensor_msgs`
- `cv_bridge`
- ROS2 런타임 자체 (`foxy`, `humble` 등)

즉:

- **AI API 서버 컨테이너**: `requirements.txt` 중심으로 구성
- **ROS2 비전 컨테이너**: `requirements.txt` + ROS2 시스템 의존성 별도 구성

### 나. 무거운 딥러닝 모델 가중치(Weights) 파일 분리
YOLO의 `.pt` 파일이나 Whisper의 언어 모델(.bin 등)은 용량이 수백 MB 단위입니다. 
- **문제점**: 이 파일들을 Dockerfile 안에서 `COPY` 해버리면 도커 이미지 덩치가 수 GB로 불어납니다.
- **해결책**:
  1. 런타임에 처음 한 번 다운로드받도록 파이썬 코드 구성.
  2. 도커 컴포즈 실행 시, **호스트 머신의 특정 폴더(예: `./model_cache`)를 컨테이너의 특정 디렉토리로 마운트(Volume Mount)** 시킵니다. 컨테이너가 꺼져도 모델 파일이 보존되도록 구성하는 것이 필수입니다!

### 다. GPU가상화 지원 (선택/고도화)
AI 추론(YOLO 실시간 탐지 등) 속도를 높이려면, 배포 서버에 그래픽카드(NVIDIA GPU)가 있을 경우 이를 도커 안으로 끌어다 써야 합니다.
- `docker run` 시 `--gpus all` 옵션을 줘야 하며, 베이스 이미지로 `nvidia/cuda` 지원 이미지를 고려해야 합니다.
- 단, 서버 컴퓨터(EC2 등)에 GPU가 없고 CPU 환경이라면 일반 파이썬 이미지로 빌드해도 구동은 가능합니다 (단지 추론 속도가 좀 더 걸릴 뿐입니다).

---

## 📦 3. 모노레포 Docker Compose 예시 (통합 배포 시)

최상위 루트 폴더에 위치하게 될 `docker-compose.yml` 에서 AI 파트를 어떻게 불러올지에 대한 가이드라인 뼈대입니다. 

```yaml
version: '3.8'

services:
  # 1. 메인 백엔드 서버 (예: Spring Boot)
  main-backend:
    build: ./backend
    ports:
      - "8080:8080"
    networks:
      - smart-home-net

  # 2. AI 추천 및 STT 전용 API 서버
  ai-api-server:
    build: 
      context: ./server_ai    # 모노레포 내 AI 폴더 지정
      dockerfile: Dockerfile.api # (추후 만들 API 전용 도커파일)
    ports:
      - "8000:8000"           # 내부 8000번 포트 개방
    volumes:                  # Whisper 캐시 등 모델을 컨테이너 밖 호스트에 저장하여 용량 절약
      - ./model_cache:/root/.cache/whisper
    networks:
      - smart-home-net

  # 3. ROS2 비전 처리 노드
  ai-vision-ros2:
    build:
      context: ./ros2_ws
      dockerfile: Dockerfile.ros2
    # ROS2의 DDS(Data Distribution Service) 통신 구조상 
    # 로봇 시뮬레이터 노드들과 멀티캐스트 통신이 되어야 하므로 
    # network_mode: "host" 설정을 해야 연결되는 경우가 많습니다.
    network_mode: "host" 
    # gpus: all             # (GPU 배포 서버일 경우 활성화)

networks:
  smart-home-net:
    driver: bridge
```
