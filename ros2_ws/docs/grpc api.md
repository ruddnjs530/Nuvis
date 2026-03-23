# gRPC Gateway API

## 기본 정보

| 항목        | 값                            |
| --------- | ---------------------------- |
| **엔드포인트** | `0.0.0.0:50051`              |
| **패키지**   | `robot.gateway.v1`           |
| **서비스**   | `RobotGateway`               |
| **프로토콜**  | Protocol Buffers v3 (proto3) |
| **버전**    | MVP v0.1.0 (단일 로봇 R1, 단일 작업) |

---

## 아키텍처 흐름

```
Web Dashboard → Backend → gRPC (50051) → ROS Gateway → ROS2 Nodes
```

---

## RPC 목록 (총 6개)

| RPC | 유형 | ROS 브릿지 대상 |
|-----|------|----------------|
| `ExecuteTask` | Unary (블로킹) | `/robot/execute_task` (Action) |
| `CancelTask` | Unary | `/robot/cancel_task` (Service) |
| `EmergencyStop` | Unary | `/robot/emergency_stop` (Service) |
| `ManualControl` | Unary | `/robot/manual_control` (Service) |
| `GetStatus` | Unary | `/robot/status` (Topic 캐시) |
| `StreamStatus` | Server-stream | `/robot/status` (Topic 스트림) |

---

## 1. ExecuteTask — 작업 실행

> Action 최종 결과까지 대기 후 반환 (블로킹 호출)

### Request: `ExecuteTaskRequest`

| # | 필드 | 타입 | 설명 |
|---|------|------|------|
| 1 | `command_id` | `string` | 외부 명령 식별자 |
| 2 | `task_id` | `string` | 작업 식별자 |
| 3 | `task_type` | `TaskType` | 작업 유형 (enum) |
| 4 | `target_zone` | `string` | 목표 구역 이름 |
| 5 | `target_x` | `double` | 목표 X 좌표 |
| 6 | `target_y` | `double` | 목표 Y 좌표 |
| 7 | `target_yaw` | `double` | 목표 방향(yaw) |
| 8 | `module_type` | `int32` | 제어 대상 모듈 유형 |
| 9 | `module_power` | `bool` | 모듈 전원 on/off |
| 10 | `module_level` | `int32` | 모듈 세기/레벨 |
| 11 | `max_exec_sec` | `uint32` | 최대 실행 허용 시간(초) |

### Response: `ExecuteTaskResponse`

| # | 필드 | 타입 | 설명 |
|---|------|------|------|
| 1 | `accepted` | `bool` | 수락 여부 |
| 2 | `task_id` | `string` | 작업 식별자 |
| 3 | `final_state` | `int32` | 최종 상태 |
| 4 | `result_code` | `uint32` | 결과 코드 |
| 5 | `result_message` | `string` | 결과 메시지 |
| 6 | `error_code` | `uint32` | 오류 코드 |

### TaskType Enum

| 값 | 이름 | 설명 |
|----|------|------|
| 0 | `TASK_MOVE_AND_EXECUTE` | 이동 + 모듈 실행 |
| 1 | `TASK_MOVE_ONLY` | 이동만 |
| 2 | `TASK_MODULE_ONLY` | 모듈 실행만 |
| 3 | `TASK_RETURN_HOME` | 홈 복귀 |

### final_state 값

| 값 | 이름 | 설명 |
|----|------|------|
| 0 | `FINAL_COMPLETED` | 정상 완료 |
| 1 | `FINAL_FAILED` | 실패 |
| 2 | `FINAL_CANCELED` | 취소됨 |
| 3 | `FINAL_REJECTED` | 거부됨 |

---

## 2. CancelTask — 작업 취소

### Request: `CancelTaskRequest`

| # | 필드 | 타입 | 설명 |
|---|------|------|------|
| 1 | `command_id` | `string` | 외부 명령 식별자 |
| 2 | `task_id` | `string` | 취소할 작업 ID |

### Response: `CancelTaskResponse`

| # | 필드 | 타입 | 설명 |
|---|------|------|------|
| 1 | `accepted` | `bool` | 수락 여부 |
| 2 | `state` | `int32` | 취소 후 상태 |
| 3 | `message` | `string` | 결과 메시지 |

---

## 3. EmergencyStop — 긴급 정지 ⚠️ 최우선

### Request: `EmergencyStopRequest`

| # | 필드 | 타입 | 설명 |
|---|------|------|------|
| 1 | `command_id` | `string` | 외부 명령 식별자 |
| 2 | `reason` | `string` | 정지 사유 |

### Response: `EmergencyStopResponse`

| # | 필드 | 타입 | 설명 |
|---|------|------|------|
| 1 | `accepted` | `bool` | 수락 여부 |
| 2 | `applied_at` | `string` | 적용 시각 |
| 3 | `message` | `string` | 결과 메시지 |

---

## 4. ManualControl — 수동 제어

