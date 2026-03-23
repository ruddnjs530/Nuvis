# robot_msgs

로봇 제어 협업을 위한 공통 ROS2 인터페이스 패키지입니다.

## 포함 인터페이스
- 메시지: `RobotStatus`, `RobotCommand`, `ModuleState`, `SensorState`, `ErrorReport`, `Heartbeat`
- 액션: `ExecuteTask`, `NavToGoal`, `ReturnHome`
- 서비스: `EmergencyStop`, `CancelTask`, `SetManualControl`, `SetModuleState`, `Relocalize`

## 빌드
```bash
colcon build --packages-select robot_msgs
```
