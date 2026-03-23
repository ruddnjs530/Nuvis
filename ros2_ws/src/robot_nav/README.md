# robot_nav

Navigation adapter package for map-based Nav2 navigation.

## Responsibilities
- Optional zone-to-pose mapping (`waypoints.yaml`, disabled by default)
- Nav2 bridge (`/robot/nav_to_goal` -> `/navigate_to_pose`)
- Return-home action endpoint (`/robot/return_home` -> `/navigate_to_pose`)
- Relocalization service endpoint (`/robot/relocalize`)
- Pose publishing (`/robot/pose`) from Nav2 feedback
- Unity pose -> odom bridge (`/unity/robot_pose` -> `/odom`, `odom->base_link` TF)
- AMCL initial pose one-shot publishing (`/initialpose`)
- Unity-to-ROS coordinate conversion for incoming Unity-frame goals

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
- SLAM mode is available with `use_slam:=true`.
- Nav2 is the only motion command generator; controller output goes directly to `/cmd_vel`.
- Obstacle avoidance is handled by Nav2 local/global costmaps with `/scan`.
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
- AMCL initial pose:
  - launch args: `initial_pose_x`, `initial_pose_y`, `initial_pose_yaw`
  - default values are `-8.010941721272749, 10.032504845484937, 0.01376541107`
  - if Unity `/unity/robot_pose` is available, one-shot init prefers Unity pose
  - one-shot publish can be disabled with `enable_initial_pose_publish:=false`
