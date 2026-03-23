# robot_msgs v0.1.0 인터페이스 명세

## 목적
- 백엔드, ROS 게이트웨이, 로봇 런타임, Unity 시뮬레이션이 공유하는 계약을 제공한다.
- 단일 로봇(`robot_id=R1`), 단일 활성 작업 기준의 MVP 우선 스키마를 사용한다.

## 토픽
- `/robot/status` (`robot_msgs/RobotStatus`) 2 Hz
- `/robot/heartbeat` (`robot_msgs/Heartbeat`) 1 Hz
- `/robot/sensor_state` (`robot_msgs/SensorState`) 2 Hz
- `/robot/error_report` (`robot_msgs/ErrorReport`) 이벤트 발생 시

## 액션
- `/robot/execute_task` (`robot_msgs/action/ExecuteTask`)
- `/robot/nav_to_goal` (`robot_msgs/action/NavToGoal`)
- `/robot/return_home` (`robot_msgs/action/ReturnHome`)

## 서비스
- `/robot/emergency_stop` (`robot_msgs/srv/EmergencyStop`)
- `/robot/cancel_task` (`robot_msgs/srv/CancelTask`)
- `/robot/manual_control` (`robot_msgs/srv/SetManualControl`)
- `/robot/module/set` (`robot_msgs/srv/SetModuleState`)
- `/robot/relocalize` (`robot_msgs/srv/Relocalize`)

## ID 및 추적
- `command_id`: 백엔드/게이트웨이가 생성하는 멱등 처리용 ID
- `task_id`: 상위 시스템 또는 오케스트레이터가 생성하는 실행 추적용 ID
- 상태/피드백/결과/오류 스트림에 최소 하나 이상의 ID를 포함해야 한다.

## 타임아웃 및 재시도 기본값
- Goal 수락 타임아웃: 1초
- 작업 실행 기본 타임아웃: 300초
- 이동 재시도: 복구 가능한 이동 실패에 대해 자동 1회
- 긴급 정지는 모든 액션을 선점한다.
