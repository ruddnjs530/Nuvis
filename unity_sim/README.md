# Unity Simulator Integration (ROS-TCP)

Unity simulator should use Unity's official ROS connector stack, not custom UDP bridge code.

## Required Unity Package
- `com.unity.robotics.ros-tcp-connector`

## ROS Endpoint
- ROS node: `ros_tcp_endpoint/default_server_endpoint`
- Default port: `10000`

`robot_system.launch.py` starts this endpoint automatically when `ros_tcp_endpoint` exists.

If missing, add it to ROS workspace:

```bash
cd ros2_ws/src
git clone https://github.com/Unity-Technologies/ROS-TCP-Endpoint.git
cd ROS-TCP-Endpoint
# checkout a ROS2-compatible branch/tag and verify package.xml uses ament
cd ../..
colcon build --symlink-install
```

## Connection Settings (Unity)
1. Open `ROS Settings`.
2. Set:
   - `ROS IP Address`: `127.0.0.1`
   - `ROS Port`: `10000`
3. Generate message classes for `robot_msgs`.

## Required Unity Components
- `AGVController.cs` on robot base object (`mode=ROS`, subscribe `/cmd_vel`)
  - use `invertAngularZ` / `invertLinearX` if turning/forward direction is opposite
- `LaserScanSensor.cs` publishing `/scan` for Nav2/SLAM obstacle layer
- `RobotPosePublisher.cs` publishing `/unity/robot_pose` for status synchronization
- `ROSClockPublisher.cs` publishing `/clock` when `use_sim_time=true`
- `ROSTransformTreePublisher.cs` should stay disabled by default (ROS owns `odom->base_link`)

## Unity Subscription Targets
- `/robot/status` (`robot_msgs/RobotStatus`)
- `/robot/task_feedback` (`robot_msgs/action/ExecuteTask_Feedback`)
- `/robot/error_report` (`robot_msgs/ErrorReport`)
- `/robot/heartbeat` (`robot_msgs/Heartbeat`)
- `/robot/sensor_state` (`robot_msgs/SensorState`)
- `/robot/module/state` (`robot_msgs/ModuleState`)
- `/robot/pose` (`geometry_msgs/PoseStamped`)
- `/cmd_vel` (`geometry_msgs/Twist`) for AGV motion controller

## Unity Publish Targets
- `/unity/robot_pose` (`geometry_msgs/PoseStamped`) from `RobotPosePublisher.cs`
- `/scan` (`sensor_msgs/LaserScan`) from `LaserScanSensor.cs`
- `/clock` (`rosgraph_msgs/Clock`) from `ROSClockPublisher.cs`

## Unity Command Targets
- Action: `/robot/execute_task` (`robot_msgs/action/ExecuteTask`)
- Service: `/robot/cancel_task` (`robot_msgs/srv/CancelTask`)
- Service: `/robot/emergency_stop` (`robot_msgs/srv/EmergencyStop`)
- Service: `/robot/manual_control` (`robot_msgs/srv/SetManualControl`)
- Service: `/robot/module/set` (`robot_msgs/srv/SetModuleState`)
- Service: `/robot/relocalize` (`robot_msgs/srv/Relocalize`)

## Movement Mismatch Note
- `robot_nav` uses Nav2 `/navigate_to_pose`; Nav2 controller output is sent directly to `/cmd_vel`.
- `status.pose_*` is synchronized from Unity measured pose when `/unity/robot_pose` is available.
- If Unity object does not move, verify `AGVController.cs` subscribes to `/cmd_vel`.
