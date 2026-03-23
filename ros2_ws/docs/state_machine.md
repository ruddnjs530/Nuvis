# Task State Machine

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

## Retry/Cancellation Rules
- Navigation retry: 1 automatic retry (policy document), current implementation: no automatic retry yet.
- Module retry: recoverable failure 1 retry (policy document), current implementation: no retry yet.
- Cancellation allowed during `ACCEPTED`, `MOVING`, `EXECUTING_MODULE`, `RETURNING`.
- E-stop has highest priority and preempts all states.
