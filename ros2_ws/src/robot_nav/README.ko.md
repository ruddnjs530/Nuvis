# robot_nav

맵 기반 Nav2 내비게이션 어댑터 패키지입니다.

## 책임 범위
- 선택적 Zone→Pose 매핑(`waypoints.yaml`, 기본 비활성)
- 방 기반 topology graph 설정(`graph.yaml`, `rooms.yaml`)
- Nav2 브리지(`/robot/nav_to_goal` -> `/navigate_to_pose`)
- 복귀 액션 엔드포인트(`/robot/return_home` -> `/navigate_to_pose`)
- 재위치추정 서비스 엔드포인트(`/robot/relocalize`)
- Nav2 피드백 기반 Pose 발행(`/robot/pose`)
- Unity pose -> odom 브리지(`/unity/robot_pose` -> `/odom`, `odom->base_link` TF)
- Unity scan 타임스탬프 브리지(`/scan` -> `/scan_nav`)
- AMCL 초기 자세 one-shot 발행(`/initialpose`)
- Unity 프레임 목표를 ROS 맵 좌표로 변환
- RViz `Publish Point` 좌표 누적 기록(`/clicked_point` -> `/robot/debug/clicked_points_markers`)

## 실행
```bash
ros2 launch robot_nav robot_nav.launch.py
```

## 참고
- `robot_nav.launch.py` 기본은 정적 맵 모드다.
  - `map_yaml_file=maps/my_map.yaml`
  - `nav2_params_file=config/nav2_params.yaml`
  - `use_slam:=false`
- `waypoints_file` 기본값은 빈 값이므로, 유효한 YAML을 넘기지 않으면 zone 기반 목표는 비활성이다.
- graph 기반 경로 해석은 `robot_core.task_executor_node`가 담당하고, `nav_adapter_node`는 단일 goal만 처리한다.
- `target_zone`은 `rooms.yaml` 기준으로 entry/work node로 해석된다.
- 좌표 직접 요청(`target_pose`)은 graph 해석을 우회해서 단일 goal로 처리된다.
- `routes.yaml`은 ingress fallback 데이터로 남아있고, 기본 경로 모델은 아니다.
- `clicked_point_recorder_node`는 기본 활성화(`enable_clicked_point_recorder:=true`)이며,
  RViz에서 클릭한 좌표를 마커/텍스트로 누적 표시한다.
- 선택 파라미터:
  - `clicked_point_persist_file`: 파일 저장 경로(기본 비활성)
  - `clicked_point_max_points`: 최대 누적 개수(기본 500)
- SLAM 모드는 `use_slam:=true`로 전환할 수 있다.
- 속도 명령은 Nav2 controller가 직접 `/cmd_vel`로 출력한다.
- 장애물 회피는 `/scan_nav`를 입력으로 하는 Nav2 local/global costmap에서 처리한다.
- `unity_scan_bridge_node`가 Unity LaserScan 타임스탬프를 ROS sim time으로 재기록해
  `Message Filter dropping message ... earlier than transform cache` 문제를 줄인다.
- Unity 좌표 변환 파라미터:
  - `unity_origin_offset_x`, `unity_origin_offset_y`
  - `unity_yaw_offset_rad`
  - `unity_scale`
- TF 권한 모델:
  - `map -> odom`: AMCL
  - `odom -> base_link`: `unity_odom_bridge_node`
  - `base_link -> base_scan`: launch 정적 TF
- Launch에서 TF 부트스트랩 옵션 제공:
  - `enable_base_scan_tf` (`base_link -> base_scan`)
  - `enable_map_odom_tf` (`map -> odom`, AMCL 충돌 방지를 위해 기본 비활성)
- Scan 브리지 옵션:
  - `enable_unity_scan_bridge:=true` (기본)
  - `unity_scan_topic:=/scan` (Unity 원본 scan 입력)
  - `nav_scan_topic:=/scan_nav` (Nav2 scan 입력 토픽)
- AMCL 초기 자세:
  - launch 인자: `initial_pose_x`, `initial_pose_y`, `initial_pose_yaw`
  - 기본값은 `-8.010941721272749, 10.032504845484937, 0.01376541107`
  - Unity `/unity/robot_pose`가 있으면 one-shot 발행 시 해당 pose를 우선 사용
  - `enable_initial_pose_publish:=false`로 one-shot 발행 비활성 가능
