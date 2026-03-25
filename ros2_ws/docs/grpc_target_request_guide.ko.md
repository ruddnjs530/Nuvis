# gRPC 목표 요청 가이드

이 문서는 `ExecuteTask` gRPC 요청에서 `좌표 방식`과 `웨이포인트 방식`을 어떻게 보내는지 정리한 전용 가이드입니다.

대상:
- 백엔드 연동 담당자
- 외부 테스트 클라이언트 사용자
- GUI/CLI 기반 수동 테스트 사용자

관련 구현:
- gRPC 게이트웨이: `ros2_ws/src/robot_gateway/robot_gateway/grpc_gateway_node.py`
- 내비게이션 어댑터: `ros2_ws/src/robot_nav/robot_nav/nav_adapter_node.py`
- 웨이포인트 정의: `ros2_ws/src/robot_nav/config/waypoints.yaml`

## 1. 결론
운영에서는 `웨이포인트 방식`을 우선 사용합니다.

권장 기준:
- 정해진 장소로 이동: `target_zone` 사용
- 임시 디버깅/미세 테스트: `target_x`, `target_y`, `target_yaw` 사용
- `target_zone` 요청은 내부 topology graph에 따라 여러 segment로 분해될 수 있음

## 2. ExecuteTask 주요 필드
`ExecuteTaskRequest`에서 목표 지정과 직접 관련된 필드는 아래입니다.

|필드|타입|의미|
|---|---|---|
|`command_id`|`string`|요청 고유 ID|
|`task_id`|`string`|작업 고유 ID|
|`task_type`|`enum`|작업 타입|
|`target_zone`|`string`|웨이포인트 이름|
|`target_x`|`double`|직접 좌표 X|
|`target_y`|`double`|직접 좌표 Y|
|`target_yaw`|`double`|직접 좌표 yaw(rad)|
|`max_exec_sec`|`uint32`|최대 실행 시간|

`task_type` 값:

|값|이름|의미|
|---|---|---|
|`0`|`TASK_MOVE_AND_EXECUTE`|이동 후 모듈 동작|
|`1`|`TASK_MOVE_ONLY`|이동만 수행|
|`2`|`TASK_MODULE_ONLY`|이동 없이 모듈만 수행|
|`3`|`TASK_RETURN_HOME`|복귀 작업|

## 3. 웨이포인트 방식
`target_zone`에 zone 이름을 넣어 보내는 방식입니다.

특징:
- 로봇 내부 `rooms.yaml` + `graph.yaml`을 조회해 실제 segment 좌표로 변환
- 좌표계 해석 실수를 줄일 수 있음
- 운영/백엔드 연동에서 가장 안전함
- `rooms.yaml`과 `graph.yaml`에 따라 내부적으로 여러 nav segment로 나뉘어 실행될 수 있음

사용 조건:
- `target_zone`이 비어있지 않음
- `target_x == 0.0`
- `target_y == 0.0`

CLI 예시:
```bash
python scripts/grpc_client/external_client.py --target 127.0.0.1:50051 execute \
  --command-id cmd-entrance-001 \
  --task-id task-entrance-001 \
  --task-type 1 \
  --target-zone entrance \
  --max-exec-sec 180
```

GUI 입력 기준:
- `target_zone`: 예) `entrance`
- `target_x`: `0.0`
- `target_y`: `0.0`
- `target_yaw`: `0.0`

## 4. 좌표 방식
`target_x`, `target_y`, `target_yaw`를 직접 보내는 방식입니다.

특징:
- 임시 목표점 테스트에 유용
- RViz에서 확인한 좌표를 바로 넣기 쉬움
- 좌표계(`map`, `unity`)를 잘못 이해하면 오동작 가능

사용 조건:
- `target_zone`가 빈 문자열이거나
- `target_x != 0.0` 또는 `target_y != 0.0`

CLI 예시:
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

GUI 입력 기준:
- `target_zone`: 빈 문자열
- `target_x`: 원하는 X 좌표
- `target_y`: 원하는 Y 좌표
- `target_yaw`: 원하는 yaw(rad)

## 5. 우선순위 규칙
현재 구현 기준 우선순위는 아래와 같습니다.

### 웨이포인트로 처리되는 경우
- `target_zone`이 비어있지 않음
- `target_x == 0.0`
- `target_y == 0.0`

### 좌표로 처리되는 경우
- `target_zone`가 빈 문자열
- 또는 `target_x != 0.0`
- 또는 `target_y != 0.0`

중요:
- `target_zone`를 채웠더라도 `target_x` 또는 `target_y`가 0이 아니면 좌표 방식으로 처리됩니다.
- `target_yaw`만 바꾸고 `target_x`, `target_y`가 `0.0`이면 웨이포인트 방식으로 처리됩니다.
- `(0, 0)` 좌표를 직접 보내고 싶으면 `target_zone`를 반드시 빈 문자열로 보내야 합니다.

