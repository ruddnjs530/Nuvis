# robot_core

ROS2 native execution layer for robot state, task lifecycle, sensor fusion, module control, and safety handling.

## Nodes
- `state_manager_node`: publishes `/robot/status`
- `heartbeat_node`: publishes `/robot/heartbeat`
- `sensor_fusion_node`: publishes `/robot/sensor_state` (mock values)
- `module_controller_node`: serves `/robot/module/set`
- `safety_manager_node`: serves `/robot/emergency_stop`, monitors low battery
- `task_executor_node`: serves `/robot/execute_task`, `/robot/cancel_task`, `/robot/manual_control`

## Key Topics
- `/robot/status` (`robot_msgs/RobotStatus`)
- `/robot/heartbeat` (`robot_msgs/Heartbeat`)
- `/robot/sensor_state` (`robot_msgs/SensorState`)
- `/robot/error_report` (`robot_msgs/ErrorReport`)
- `/robot/task_feedback` (`robot_msgs/action/ExecuteTask_Feedback`)

## Launch
```bash
ros2 launch robot_core robot_core.launch.py
ros2 launch robot_core robot_system.launch.py
```
