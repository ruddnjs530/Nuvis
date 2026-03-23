# Unity Simulator Integration Guide (ROS-TCP)

## 1) Overview
This project uses Unity's official ROS bridge stack:

- Unity side: `com.unity.robotics.ros-tcp-connector`
- ROS2 side: `ROS-TCP-Endpoint` (`ros_tcp_endpoint` package)

Main flow:

- Unity subscribes to robot state topics (`/robot/status`, `/robot/task_feedback`, `/robot/error_report`, ...)
- Unity sends control requests through ROS Service/Action (`/robot/manual_control`, `/robot/execute_task`, ...)
- Unity publishes measured robot pose (`/unity/robot_pose`) for status synchronization
- ROS `unity_odom_bridge_node` converts Unity pose to `/odom` + `odom->base_link` TF for Nav2
- AMCL estimates `map->odom` from `/map` + `/scan` (Unity must not publish duplicate `odom->base_link` TF)

## 2) ROS2 Runtime Requirements
`robot_system.launch.py` attempts to start:

- `ros_tcp_endpoint/default_server_endpoint`

Default TCP port:

- `10000` (`ROS_TCP_ENDPOINT_PORT`)

If `ros_tcp_endpoint` is not present in your workspace, launch prints a warning and continues without Unity TCP bridge.

Install example:

```bash
cd ros2_ws/src
git clone https://github.com/Unity-Technologies/ROS-TCP-Endpoint.git
cd ROS-TCP-Endpoint
# checkout a ROS2-compatible branch/tag from the repository
# and verify package.xml uses ament (not catkin)
cd ../..
colcon build --symlink-install
```

## 3) Docker Port Mapping
`docker-compose.yml` exposes:

- `50051/tcp`: gRPC gateway
- `10000/tcp`: ROS-TCP-Endpoint

## 4) Unity Connection Setup
1. Install Unity package `ROS-TCP-Connector`.
2. Open `ROS Settings` in Unity.
3. Set endpoint:
   - ROS IP: `127.0.0.1` (local Docker port forwarding)
   - ROS Port: `10000`
4. Generate message classes for custom package `robot_msgs` in Unity.

## 5) Topic/Service/Action Contract for Unity

Current `ros_tcp_endpoint` in this workspace supports Topic/Service command registration.
If your Unity connector setup does not support ROS2 Action directly, trigger long tasks via backend/gRPC path
or add a ROS Service wrapper for `/robot/execute_task`.

### 5-1. Unity subscribes (ROS -> Unity)
| Interface | Name | Type | Purpose |
|---|---|---|---|
| Topic | `/robot/status` | `robot_msgs/RobotStatus` | Integrated robot state for dashboard/sim HUD |
| Topic | `/robot/task_feedback` | `robot_msgs/action/ExecuteTask_Feedback` | Long-running task progress |
| Topic | `/robot/error_report` | `robot_msgs/ErrorReport` | Error/event notification |
| Topic | `/robot/heartbeat` | `robot_msgs/Heartbeat` | Liveness monitoring |
| Topic | `/robot/sensor_state` | `robot_msgs/SensorState` | Sensor telemetry |
| Topic | `/robot/module/state` | `robot_msgs/ModuleState` | Module status changes |
| Topic | `/robot/pose` | `geometry_msgs/PoseStamped` | Robot pose update |
| Topic | `/cmd_vel` | `geometry_msgs/Twist` | Velocity command consumed by Unity AGV controller |

### 5-1-bis. Unity publishes (Unity -> ROS)
| Interface | Name | Type | Purpose |
|---|---|---|---|
| Topic | `/unity/robot_pose` | `geometry_msgs/PoseStamped` | Ground-truth pose from Unity for status synchronization |
| Topic | `/scan` | `sensor_msgs/LaserScan` | Obstacle and localization input for AMCL/costmaps |
| Topic | `/clock` | `rosgraph_msgs/Clock` | Simulation time source when `use_sim_time=true` |

### 5-2. Unity sends commands (Unity -> ROS)
| Interface | Name | Type | Purpose |
|---|---|---|---|
| Action | `/robot/execute_task` | `robot_msgs/action/ExecuteTask` | Execute mission (move/module/return) |
| Service | `/robot/cancel_task` | `robot_msgs/srv/CancelTask` | Cancel active task |
| Service | `/robot/emergency_stop` | `robot_msgs/srv/EmergencyStop` | Immediate emergency stop |
| Service | `/robot/manual_control` | `robot_msgs/srv/SetManualControl` | Manual velocity command |
| Service | `/robot/module/set` | `robot_msgs/srv/SetModuleState` | Module on/off/level |
| Service | `/robot/relocalize` | `robot_msgs/srv/Relocalize` | Recover localization |

