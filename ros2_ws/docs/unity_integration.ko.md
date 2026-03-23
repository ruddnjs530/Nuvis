# Unity 시뮬레이터 연동 가이드 (ROS-TCP)

## 1) 개요
이 프로젝트는 Unity 공식 ROS 브릿지 스택을 사용합니다.

- Unity 측: `com.unity.robotics.ros-tcp-connector`
- ROS2 측: `ROS-TCP-Endpoint` (`ros_tcp_endpoint` 패키지)

주요 흐름:

- Unity는 로봇 상태 토픽(`/robot/status`, `/robot/task_feedback`, `/robot/error_report` 등)을 구독
- Unity는 ROS Service/Action(`/robot/manual_control`, `/robot/execute_task` 등)으로 제어 명령 전송
- Unity는 실측 로봇 pose(`/unity/robot_pose`)를 발행해 상태를 동기화
- ROS `unity_odom_bridge_node`는 Unity pose를 `/odom` + `odom->base_link` TF로 변환해 Nav2에 연결
- AMCL은 `/map` + `/scan`으로 `map->odom`을 추정한다 (Unity가 `odom->base_link`를 중복 발행하면 안 됨)

## 2) ROS2 런타임 요구사항
`robot_system.launch.py`는 아래 노드 기동을 시도합니다.

- `ros_tcp_endpoint/default_server_endpoint`

기본 TCP 포트:

- `10000` (`ROS_TCP_ENDPOINT_PORT`)

워크스페이스에 `ros_tcp_endpoint`가 없으면 launch는 경고를 출력하고 Unity TCP 브릿지 없이 계속 실행됩니다.

설치 예시:

```bash
cd ros2_ws/src
git clone https://github.com/Unity-Technologies/ROS-TCP-Endpoint.git
cd ROS-TCP-Endpoint
# 저장소에서 ROS2 호환 브랜치/태그로 체크아웃하고
# package.xml이 catkin이 아닌 ament 기반인지 확인
cd ../..
colcon build --symlink-install
```

## 3) Docker 포트 매핑
`docker-compose.yml`에서 다음 포트를 노출합니다.

- `50051/tcp`: gRPC gateway
- `10000/tcp`: ROS-TCP-Endpoint

## 4) Unity 연결 설정
1. Unity에서 `ROS-TCP-Connector` 패키지를 설치합니다.
2. `ROS Settings`를 엽니다.
3. 엔드포인트를 설정합니다.
   - ROS IP: `127.0.0.1` (로컬 Docker 포트포워딩 기준)
   - ROS Port: `10000`
4. Unity에서 `robot_msgs` 커스텀 메시지 코드를 생성합니다.

## 5) Unity 연동 인터페이스 계약

현재 워크스페이스의 `ros_tcp_endpoint`는 Topic/Service 등록 중심입니다.
Unity Connector 환경에서 ROS2 Action 직접 호출이 안 되면,
장시간 작업(`/robot/execute_task`)은 backend/gRPC 경유 또는 별도 Service 래퍼를 사용하세요.

### 5-1. Unity 구독 (ROS -> Unity)
| 인터페이스 | 이름 | 타입 | 용도 |
|---|---|---|---|
| Topic | `/robot/status` | `robot_msgs/RobotStatus` | 통합 로봇 상태 HUD/대시보드 |
| Topic | `/robot/task_feedback` | `robot_msgs/action/ExecuteTask_Feedback` | 장시간 작업 진행률 표시 |
| Topic | `/robot/error_report` | `robot_msgs/ErrorReport` | 오류/예외 이벤트 표시 |
| Topic | `/robot/heartbeat` | `robot_msgs/Heartbeat` | 생존 상태 모니터링 |
| Topic | `/robot/sensor_state` | `robot_msgs/SensorState` | 센서 텔레메트리 |
| Topic | `/robot/module/state` | `robot_msgs/ModuleState` | 모듈 상태 변화 표시 |
| Topic | `/robot/pose` | `geometry_msgs/PoseStamped` | 로봇 위치/자세 표시 |
| Topic | `/cmd_vel` | `geometry_msgs/Twist` | Unity AGV 구동용 속도 명령 |

### 5-1-bis. Unity 발행 (Unity -> ROS)
| 인터페이스 | 이름 | 타입 | 용도 |
|---|---|---|---|
| Topic | `/unity/robot_pose` | `geometry_msgs/PoseStamped` | Unity 실측 pose를 ROS 상태와 동기화 |
| Topic | `/scan` | `sensor_msgs/LaserScan` | AMCL/코스트맵 장애물 및 위치추정 입력 |
| Topic | `/clock` | `rosgraph_msgs/Clock` | `use_sim_time=true`일 때 시뮬레이션 시간 소스 |

### 5-2. Unity 명령 전송 (Unity -> ROS)
| 인터페이스 | 이름 | 타입 | 용도 |
|---|---|---|---|
| Action | `/robot/execute_task` | `robot_msgs/action/ExecuteTask` | 작업 실행(이동/모듈/복귀) |
| Service | `/robot/cancel_task` | `robot_msgs/srv/CancelTask` | 현재 작업 취소 |
| Service | `/robot/emergency_stop` | `robot_msgs/srv/EmergencyStop` | 긴급 정지 |
| Service | `/robot/manual_control` | `robot_msgs/srv/SetManualControl` | 수동 속도 제어 |
| Service | `/robot/module/set` | `robot_msgs/srv/SetModuleState` | 모듈 on/off/세기 제어 |
| Service | `/robot/relocalize` | `robot_msgs/srv/Relocalize` | 위치추정 복구 요청 |

