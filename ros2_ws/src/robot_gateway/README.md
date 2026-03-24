# robot_gateway

gRPC gateway package that exposes robot ROS2 controls to external clients.

## Components
- `grpc_gateway_node`: gRPC server -> ROS Action/Service bridge
- `grpc_test_client`: CLI test client for gateway RPC calls
- `proto/robot_gateway.proto`: gRPC contract

## gRPC Endpoint (default)
- `0.0.0.0:50051`

## Runtime Parameters
- `grpc_host` (default: `0.0.0.0`)
- `grpc_port` (default: `50051`)
- `target_pose_frame` (default: `map`)
  - used when execute request sends `target_x/target_y/target_yaw`
  - set `target_pose_frame:=unity` if clients provide Unity-frame coordinates

## Build
```bash
python -m pip install grpcio grpcio-tools
colcon build --packages-select robot_gateway
```

## Run
```bash
ros2 run robot_gateway grpc_gateway_node
```

## ExecuteTask Request Modes
`ExecuteTaskRequest` supports two ways to specify a navigation target.

### 1. Waypoint mode
- send a zone name in `target_zone`
- robot side resolves it through `waypoints.yaml`
- recommended for normal operation

Conditions:
- `target_zone` is not empty
- `target_x == 0.0`
- `target_y == 0.0`

Example:
```bash
python scripts/grpc_client/external_client.py --target 127.0.0.1:50051 execute \
  --command-id cmd-entrance-001 \
  --task-id task-entrance-001 \
  --task-type 1 \
  --target-zone entrance \
  --max-exec-sec 180
```

### 2. Coordinate mode
- send `target_x`, `target_y`, `target_yaw` directly
- gateway converts them into ROS `PoseStamped`
- useful for debugging or ad-hoc testing

Conditions:
- `target_zone` is empty, or
- `target_x != 0.0`, or
- `target_y != 0.0`

Example:
```bash
python scripts/grpc_client/external_client.py --target 127.0.0.1:50051 execute \
  --command-id cmd-pose-001 \
  --task-id task-pose-001 \
  --task-type 1 \
  --target-zone "" \
  --target-x -6.0 \
  --target-y 10.0 \
  --target-yaw 0.0 \
  --max-exec-sec 180
```

### Priority rule
- waypoint mode is used when only `target_zone` is set
- coordinate mode is used when `target_zone` is empty or either `target_x` or `target_y` is non-zero
- setting only `target_yaw` does not switch to coordinate mode
- to send `(0, 0)` directly, `target_zone` must be an empty string

## Registered Waypoints
- `hq`
- `entrance`
- `entrance_next_room`
- `pc`
- `tv`
- `picture`
- `kitchen`
- `first_toilet`
- `toilet_next_room`
- `left_up_room`
- `left_down_room`
- `second_toilet`

## Test Client Examples
```bash
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 status
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 execute --command-id cmd-1 --task-type 1 --target-zone hq --max-exec-sec 120
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 execute --command-id cmd-2 --task-type 1 --target-zone "" --target-x -6.0 --target-y 10.0 --target-yaw 0.0 --max-exec-sec 120
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 cancel --command-id cmd-2 --task-id task-1
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 estop --command-id cmd-3 --reason emergency
```