### Request: `ManualControlRequest`

| # | 필드 | 타입 | 설명 |
|---|------|------|------|
| 1 | `command_id` | `string` | 외부 명령 식별자 |
| 2 | `vx` | `float` | 선속도 (m/s) |
| 3 | `wz` | `float` | 각속도 (rad/s) |
| 4 | `duration_ms` | `uint32` | 지속 시간 (ms) |

### Response: `ManualControlResponse`

| # | 필드 | 타입 | 설명 |
|---|------|------|------|
| 1 | `accepted` | `bool` | 수락 여부 |
| 2 | `message` | `string` | 결과 메시지 |

---

## 5. GetStatus — 상태 조회 (단건)

### Request: `GetStatusRequest`

> 필드 없음 (빈 메시지)

### Response: `RobotStatusResponse`

| # | 필드 | 타입 | 설명 |
|---|------|------|------|
| 1 | `robot_id` | `string` | 로봇 식별자 |
| 2 | `mode` | `int32` | 동작 모드 |
| 3 | `task_state` | `int32` | 작업 상태 |
| 4 | `active_task_id` | `string` | 활성 작업 ID |
| 5 | `battery_pct` | `float` | 배터리 잔량 (0~100) |
| 6 | `is_charging` | `bool` | 충전 중 여부 |
| 7 | `safety_state` | `int32` | 안전 상태 |
| 8 | `last_error_code` | `uint32` | 마지막 오류 코드 |
| 9 | `pose_x` | `double` | 위치 X |
| 10 | `pose_y` | `double` | 위치 Y |
| 11 | `pose_yaw` | `double` | 방향 Yaw |
| 12 | `stamp` | `string` | 상태 시각 |

### mode 값

| 값 | 이름 |
|----|------|
| - | `IDLE` / `MANUAL` / `AUTONOMOUS` / `DOCKING` / `ERROR` |

### safety_state 값

| 값 | 이름 |
|----|------|
| - | `NORMAL` / `WARN` / `ESTOP` |

---

## 6. StreamStatus — 상태 스트림 (Server Streaming)

### Request: `StreamStatusRequest`

| # | 필드 | 타입 | 설명 |
|---|------|------|------|
| 1 | `interval_ms` | `uint32` | 전송 간격 (ms), **100~10000으로 보정** |

### Response: `stream RobotStatusResponse`

> `GetStatus`와 동일한 `RobotStatusResponse`가 반복 전송됨

---

## 오류 코드 표

| 코드 | 이름 | 설명 | 심각도 |
|------|------|------|--------|
| 0 | `OK` | 정상 | - |
| 1001 | `VALIDATION_FAILED` | 명령 검증 실패 | ERROR |
| 2001 | `NAVIGATION_FAILED` | 이동/복귀 실패 | ERROR |
| 3001 | `MODULE_FAILED` | 모듈 제어 실패 | ERROR |
| 4001 | `CANCELED` | 작업 취소 | INFO |
| 5001 | `EMERGENCY_STOP` | 긴급 정지 | FATAL |
| 5002 | `LOW_BATTERY` | 저전력 이벤트 | WARN |
| 6001 | `LOCALIZATION_LOST` | 위치추정 신뢰도 하락 | ERROR |

---

## 동작 주의사항

| 항목 | 내용 |
|------|------|
| `ExecuteTask` | Action 최종 결과까지 **블로킹 대기** 후 반환 |
| `StreamStatus` | `interval_ms`는 **100~10000** 범위로 자동 보정 |
| ROS 미기동 시 | `accepted=false` + 오류 메시지 반환 |
| 최우선 명령 | `EmergencyStop` (어떤 상태에서든 즉시 처리) |
| Goal 수락 타임아웃 | 1초 |
| 작업 기본 타임아웃 | 300초 |

---

## 호출 예시

### Python (외부 클라이언트, ROS 불필요)

```bash
# 상태 조회
python external_client.py --target 127.0.0.1:50051 status

# 상태 스트림
python external_client.py --target 127.0.0.1:50051 watch --interval-ms 500 --count 5

# 작업 실행 (이동+모듈)
python external_client.py --target 127.0.0.1:50051 execute \
  --command-id cmd-1 --task-type 0 --target-zone living_room \
  --module-type 1 --module-power --module-level 2 --max-exec-sec 120

# 작업 취소
python external_client.py --target 127.0.0.1:50051 cancel \
  --command-id cmd-2 --task-id task-1

# 긴급 정지
python external_client.py --target 127.0.0.1:50051 estop \
  --command-id cmd-3 --reason emergency

# 수동 제어
python external_client.py --target 127.0.0.1:50051 manual \
  --command-id cmd-4 --vx 0.2 --wz 0.0 --duration-ms 1500
```

### GUI 클라이언트

```bash
cd scripts/grpc_client
pip install -r requirements.txt
python external_client_gui.py --target 127.0.0.1:50051
```