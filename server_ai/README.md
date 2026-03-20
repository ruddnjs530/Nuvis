# 스마트 홈 로봇 - AI Part (`server_ai`)

스마트 홈 대시보드와 로봇, IoT 모듈을 연동하는 프로젝트의 **AI 전담 파트 작업공간**입니다.  
현재 기준으로 `server_ai`는 **추천 AI + STT 전용 서비스**를 중심으로 관리하고, YOLO 비전 노드는 프로토타입만 함께 보관한 뒤 추후 `ros2_ws` 측으로 재배치하는 방향으로 정리했습니다.

> 참고: 현재 저장소에는 초기 프로토타입 단계의 `vision/` 코드가 함께 포함되어 있으나, 이는 최종 배치 기준으로는 `server_ai`의 주 책임 범위에 포함하지 않습니다.

## 📂 폴더 구조
```text
📦 server_ai/
 ┣ 📂 docs/
 ┃  ┣ 📂 shared/                  # 팀 공유 문서
 ┃  ┃  ┣ 📄 backend_integration_proposal.md
 ┃  ┃  ┣ 📄 docker_deployment_guide.md
 ┃  ┃  ┣ 📄 git_sparse_guide.md
 ┃  ┃  ┗ 📂 api/
 ┃  ┗ 📂 personal/                # 개인 작업 문서
 ┃     ┣ 📄 ai_roadmap.md
 ┃     ┣ 📄 dev_log.md
 ┃     ┣ 📄 daily_todo.md
 ┃     ┗ 📄 portfolio.md
 ┣ 📂 recommendation/             # Phase 2: IoT 데이터 기반 추천 AI API
 ┣ 📂 stt/                        # Phase 3: Whisper 기반 STT / 파서
 ┣ 📂 vision/                     # YOLO ROS2 노드 프로토타입 (추후 ros2_ws 측 분리 예정)
 ┣ 📄 requirements.txt
 ┗ 📄 test_client.py
```

## 🚀 시작하기 (Getting Started)

### 1. 환경 설정
프로젝트는 파이썬 환경의 가상환경(venv) 구축을 권장합니다.

```sh
python -m venv venv
# Windows:
source venv/Scripts/activate

pip install -r requirements.txt
```

#### ✅ `pip`로 설치하는 항목

현재 `requirements.txt` 기준으로 아래 패키지들이 설치됩니다.

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

#### ⚠️ ROS2 쪽은 `pip`와 별도입니다

`vision/yolo_node.py`는 일반 파이썬 패키지만으로는 실행되지 않습니다.
아래 항목은 **ROS2 환경 설치 및 sourcing** 이 별도로 필요합니다.

- `rclpy`
- `sensor_msgs`
- `cv_bridge`
- ROS2 배포판 자체 설치 (`foxy`, `humble` 등)

즉:

- 추천 시스템 / STT만 실행: `pip install -r requirements.txt` 로 시작 가능
- 비전 프로토타입까지 실행: 위 `pip` 패키지 + ROS2 별도 환경 필요

### 2. 모듈별 실행 방법

#### 🤖 비전 프레임워크 (YOLO ROS2 Node, 프로토타입 보관)
*   **경로:** `vision/yolo_node.py`
*   **설명:** 주행 파트의 로봇/시뮬레이터에서 발행하는 카메라 토픽(`image_raw`)을 Subscribe 하고, YOLO 모델을 사용해 전방의 장애물을 탐지하여 결과를 로깅/Publish 합니다.
*   **배치 방향:** 최종 모노레포에서는 일반 AI API 서버가 아닌 `ros2_ws` 측 비전 패키지로 재배치 예정입니다.
*   **의존성 구분:** `ultralytics`, `opencv-python`은 `pip`로 설치 가능하지만, `rclpy`, `sensor_msgs`, `cv_bridge`는 ROS2 환경에서 별도 준비해야 합니다.
*   **실행:** `python yolo_node.py` (ROS2 환경 sourcing 필수)

