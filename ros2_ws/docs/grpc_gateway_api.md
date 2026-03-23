# gRPC Gateway API (MVP v0.1.0)

## Endpoint
- Default: `0.0.0.0:50051`
- Service: `robot.gateway.v1.RobotGateway`

## RPCs
|RPC|Request|Response|ROS Bridge|
|---|---|---|---|
|`ExecuteTask`|`ExecuteTaskRequest`|`ExecuteTaskResponse`|`/robot/execute_task` (Action)|
|`CancelTask`|`CancelTaskRequest`|`CancelTaskResponse`|`/robot/cancel_task` (Service)|
|`EmergencyStop`|`EmergencyStopRequest`|`EmergencyStopResponse`|`/robot/emergency_stop` (Service)|
|`ManualControl`|`ManualControlRequest`|`ManualControlResponse`|`/robot/manual_control` (Service)|
|`GetStatus`|`GetStatusRequest`|`RobotStatusResponse`|`/robot/status` (Topic cache)|
|`StreamStatus`|`StreamStatusRequest`|`stream RobotStatusResponse`|`/robot/status` (Topic stream)|

## Notes
- `ExecuteTask` waits for action result and returns final state.
- `StreamStatus.interval_ms` range is clamped to `100..10000`.
- If ROS service/action is unavailable, RPC returns `accepted=false` with error message.

## Test Client Commands (ROS package)
```bash
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 status
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 watch --interval-ms 500 --count 5
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 execute --command-id cmd-1 --task-type 0 --target-zone living_room --module-type 1 --module-power --module-level 2 --max-exec-sec 120
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 cancel --command-id cmd-2 --task-id task-1
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 estop --command-id cmd-3 --reason emergency
ros2 run robot_gateway grpc_test_client --target 127.0.0.1:50051 manual --command-id cmd-4 --vx 0.2 --wz 0.0 --duration-ms 1500
```

## Test Client Commands (External, no ROS2 dependency)
```bash
cd scripts/grpc_client
python -m pip install -r requirements.txt

python external_client_gui.py --target 127.0.0.1:50051

python external_client.py --target 127.0.0.1:50051 status
python external_client.py --target 127.0.0.1:50051 watch --interval-ms 500 --count 5
python external_client.py --target 127.0.0.1:50051 execute --command-id cmd-1 --task-type 0 --target-zone living_room --module-type 1 --module-power --module-level 2 --max-exec-sec 120
python external_client.py --target 127.0.0.1:50051 cancel --command-id cmd-2 --task-id task-1
python external_client.py --target 127.0.0.1:50051 estop --command-id cmd-3 --reason emergency
python external_client.py --target 127.0.0.1:50051 manual --command-id cmd-4 --vx 0.2 --wz 0.0 --duration-ms 1500
```
