# robot_msgs v0.1.0 Interface Spec

## Purpose
- Shared contract for backend, ROS gateway, robot runtime, and Unity simulation.
- MVP-first schema for single robot (`robot_id=R1`) and single active task.

## Topics
- `/robot/status` (`robot_msgs/RobotStatus`) at 2 Hz
- `/robot/heartbeat` (`robot_msgs/Heartbeat`) at 1 Hz
- `/robot/sensor_state` (`robot_msgs/SensorState`) at 2 Hz
- `/robot/error_report` (`robot_msgs/ErrorReport`) on event
- `/robot/module/state` (`robot_msgs/ModuleState`) at 1 Hz
- `/robot/module/swap_event` (`robot_msgs/ModuleSwapEvent`) on event
- `/robot/module/operation_event` (`robot_msgs/ModuleOperationEvent`) on event

## Actions
- `/robot/execute_task` (`robot_msgs/action/ExecuteTask`)
- `/robot/nav_to_goal` (`robot_msgs/action/NavToGoal`)
- `/robot/nav_path` (`robot_msgs/action/NavPath`) for internal multi-segment navigation
- `/robot/return_home` (`robot_msgs/action/ReturnHome`)

## Services
- `/robot/emergency_stop` (`robot_msgs/srv/EmergencyStop`)
- `/robot/cancel_task` (`robot_msgs/srv/CancelTask`)
- `/robot/manual_control` (`robot_msgs/srv/SetManualControl`)
- `/robot/module/set` (`robot_msgs/srv/SetModuleState`)
- `/robot/relocalize` (`robot_msgs/srv/Relocalize`)

`SetModuleState.srv` request fields:
- `module_type`
- `power_on`
- `level`
- `task_id`
- `command_id`

## IDs and Tracking
- `command_id`: created by backend/gateway for idempotency.
- `task_id`: created upstream or by orchestrator for execution tracking.
- At least one of the IDs must appear in status/feedback/result/error streams.

## Timeout and Retry Defaults
- Goal accept timeout: 1 second.
- Execute timeout default: 300 seconds.
- Move retry: 1 automatic retry for recoverable navigation failure.
- Emergency stop preempts all actions.
