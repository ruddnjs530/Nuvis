# robot_core

로봇 상태, 작업 생명주기, 센서 융합, 모듈 제어, 안전 처리를 담당하는 ROS2 네이티브 실행 계층입니다.

## 노드
- `state_manager_node`: `/robot/status` 발행
- `heartbeat_node`: `/robot/heartbeat` 발행
- `sensor_fusion_node`: `/robot/sensor_state` 발행 (mock 값)
- `module_controller_node`: `/robot/module/set` 서비스 제공
- `safety_manager_node`: `/robot/emergency_stop` 서비스 제공, 저전력 감시
- `task_executor_node`: `/robot/execute_task`, `/robot/cancel_task`, `/robot/manual_control` 제공

## 핵심 토픽
- `/robot/status` (`robot_msgs/RobotStatus`)
- `/robot/heartbeat` (`robot_msgs/Heartbeat`)
- `/robot/sensor_state` (`robot_msgs/SensorState`)
- `/robot/error_report` (`robot_msgs/ErrorReport`)
- `/robot/task_feedback` (`robot_msgs/action/ExecuteTask_Feedback`)

## 실행
```bash
ros2 launch robot_core robot_core.launch.py
ros2 launch robot_core robot_system.launch.py
```
