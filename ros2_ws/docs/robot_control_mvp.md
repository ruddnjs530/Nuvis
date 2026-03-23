# Robot Control MVP Spec (Implemented)

## Scope
- `robot_msgs`: shared Topic/Service/Action contracts.
- `robot_core`: state/task/safety/sensor/module runtime.
- `robot_nav`: waypoint + navigation/return actions.

## Runtime Topology
1. Backend/Gateway sends `/robot/execute_task` action.
2. `task_executor_node` validates + orchestrates.
3. `nav_adapter_node` handles goal/return navigation actions.
4. `module_controller_node` executes module state requests.
5. `state_manager_node` publishes unified `/robot/status`.
6. `safety_manager_node` enforces estop/low-battery policy.
7. `heartbeat_node` publishes liveness.

## State Machine
- `IDLE -> RECEIVED -> VALIDATING -> ACCEPTED -> MOVING -> ARRIVED -> EXECUTING_MODULE -> RETURNING -> COMPLETED`
- failure branches: `FAILED`, `CANCELED`, emergency branch `EMERGENCY_STOPPED`

## Safety Policy (MVP)
- Emergency stop preempts all task execution.
- Low battery warning at 20%.
- Return-home trigger at 15%.
- Cancel allowed during running phases.

## Launch
```bash
ros2 launch robot_core robot_system.launch.py
```

## Validation Checklist
- [ ] Execute task accepted/rejected by validation.
- [ ] Move + module flow produces feedback and result.
- [ ] Cancel request transitions task to `CANCELED`.
- [ ] Emergency stop interrupts active execution.
- [ ] Low battery warning and return-home request are emitted.
- [ ] Status and heartbeat topics are continuously published.
