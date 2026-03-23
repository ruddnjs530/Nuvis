# 작업 상태 머신

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> COMMAND_RECEIVED: execute_task goal
    COMMAND_RECEIVED --> VALIDATING
    VALIDATING --> ACCEPTED: valid
    VALIDATING --> FAILED: invalid
    ACCEPTED --> MOVING: move task
    ACCEPTED --> EXECUTING_MODULE: module only
    MOVING --> ARRIVED: goal reached
    MOVING --> FAILED: nav fail/timeout
    ARRIVED --> EXECUTING_MODULE
    EXECUTING_MODULE --> RETURNING: return policy on
    EXECUTING_MODULE --> COMPLETED: return policy off
    EXECUTING_MODULE --> FAILED: module fail
    RETURNING --> COMPLETED
    ACCEPTED --> CANCELED: cancel
    MOVING --> CANCELED: cancel
    EXECUTING_MODULE --> CANCELED: cancel
    RETURNING --> CANCELED: cancel
    IDLE --> EMERGENCY_STOPPED: estop
    COMMAND_RECEIVED --> EMERGENCY_STOPPED: estop
    VALIDATING --> EMERGENCY_STOPPED: estop
    ACCEPTED --> EMERGENCY_STOPPED: estop
    MOVING --> EMERGENCY_STOPPED: estop
    EXECUTING_MODULE --> EMERGENCY_STOPPED: estop
    RETURNING --> EMERGENCY_STOPPED: estop
```


## 재시도/취소 규칙
- 이동 재시도: 자동 1회(정책 문서 기준), 현재 구현은 자동 재시도 미적용.
- 모듈 재시도: 복구 가능 실패 시 1회(정책 문서 기준), 현재 구현은 재시도 미적용.
- 취소 허용 상태: `ACCEPTED`, `MOVING`, `EXECUTING_MODULE`, `RETURNING`.
- E-stop은 최우선이며 모든 상태를 선점한다.
