# ros2_ws

로봇/제어 도메인을 위한 ROS2 워크스페이스입니다.

## 패키지
- `robot_msgs`: 인터페이스 정의
- `robot_core`: 작업/상태/안전/모듈/센서 런타임
- `robot_nav`: 내비게이션 어댑터 및 웨이포인트 처리
- `robot_gateway`: gRPC 게이트웨이(외부 <-> ROS2 브릿지)

## 문서
- `docs/API.md`: 로봇 제어 통합 API 문서
- `docs/docker_ros2.md`: ROS2 워크스페이스 Docker 빌드/실행 가이드
- `docs/unity_integration.md`: Unity 시뮬레이터 ROS-TCP 연동 가이드
- `docs/unity_integration.ko.md`: Unity 시뮬레이터 ROS-TCP 연동 가이드(한글)
- `../scripts/grpc_client/README.md`: 외부(비 ROS) gRPC 테스트 클라이언트 가이드

## 빌드
```bash
cd ros2_ws
colcon build --packages-select ros_tcp_endpoint robot_msgs robot_core robot_nav robot_gateway
```

## 환경 설정 및 실행
```bash
source install/setup.bash
ros2 launch robot_core robot_system.launch.py
```

`ros_tcp_endpoint` 패키지가 설치되어 있으면 `robot_system.launch.py`에서 자동으로 Unity TCP 엔드포인트를 함께 기동합니다.

## Docker 빠른 시작
```bash
docker compose run --rm ros2-dev bash -lc "cd /workspace/ros2_ws && colcon build --symlink-install --packages-select ros_tcp_endpoint robot_msgs robot_core robot_nav robot_gateway"
docker compose up --build ros2-run
```

## 빠른 점검
```bash
ros2 topic echo /robot/status
ros2 topic echo /robot/heartbeat
ros2 action send_goal /robot/execute_task robot_msgs/action/ExecuteTask "{task_id: 'task-1', command_id: 'cmd-1', task_type: 0, target_zone: 'living_room', module_type: 1, module_power: true, module_level: 2, max_exec_sec: 120}"
```
