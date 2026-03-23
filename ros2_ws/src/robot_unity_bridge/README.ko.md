# robot_unity_bridge

ROS2 로봇 런타임과 Unity 시뮬레이터를 연결하는 UDP JSON 브릿지 패키지입니다.

## 통신 방향
- ROS2 -> Unity: 상태/센서/하트비트/오류/모듈/작업 피드백 이벤트 전송
- Unity -> ROS2: 작업 실행/취소/긴급정지/수동 제어 명령 전송

## 기본 UDP 포트
- ROS2 -> Unity (`unity_tx_port`): `9001`
- Unity -> ROS2 (`unity_rx_port`): `9002`

## 실행
```bash
ros2 run robot_unity_bridge unity_bridge_node
```

## 명령 포맷 예시 (Unity -> ROS2)
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