참고:

- MVP 기준으로 Unity 명령은 Topic이 아니라 Service/Action 경로를 사용합니다.
- 추적을 위해 각 요청의 `command_id`, `task_id`는 고유값으로 사용해야 합니다.

### 5-3. 트러블슈팅: status는 바뀌는데 Unity 로봇이 안 움직일 때
- 증상: gRPC/ROS 작업은 완료되고 `/robot/status.pose_*`는 바뀌지만 Unity 오브젝트는 정지함
- 원인: ROS 내부 내비게이션 상태만 갱신되고 Unity가 실제 모션을 적용하지 못한 상태
- 확인 체크:
  - Unity 로봇 컨트롤러가 `/cmd_vel`을 구독하는지 확인 (`AGVController.cs` 등)
  - 이동 작업 실행 중 `/cmd_vel`이 발행되는지 확인 (`ros2 topic echo /cmd_vel`)
  - Unity ROS Endpoint 연결값이 `127.0.0.1:10000`인지 확인
  - ROS-TCP 워크플로우에서는 기존 UDP 브릿지 스크립트를 비활성화
  - 목표 좌표는 ROS `map` 프레임(미터) 기준이므로 Unity 월드 원점/축 정렬이 맞지 않으면 점프/이상 이동이 발생

### 5-3-bis. 트러블슈팅: `TF_OLD_DATA`가 계속 발생할 때
- 대표 원인:
  - Unity가 `/tf`로 `odom->base_link`를 발행하고, ROS `unity_odom_bridge_node`도 같은 TF를 발행함
  - `enable_map_odom_tf:=true`와 AMCL을 동시에 켬
  - `use_sim_time=true`인데 `/clock`이 없거나 시간이 역행함
- 단일 권한 모델:
  - `map->odom`: AMCL
  - `odom->base_link`: ROS `unity_odom_bridge_node`
  - `base_link->base_scan`: launch 정적 TF
- Unity 측 규칙:
  - `ROSTransformTreePublisher`는 기본 비활성으로 유지

### 5-4. Unity/ROS 좌표 변환 파라미터
Unity 프레임 값을 ROS map 프레임으로 변환할 때 아래 파라미터를 사용합니다.
- `unity_origin_offset_x`
- `unity_origin_offset_y`
- `unity_yaw_offset_rad`
- `unity_scale`

동일 파라미터를 아래 노드에 일관되게 적용해야 합니다.
- `robot_nav/nav_adapter_node` (Unity 프레임 목표 변환)
- `robot_nav/unity_odom_bridge_node` (Unity 실측 pose -> `/odom`, TF)
- `robot_core/state_manager_node` (Unity 실측 pose -> `/robot/status.pose`)

`robot_core/state_manager_node` 기본값:
- `prefer_unity_pose=true`
- `unity_pose_timeout_sec=5.0`

### 5-5. Unity 필수 스크립트
- `AGVController.cs`: `/cmd_vel` 구독 후 실제 이동 적용
  - 회전/전진 방향이 반대로 나오면 `invertAngularZ` / `invertLinearX` 값으로 보정
- `RobotPosePublisher.cs`: `/unity/robot_pose` 발행
- `LaserScanSensor.cs`: `/scan` 발행
- `ROSClockPublisher.cs`: `/clock` 발행
- `ROSTransformTreePublisher.cs`: 기본 비활성 유지(특수 테스트 시에만 사용)

### 5-6. Nav2 기동 참고
- `robot_nav.launch.py` 기본값은 맵 모드(`use_slam:=false`)이며 아래를 사용합니다.
  - `map_yaml_file=robot_nav/maps/my_map.yaml`
  - `nav2_params_file=robot_nav/config/nav2_params.yaml`
- SLAM 모드는 `use_slam:=true`로 전환합니다.
- Launch TF 부트스트랩 옵션:
  - `enable_base_scan_tf` (`base_link -> base_scan`)
  - `enable_map_odom_tf` (`map -> odom`, AMCL 사용 시 기본 `false` 유지)
- AMCL 초기 자세 one-shot 기본 활성:
  - `initial_pose_x`, `initial_pose_y`, `initial_pose_yaw` (기본값: `0.0, 0.0, 0.0`)
  - Unity `/unity/robot_pose`가 수신되면 one-shot 초기 자세에 우선 반영
  - `enable_initial_pose_publish:=false`로 비활성 가능
- gRPC 좌표 프레임 선택:
  - 기본: `grpc_target_pose_frame:=map`
  - 외부 클라이언트 `target_x/target_y`를 Unity 좌표로 보낼 때: `grpc_target_pose_frame:=unity`

## 6) 빠른 검증
`robot_system.launch.py` 실행 후:

```bash
ros2 topic echo /robot/status
ros2 service type /robot/manual_control
ros2 action list | grep /robot/execute_task
```

이후 Unity를 `127.0.0.1:10000`에 연결해 메시지 송수신을 확인합니다.
