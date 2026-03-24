# ROS2 Docker 가이드

이 문서는 `ros2_ws`를 Docker(WSL2 기반)에서 빌드/실행하고, `ros2-rviz` 서비스로 RViz GUI를 Windows 화면에 표시하는 방법을 설명합니다.

## 1. 구성 파일
- Dockerfile: `docker/ros2/Dockerfile`
- Entrypoint: `docker/ros2/entrypoint.sh`
- Compose: `docker-compose.yml`
  - `ros2-run`: 시스템 런치(`robot_system.launch.py`)
  - `ros2-rviz`: RViz 디버깅 전용 GUI 서비스
  - `ros2-dev`: 개발용 쉘 서비스
- RViz 기본 설정: `ros2_ws/src/robot_nav/config/nav_debug.rviz`

## 2. 사전 준비
- Windows 11 + WSL2 + Docker Desktop(WSL 통합 활성화)
- Unity 연동 시 `ros2_ws/src/ROS-TCP-Endpoint` 소스 포함
- RViz 사용 시 **WSL 터미널에서** `docker compose` 실행 권장

### 2-1. WSLg 점검
WSL 터미널에서 아래를 확인하세요.

```bash
echo "$DISPLAY"
echo "$WAYLAND_DISPLAY"
echo "$XDG_RUNTIME_DIR"
ls /mnt/wslg
ls /mnt/wslg/.X11-unix
```

정상 예:
- `DISPLAY` 값 존재(예: `:0`)
- `WAYLAND_DISPLAY` 값 존재(예: `wayland-0`)
- `/mnt/wslg` 디렉터리 접근 가능
- `/mnt/wslg/.X11-unix/X0` 소켓 존재

### 2-2. `install/setup.bash` 관련
- `ros2_ws/install/setup.bash`는 저장소 커밋 대상이 아닙니다.
- `colcon build` 후 `ros2_ws/install/`에 생성됩니다.
- 처음에는 파일이 없는 것이 정상입니다.

## 3. 이미지 빌드
프로젝트 루트에서:

```bash
docker build -f docker/ros2/Dockerfile -t b110-ros2:humble .
```

## 4. 시스템 실행(ros2-run)
프로젝트 루트에서:

```bash
docker compose up -d --build ros2-run
docker compose logs -f ros2-run
```

`ros2-run`은 내부에서 아래를 수행합니다.
- `colcon build --symlink-install --packages-select ros_tcp_endpoint robot_msgs robot_core robot_nav robot_gateway`
- `source install/setup.bash`
- `ros2 launch robot_core robot_system.launch.py`

## 5. RViz GUI 실행(ros2-rviz)
`ros2-run`과 같은 ROS Domain을 사용해 RViz를 띄웁니다.

```bash
docker compose up -d --build ros2-run ros2-rviz
docker compose logs -f ros2-rviz
```

동작 방식:
- `ros2-rviz`는 `install/setup.bash` 생성까지 대기 후 실행(최대 10분)
- RViz는 `ros2_ws/src/robot_nav/config/nav_debug.rviz`를 자동 로드
- Fixed Frame은 `map`으로 기본 설정

## 6. 자주 쓰는 명령
개발 쉘 진입:

```bash
docker compose up -d --build ros2-dev
docker compose exec ros2-dev bash
```

실행 중 토픽 확인:

```bash
docker compose exec ros2-run bash -lc "source /workspace/ros2_ws/install/setup.bash && ros2 topic list"
```

RViz만 재기동:

```bash
docker compose restart ros2-rviz
```

종료:

```bash
docker compose down
```

## 7. 포트
- gRPC Gateway: `50051:50051`
- Unity ROS-TCP Endpoint: `10000:10000`

## 8. RViz 기본 관찰 토픽
`nav_debug.rviz`는 아래 토픽/프레임 관찰을 기본으로 포함합니다.
- Frame: `map` (Fixed Frame)
- `/map`
- `/tf`
- `/scan`
- `/scan_nav`
- `/odom`
- `/amcl_pose`
- `/plan`
- `/local_plan`
- `/unity/robot_pose`

참고:
- `/robot/status`, `/robot/task_feedback`, `/robot/error_report`는 RViz 기본 디스플레이 타입이 아니므로 `ros2 topic echo` 또는 별도 시각화 도구로 확인합니다.

## 9. 트러블슈팅
### 9-1. RViz 창이 안 뜰 때
- WSL 터미널에서 실행했는지 확인
- `/mnt/wslg` 마운트 상태 확인:

```bash
docker compose exec ros2-rviz bash -lc "ls /mnt/wslg"
```

### 9-2. Qt/Display 에러가 날 때
- `ros2-rviz` 로그에서 `xcb`, `wayland` 관련 에러 확인
- WSLg 환경 변수 재확인(`DISPLAY`, `WAYLAND_DISPLAY`, `XDG_RUNTIME_DIR`)
- 특히 아래 오류는 X11 소켓 미연결이 원인입니다.
  - `qt.qpa.xcb: could not connect to display :0`
  - `Could not load the Qt platform plugin "xcb"`

권장 확인 순서:

```bash
# 1) WSL 내부에서 실행 중인지 확인
uname -a

# 2) WSLg 소켓 존재 확인
ls -l /mnt/wslg/.X11-unix/X0

# 3) compose를 WSL 터미널에서 실행
docker compose up -d --build ros2-run ros2-rviz
docker compose logs -f ros2-rviz
```

PowerShell/CMD에서 직접 실행하면 WSLg 소켓 마운트가 비정상일 수 있으므로, 반드시 WSL 터미널에서 실행하세요.

### 9-3. RViz에 TF/토픽이 비어 있을 때
- `ros2-run`과 `ros2-rviz`의 `ROS_DOMAIN_ID`가 동일한지 확인
- `ros2-run`이 정상 기동했는지 확인:

```bash
docker compose logs -f ros2-run
```

### 9-4. 시간이 멈춘 것처럼 보일 때
- `use_sim_time=true` 환경에서 `/clock`이 정상 발행되는지 확인
- `/clock`이 정지하면 Nav2/RViz 갱신이 멈춘 것처럼 보일 수 있음

### 9-5. `Message Filter dropping message ... earlier than transform cache`
- Unity 원본 `/scan` 타임스탬프와 ROS TF 시간이 어긋나면 발생합니다.
- 기본 설정에서 `unity_scan_bridge_node`가 `/scan -> /scan_nav`로 타임스탬프를 보정합니다.
- 아래로 입력/보정 토픽을 각각 확인하세요.

```bash
docker compose exec ros2-run bash -lc "source /workspace/ros2_ws/install/setup.bash && ros2 topic hz /scan"
docker compose exec ros2-run bash -lc "source /workspace/ros2_ws/install/setup.bash && ros2 topic hz /scan_nav"
```
