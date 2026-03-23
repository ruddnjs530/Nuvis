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
python external_client.py --target 127.0.0.1:50051 --rpc-timeout-sec 30 execute --command-id cmd-1 --task-type 0 --target-zone living_room --module-type 1 --module-power --module-level 2 --max-exec-sec 120
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

## 참고
- 이 클라이언트는 ROS2 패키지/`rclpy`에 의존하지 않습니다.
- RPC 스키마는 `scripts/grpc_client/robot_gateway.proto`를 기준으로 합니다.
- GUI 클라이언트는 `tkinter`(Python 기본 포함)를 사용합니다.
