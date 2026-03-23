# robot_gateway

외부 클라이언트가 로봇 ROS2 제어 인터페이스를 사용할 수 있도록 제공하는 gRPC 게이트웨이 패키지입니다.

## 구성 요소
- `grpc_gateway_node`: gRPC 서버 -> ROS Action/Service 브릿지
- `grpc_test_client`: 게이트웨이 RPC 호출용 CLI 테스트 클라이언트
- `proto/robot_gateway.proto`: gRPC 계약 정의

## 기본 gRPC 엔드포인트
- `0.0.0.0:50051`

## 런타임 파라미터
- `grpc_host` (기본값: `0.0.0.0`)
- `grpc_port` (기본값: `50051`)
- `target_pose_frame` (기본값: `map`)
  - `execute` 요청에서 `target_x/target_y/target_yaw`를 Pose로 만들 때 사용
  - 외부 클라이언트가 Unity 좌표를 직접 보내면 `target_pose_frame:=unity` 사용

## 빌드
```bash
python -m pip install grpcio grpcio-tools
colcon build --packages-select robot_gateway
```

## 실행
```bash
ros2 run robot_gateway grpc_gateway_node
```

## 테스트 클라이언트 예시
```bash
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 status
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 execute --command-id cmd-1 --task-type 0 --target-zone living_room --module-type 1 --module-power --module-level 2 --max-exec-sec 120
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 cancel --command-id cmd-2 --task-id task-1
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 estop --command-id cmd-3 --reason emergency
```
