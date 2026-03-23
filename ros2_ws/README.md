# ros2_ws

ROS2 workspace for robot/control domain.

## Packages
- `robot_msgs`: interface definitions
- `robot_core`: task/state/safety/module/sensor runtime
- `robot_nav`: navigation adapter and waypoint handling
- `robot_gateway`: gRPC gateway (external <-> ROS2 bridge)

## Documents
- `docs/API.md`: integrated robot control API documentation
- `docs/docker_ros2.md`: Docker build/run guide for ROS2 workspace
- `docs/unity_integration.md`: Unity simulator ROS-TCP integration guide
- `../scripts/grpc_client/README.md`: external (non-ROS) gRPC test client guide

## Build
```bash
cd ros2_ws
colcon build --packages-select ros_tcp_endpoint robot_msgs robot_core robot_nav robot_gateway
```

## Source and Run
```bash
source install/setup.bash
ros2 launch robot_core robot_system.launch.py
```

`robot_system.launch.py` starts `ros_tcp_endpoint` automatically when the package is installed.

## Docker Quick Start
```bash
docker compose run --rm ros2-dev bash -lc "cd /workspace/ros2_ws && colcon build --symlink-install --packages-select ros_tcp_endpoint robot_msgs robot_core robot_nav robot_gateway"
docker compose up --build ros2-run
```

## Quick Checks
```bash
ros2 topic echo /robot/status
ros2 topic echo /robot/heartbeat
ros2 action send_goal /robot/execute_task robot_msgs/action/ExecuteTask "{task_id: 'task-1', command_id: 'cmd-1', task_type: 0, target_zone: 'living_room', module_type: 1, module_power: true, module_level: 2, max_exec_sec: 120}"
```
