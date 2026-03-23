# 로봇 제어 MVP 명세 (구현 반영)

## 범위
- `robot_msgs`: 공통 Topic/Service/Action 계약
- `robot_core`: 상태/작업/안전/센서/모듈 런타임
- `robot_nav`: 웨이포인트 + 이동/복귀 액션

## 런타임 토폴로지
1. Backend/Gateway가 `/robot/execute_task` 액션을 전송한다.
2. `task_executor_node`가 검증 후 오케스트레이션을 수행한다.
3. `nav_adapter_node`가 이동/복귀 내비게이션 액션을 처리한다.
4. `module_controller_node`가 모듈 상태 요청을 수행한다.
5. `state_manager_node`가 통합 `/robot/status`를 발행한다.
6. `safety_manager_node`가 긴급정지/저전력 정책을 강제한다.
7. `heartbeat_node`가 생존 신호를 발행한다.

## 상태 머신
- `IDLE -> RECEIVED -> VALIDATING -> ACCEPTED -> MOVING -> ARRIVED -> EXECUTING_MODULE -> RETURNING -> COMPLETED`
- 실패 분기: `FAILED`, `CANCELED`, 긴급 분기: `EMERGENCY_STOPPED`

## 안전 정책 (MVP)
- 긴급 정지는 모든 작업 실행을 선점한다.
- 배터리 20%에서 경고를 발생시킨다.
- 배터리 15%에서 복귀 트리거를 발생시킨다.
- 실행 중 상태에서 취소를 허용한다.

## 실행
```bash
ros2 launch robot_core robot_system.launch.py
```

## 검증 체크리스트
- [ ] 작업 실행 요청이 검증 단계에서 수락/거절된다.
- [ ] 이동 + 모듈 흐름에서 피드백과 결과가 생성된다.
- [ ] 취소 요청 시 작업이 `CANCELED`로 전이된다.
- [ ] 긴급 정지 시 활성 실행이 중단된다.
- [ ] 저전력 경고와 복귀 요청이 발행된다.
- [ ] 상태/하트비트 토픽이 지속 발행된다.
