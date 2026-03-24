# External gRPC Test Client

ROS2 없이 외부 환경에서 gRPC 게이트웨이에 직접 접속해 로봇 제어 API를 테스트하는 클라이언트입니다.

## 위치
- `scripts/grpc_client/external_client.py`

## 필요 사항
- Python 3.10+
- gRPC 서버 실행 중 (`robot_gateway` 기본: `127.0.0.1:50051`)

## 설치
```bash
cd scripts/grpc_client
python -m pip install -r requirements.txt
```

## 사용 예시
GUI 실행:
```bash
python external_client_gui.py --target 127.0.0.1:50051
```

상태 조회:
```bash
python external_client.py --target 127.0.0.1:50051 status
```

상태 스트리밍 5회:
```bash
python external_client.py --target 127.0.0.1:50051 watch --interval-ms 500 --count 5
```

작업 실행:
```bash
python external_client.py --target 127.0.0.1:50051 --rpc-timeout-sec 180 execute --command-id cmd-1 --task-type 1 --target-zone hq --max-exec-sec 120
```

작업 취소:
```bash
python external_client.py --target 127.0.0.1:50051 cancel --command-id cmd-2 --task-id task-1
```

긴급 정지:
```bash
python external_client.py --target 127.0.0.1:50051 estop --command-id cmd-3 --reason emergency
```

수동 제어:
```bash
python external_client.py --target 127.0.0.1:50051 manual --command-id cmd-4 --vx 0.2 --wz 0.0 --duration-ms 1500
```

## `execute` 호출 방식
`execute`는 `웨이포인트 방식`과 `좌표 방식` 두 가지를 지원합니다.

### 웨이포인트 방식
- `target_zone`만 사용
- `target_x`, `target_y`, `target_yaw`는 기본값으로 두는 것을 권장
- 로봇 내부 `waypoints.yaml`에 등록된 이름으로 이동

예시:
```bash
python external_client.py --target 127.0.0.1:50051 execute \
  --command-id cmd-entrance-001 \
  --task-id task-entrance-001 \
  --task-type 1 \
  --target-zone entrance \
  --max-exec-sec 180
```

### 좌표 방식
- `target_zone`를 비우고 `target_x`, `target_y`, `target_yaw`를 직접 전달
- `target_pose_frame` 기본값은 `map`

예시:
```bash
python external_client.py --target 127.0.0.1:50051 execute \
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
- `target_zone`가 있어도 `target_x` 또는 `target_y`가 0이 아니면 좌표 방식
- `target_yaw`만 넣는다고 좌표 방식으로 바뀌지 않음
- `(0, 0)` 좌표를 직접 보내려면 `target_zone`를 빈 문자열로 보내야 함

### 현재 사용 가능한 waypoint 이름
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

## GUI 입력 기준
- 웨이포인트 방식: `target_zone`만 입력, `target_x/y/yaw`는 `0.0`
- 좌표 방식: `target_zone`를 비우고 `target_x/y/yaw` 입력

## 참고
- 이 클라이언트는 ROS2 패키지/`rclpy`에 의존하지 않습니다.
- RPC 스키마는 `scripts/grpc_client/robot_gateway.proto`를 기준으로 합니다.
- GUI 클라이언트는 `tkinter`(Python 기본 포함)를 사용합니다.
- `execute` 호출은 `max(rpc-timeout-sec, max_exec_sec + 30)` 규칙으로 timeout을 자동 확장합니다.