Notes:

- MVP command path is Service/Action based; there is no Unity command topic in v1.
- Keep `command_id`/`task_id` unique per request for tracking.

### 5-3. Troubleshooting: Status changes but Unity robot does not move
- Symptom: gRPC/ROS task completes and `/robot/status.pose_*` changes, but Unity object stays still.
- Cause: ROS internal navigation state can update even when Unity is not applying motion.
- Check:
  - Unity robot controller subscribes to `/cmd_vel` (example: `AGVController.cs` in Nav2SLAMExampleProject).
  - `/cmd_vel` is emitted during move task execution (`ros2 topic echo /cmd_vel` while running `execute`).
  - Unity ROS endpoint is connected to `127.0.0.1:10000`.
  - Legacy UDP bridge scripts are disabled in ROS-TCP workflow.
  - Goal coordinates are in ROS `map` frame meters; Unity world origin/axis must be aligned (frame mismatch causes odd jumps).

### 5-3-bis. Troubleshooting: `TF_OLD_DATA` spam
- Typical causes:
  - Unity also publishes `/tf` for `odom->base_link` while ROS `unity_odom_bridge_node` already publishes it.
  - `enable_map_odom_tf:=true` is set together with AMCL map localization.
  - `/clock` is missing or non-monotonic while `use_sim_time=true`.
- Required single-authority model:
  - `map->odom`: AMCL
  - `odom->base_link`: ROS `unity_odom_bridge_node`
  - `base_link->base_scan`: static TF from launch
- Unity-side rule:
  - Keep `ROSTransformTreePublisher` disabled by default.

### 5-4. Unity/ROS coordinate transform parameters
These parameters are used when converting Unity-frame values to ROS map-frame values:
- `unity_origin_offset_x`
- `unity_origin_offset_y`
- `unity_yaw_offset_rad`
- `unity_scale`

The same transform settings should be aligned in:
- `robot_nav/nav_adapter_node` (incoming Unity-frame goals)
- `robot_nav/unity_odom_bridge_node` (Unity measured pose -> `/odom`, TF)
- `robot_core/state_manager_node` (Unity measured pose -> `/robot/status.pose`)

`robot_core/state_manager_node` defaults:
- `prefer_unity_pose=true`
- `unity_pose_timeout_sec=5.0`

### 5-5. Required Unity scripts
- `AGVController.cs`: subscribe `/cmd_vel` and apply motion.
  - if turn/forward direction is reversed, tune `invertAngularZ` / `invertLinearX`.
- `RobotPosePublisher.cs`: publish measured pose to `/unity/robot_pose`.
- `LaserScanSensor.cs`: publish `/scan`.
- `ROSClockPublisher.cs`: publish `/clock`.
- `ROSTransformTreePublisher.cs`: keep disabled unless explicitly testing TF publisher behavior.

### 5-6. Nav2 startup notes
- `robot_nav.launch.py` defaults to map mode (`use_slam:=false`) with:
  - `map_yaml_file=robot_nav/maps/my_map.yaml`
  - `nav2_params_file=robot_nav/config/nav2_params.yaml`
- Enable SLAM mode with `use_slam:=true`.
- TF bootstrap options in launch:
  - `enable_base_scan_tf` (`base_link -> base_scan`)
  - `enable_map_odom_tf` (`map -> odom`, keep `false` with AMCL)
- AMCL initial pose one-shot is enabled by default:
  - `initial_pose_x`, `initial_pose_y`, `initial_pose_yaw` (default: `0.0, 0.0, 0.0`)
  - if Unity `/unity/robot_pose` is received, one-shot init prefers Unity pose
  - disable with `enable_initial_pose_publish:=false`
- gRPC coordinate frame selection:
  - `grpc_target_pose_frame:=map` (default)
  - set `grpc_target_pose_frame:=unity` if external clients send Unity-frame `target_x/target_y`

## 6) Quick Validation
After launching `robot_system.launch.py`:

```bash
ros2 topic echo /robot/status
ros2 service type /robot/manual_control
ros2 action list | grep /robot/execute_task
```

Then connect Unity to `127.0.0.1:10000` and verify message round-trip.
