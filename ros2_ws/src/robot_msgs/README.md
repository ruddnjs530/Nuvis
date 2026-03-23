# robot_msgs

Shared ROS2 interface package for robot control collaboration.

## Included Interfaces
- Messages: `RobotStatus`, `RobotCommand`, `ModuleState`, `SensorState`, `ErrorReport`, `Heartbeat`
- Actions: `ExecuteTask`, `NavToGoal`, `ReturnHome`
- Services: `EmergencyStop`, `CancelTask`, `SetManualControl`, `SetModuleState`, `Relocalize`

## Build
```bash
colcon build --packages-select robot_msgs
```
