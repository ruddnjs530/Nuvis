# robot_nav

Navigation adapter package for map-based Nav2 navigation.

## Responsibilities
- Optional zone-to-pose mapping (`waypoints.yaml`, disabled by default)
- Topology graph configuration for room navigation (`graph.yaml`, `rooms.yaml`)
- Nav2 bridge (`/robot/nav_to_goal` -> `/navigate_to_pose`)
- Return-home action endpoint (`/robot/return_home` -> `/navigate_to_pose`)
- Relocalization service endpoint (`/robot/relocalize`)
- Pose publishing (`/robot/pose`) from Nav2 feedback
- Unity pose -> odom bridge (`/unity/robot_pose` -> `/odom`, `odom->base_link` TF)
- Unity scan timestamp bridge (`/scan` -> `/scan_nav`)
- AMCL initial pose one-shot publishing (`/initialpose`)
- Unity-to-ROS coordinate conversion for incoming Unity-frame goals
- RViz `Publish Point` persistence (`/clicked_point` -> `/robot/debug/clicked_points_markers`)

## Launch
```bash
ros2 launch robot_nav robot_nav.launch.py
```

## Notes
- `robot_nav.launch.py` starts Nav2 bringup in static-map mode by default:
  - `map_yaml_file=maps/my_map.yaml`
  - `nav2_params_file=config/nav2_params.yaml`
  - `use_slam:=false`
- `waypoints_file` default is empty, so zone-based targets are disabled unless you pass a valid YAML file.
- Graph routing runs in `robot_core.task_executor_node`; `nav_adapter_node` still executes one goal at a time.
- `target_zone` is resolved through `rooms.yaml` to room entry/work graph nodes.
- `target_pose` direct requests bypass graph routing and go to Nav2 as a single goal.
- `routes.yaml` remains as ingress fallback data, not the default path model.
- `clicked_point_recorder_node` is enabled by default (`enable_clicked_point_recorder:=true`)
  and keeps clicked points visible as marker + coordinate text.
- Optional arguments:
  - `clicked_point_persist_file` (save clicked points to YAML; default disabled)
  - `clicked_point_max_points` (max retained points; default `500`)
- SLAM mode is available with `use_slam:=true`.
- Nav2 is the only motion command generator; controller output goes directly to `/cmd_vel`.
- Obstacle avoidance is handled by Nav2 local/global costmaps with `/scan_nav`.
- `unity_scan_bridge_node` rewrites Unity LaserScan timestamps to ROS sim time to avoid
  `Message Filter dropping message ... earlier than transform cache`.
- Unity-frame targets are transformed with:
  - `unity_origin_offset_x`, `unity_origin_offset_y`
  - `unity_yaw_offset_rad`
  - `unity_scale`
- TF authority model:
  - `map -> odom`: AMCL
  - `odom -> base_link`: `unity_odom_bridge_node`
  - `base_link -> base_scan`: static TF from launch
- Launch provides TF bootstrap options:
  - `enable_base_scan_tf` (`base_link -> base_scan`)
  - `enable_map_odom_tf` (`map -> odom`, disabled by default to avoid AMCL conflict)
- Scan bridge options:
  - `enable_unity_scan_bridge:=true` (default)
  - `unity_scan_topic:=/scan` (Unity raw scan input)
  - `nav_scan_topic:=/scan_nav` (Nav2 scan input topic)
- AMCL initial pose:
  - launch args: `initial_pose_x`, `initial_pose_y`, `initial_pose_yaw`
  - default values are `-8.010941721272749, 10.032504845484937, 0.01376541107`
  - if Unity `/unity/robot_pose` is available, one-shot init prefers Unity pose
  - one-shot publish can be disabled with `enable_initial_pose_publish:=false`
