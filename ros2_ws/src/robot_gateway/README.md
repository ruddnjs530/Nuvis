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

## Test Client Examples
```bash
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 status
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 execute --command-id cmd-1 --task-type 0 --target-zone living_room --module-type 1 --module-power --module-level 2 --max-exec-sec 120
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 cancel --command-id cmd-2 --task-id task-1
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 estop --command-id cmd-3 --reason emergency
```