#### 📈 추천 시스템 (AI Recommendation API)
*   **경로:** `recommendation/main.py`, `recommendation/generate_mock_data.py`
*   **설명:** 서버의 환경 데이터와 유저의 과거 모듈 제어 내역을 Pandas로 분석하여 이동 평균 기반 통계 임계값(`pm25_alert_threshold` 등)을 스마트하게 산출하고 추천합니다.
*   **의존성 구분:** 이 모듈은 ROS2 없이 `pip install -r requirements.txt` 만으로 실행 가능합니다.
*   **실행:**
    1.  `python generate_mock_data.py` : 테스트용 가상 데이터 생성 (`mock_payload.json`)
    2.  `python gpu_lstm_model.py` : LSTM 기반 시계열 예측 모델 학습 및 저장 (`model/lstm_device_model.pth`)
        - **주의:** GPU 서버 환경에서 실행 시 GPU 가속을 활용하며, 학습 완료 후 최신 모델이 자동 저장됩니다.
    3.  `python main.py` : Uvicorn 내부 API 서버 실행 (기본 포트 8000)
    4.  `GET http://localhost:8000/api/event/ai-suggestions` 로 결과 확인 가능.

#### 🎙️ 음성 인식 제어 (STT Pipeline)
*   **경로:** `stt/whisper_test.py`, `stt/stt_parser.py`
*   **설명:** 사람의 녹음된 목소리 `.wav` 파일을 입력받아 텍스트로 바꾸고(OpenAI Whisper), 자연어 텍스트 문맥과 의도를 파악하여 `{대상, 모듈, 전원_상태}` 구조화된 JSON 로봇 제어 명령어 객체로 만듭니다.
*   **의존성 구분:** 이 모듈도 ROS2 없이 `pip install -r requirements.txt` 만으로 시작할 수 있습니다. 단, Whisper 추론 성능을 위해 GPU 환경 권장.
*   **실행:** `python whisper_test.py` (동일 폴더 내에 음성 파일 구비 필요)

## 📌 비고 (관련 문서)
본 프로젝트에 대한 더 자세한 내용은 아래의 문서들을 참고해 주시기 바랍니다.

### 🗂️ 공유 문서 (`docs/shared/`)
- [📐 시스템 아키텍처](docs/shared/시스템_아키텍처.png): 전체 서버/로봇/IoT 통신 구조 다이어그램
- [🗄️ ERD](docs/shared/ERD.jpg): 전체 데이터베이스 스키마 설계
- [🏆 MVP 요구사항](docs/shared/MVP.md): 전체 프로젝트 기능 요구사항 명세
- [📋 API 명세서](docs/shared/api/API_명세서.md): AI 서버 ↔ 백엔드 서버 API 계약 명세
- [🔗 백엔드 연동 제안서](docs/shared/backend_integration_proposal.md): AI 서버 ↔ 백엔드 연동 아키텍처 및 DB 수정 요청
- [🐳 Docker 배포 가이드](docs/shared/docker_deployment_guide.md): 멀티 컨테이너 배포 및 운영 기준
- [🤖 자동화 연동 논의](docs/shared/automation_discussion_guide.md): AI ↔ 백엔드 Push/Polling 방식 의사결정 가이드
- [🔄 GPU 서버 연동](docs/shared/git_sparse_guide.md): GPU 환경에서 AI 파트만 부분 복제하는 방법 안내

### 👤 개인 문서 (`docs/personal/`)
- [🏅 포트폴리오](docs/personal/portfolio.md): 프로젝트 개요, 주요 성과, 기술 스택, 팀 회고
- [🗺️ AI 파트 로드맵](docs/personal/ai_roadmap.md): AI 파트 단계별 개발 계획 및 통합 아키텍처
- [📝 개발 일지](docs/personal/dev_log.md): AI 작업 내역, 구조 변경, 트러블슈팅 기록
- [✅ 일일 목표 및 할 일](docs/personal/daily_todo.md): 일일 업무 로그 및 TODO
