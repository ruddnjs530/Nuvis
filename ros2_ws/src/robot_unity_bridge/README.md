# robot_unity_bridge

UDP JSON bridge between ROS2 robot runtime and Unity simulator.

## Direction
- ROS2 -> Unity: robot status/sensor/heartbeat/error/module/task feedback events
- Unity -> ROS2: execute task / cancel / emergency stop / manual control commands

## Default UDP Ports
- ROS2 to Unity (`unity_tx_port`): `9001`
- Unity to ROS2 (`unity_rx_port`): `9002`

## Run
```bash
ros2 run robot_unity_bridge unity_bridge_node
```

## Command Format (Unity -> ROS2)
```json
{
  "type": "execute_task",
  "data": {
    "command_id": "unity-cmd-1",
    "task_id": "unity-task-1",
    "task_type": 0,
    "target_zone": "living_room",
    "module_type": 1,
    "module_power": true,
    "module_level": 2,
    "max_exec_sec": 120
  }
}
```