## 6. 좌표계 기준
좌표 방식은 게이트웨이의 `target_pose_frame` 파라미터를 따릅니다.

기본값:
- `target_pose_frame = map`

의미:
- 일반적인 외부 테스트는 `map` 좌표 기준으로 보냅니다.
- Unity 좌표를 직접 보내는 특수한 구성에서는 `target_pose_frame:=unity`로 실행해야 합니다.

## 7. 현재 등록된 웨이포인트
현재 `ros2_ws/src/robot_nav/config/waypoints.yaml`에 등록된 값은 아래와 같습니다.

|이름|x|y|yaw|
|---|---:|---:|---:|
|`hq`|1.0|-4.5|0.0|
|`entrance`|-6.0|10.0|0.0|
|`entrance_next_room`|-3.8|3.6|0.0|
|`pc`|-6.3|-1.3|0.0|
|`tv`|-3.1|-1.8|0.0|
|`picture`|1.0|-2.2|0.0|
|`kitchen`|5.5|-0.6|0.0|
|`first_toilet`|-0.6|9.0|0.0|
|`toilet_next_room`|6.0|9.1|0.0|
|`left_up_room`|5.2|15.6|0.0|
|`left_down_room`|-4.8|17.8|0.0|
|`second_toilet`|0.1|19.3|0.0|

## 8. 내부 graph 해석 방식
- 외부 `target_zone`은 room/business 의미를 유지합니다.
- robot_core는 `rooms.yaml`에서 `target_zone`의 `entry/work` node를 조회합니다.
- 현재 로봇 pose를 graph node로 snap한 뒤 최단 경로를 계산합니다.
- 계산된 node path를 Nav2 segment로 순차 실행합니다.

## 9. 사용 예시 모음
### 예시 1. `entrance`로 이동
```bash
python scripts/grpc_client/external_client.py --target 127.0.0.1:50051 execute \
  --command-id cmd-entrance-001 \
  --task-id task-entrance-001 \
  --task-type 1 \
  --target-zone entrance \
  --max-exec-sec 180
```

### 예시 2. `kitchen`으로 이동
```bash
python scripts/grpc_client/external_client.py --target 127.0.0.1:50051 execute \
  --command-id cmd-kitchen-001 \
  --task-id task-kitchen-001 \
  --task-type 1 \
  --target-zone kitchen \
  --max-exec-sec 180
```

### 예시 3. 직접 좌표 `(-3.8, 3.6)`로 이동
```bash
python scripts/grpc_client/external_client.py --target 127.0.0.1:50051 execute \
  --command-id cmd-pose-003 \
  --task-id task-pose-003 \
  --task-type 1 \
  --target-zone "" \
  --target-x -3.8 \
  --target-y 3.6 \
  --target-yaw 0.0 \
  --max-exec-sec 180
```

### 예시 4. 복귀(`hq`)는 zone 기반 사용 권장
```bash
python scripts/grpc_client/external_client.py --target 127.0.0.1:50051 execute \
  --command-id cmd-return-001 \
  --task-id task-return-001 \
  --task-type 3 \
  --target-zone hq \
  --max-exec-sec 180
```

## 10. 자주 하는 실수
### 실수 1. `target_zone`와 `target_x/y`를 같이 보냄
결과:
- zone 이동이라고 생각했지만 실제로는 좌표 이동으로 처리될 수 있음

권장:
- zone 이동이면 `target_x = 0.0`, `target_y = 0.0` 유지

### 실수 2. `(0, 0)` 좌표로 보내고 싶지만 `target_zone`를 채워둠
결과:
- 웨이포인트 방식으로 처리될 수 있음

권장:
- `(0, 0)` 좌표 직지정 시 `target_zone`를 빈 문자열로 보냄

### 실수 3. GUI에서 예전 좌표가 남아 있음
결과:
- `target_zone`를 입력해도 좌표 방식이 우선 적용될 수 있음

권장:
- 웨이포인트 방식 테스트 시 `target_x/y/yaw`를 모두 `0.0`으로 초기화

### 실수 4. zone 하나를 보냈는데 중간 이동 로그가 보임
결과:
- 오류가 아니라 내부 graph 경로 분해가 적용된 정상 동작일 수 있음

권장:
- `TaskFeedback.note` 또는 ROS 로그에서 `segment n/m` 메시지를 확인

## 11. 운영 권장안
운영/백엔드 연동에서는 아래 원칙을 권장합니다.

- 정해진 장소 이동은 `target_zone`만 사용
- 좌표 방식은 디버깅/임시 테스트에만 사용
- `waypoints.yaml` 변경 시 문서와 백엔드 enum/string 목록을 같이 갱신
- `graph.yaml`/`rooms.yaml`이 바뀌면 운영 문서와 테스트 시나리오를 같이 갱신
- 클라이언트에서는 zone 입력 시 좌표 필드를 자동으로 `0.0`으로 초기화하는 것이 안전
