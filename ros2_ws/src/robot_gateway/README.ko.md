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

## ExecuteTask 요청 방식
`ExecuteTaskRequest`는 두 가지 이동 방식을 지원합니다.

### 1. 웨이포인트 방식
- `target_zone`에 zone 이름을 넣어 요청
- 로봇 내부에서 `waypoints.yaml`을 조회해 좌표로 변환
- 운영 관점에서는 이 방식을 우선 권장

조건:
- `target_zone`이 비어있지 않음
- `target_x == 0.0`
- `target_y == 0.0`

예시:
```bash
python scripts/grpc_client/external_client.py --target 127.0.0.1:50051 execute \
  --command-id cmd-entrance-001 \
  --task-id task-entrance-001 \
  --task-type 1 \
  --target-zone entrance \
  --max-exec-sec 180
```

### 2. 좌표 방식
- `target_x`, `target_y`, `target_yaw`를 직접 전달
- 게이트웨이가 ROS `PoseStamped`로 변환해 로봇에 전달
- 디버깅/임시 테스트에는 유용하지만 운영 요청은 웨이포인트 방식이 더 안전

조건:
- `target_zone`이 빈 문자열이거나
- `target_x != 0.0` 또는 `target_y != 0.0`

예시:
```bash
python scripts/grpc_client/external_client.py --target 127.0.0.1:50051 execute \
  --command-id cmd-pose-001 \
  --task-id task-pose-001 \
  --task-type 1 \
  --target-zone "" \
  --target-x -6.0 \
  --target-y 10.0 \
  --target-yaw 0.0 \
  --max-exec-sec 180
```

### 우선순위 규칙
- `target_zone`만 채우고 `target_x`, `target_y`를 `0.0`으로 두면 웨이포인트 방식
- `target_zone`를 채웠더라도 `target_x` 또는 `target_y`가 0이 아니면 좌표 방식
- `target_yaw`만 바꾸고 `target_x`, `target_y`가 `0.0`이면 웨이포인트 방식으로 처리됨
- `(0, 0)` 좌표로 직접 보내고 싶으면 `target_zone`를 반드시 빈 문자열로 보내야 함

## 현재 등록된 웨이포인트
- `hq`
- `entrance`
- `entrance_next_room`
- `pc`
- `tv`
- `picture`
- `kitchen`
- `first_toilet`
- `toilet_next_room`
- `left_up_room`
- `left_down_room`
- `second_toilet`

## 테스트 클라이언트 예시
```bash
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 status
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 execute --command-id cmd-1 --task-type 1 --target-zone hq --max-exec-sec 120
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 execute --command-id cmd-2 --task-type 1 --target-zone "" --target-x -6.0 --target-y 10.0 --target-yaw 0.0 --max-exec-sec 120
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 cancel --command-id cmd-2 --task-id task-1
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 estop --command-id cmd-3 --reason emergency
```
