from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    robot_nav_share = Path(get_package_share_directory("robot_nav"))
    nav2_bringup_share = Path(get_package_share_directory("nav2_bringup"))

    waypoints_file_default = str(robot_nav_share / "config" / "waypoints.yaml")
    map_file_default = str(robot_nav_share / "maps" / "my_map.yaml")
    nav2_params_default = str(robot_nav_share / "config" / "nav2_params.yaml")
    nav2_bringup_launch = str(nav2_bringup_share / "launch" / "bringup_launch.py")

    use_slam = LaunchConfiguration("use_slam")
    use_sim_time = LaunchConfiguration("use_sim_time")
    autostart = LaunchConfiguration("autostart")
    use_respawn = LaunchConfiguration("use_respawn")
    nav2_params_file = LaunchConfiguration("nav2_params_file")
    map_yaml_file = LaunchConfiguration("map_yaml_file")
    waypoints_file = LaunchConfiguration("waypoints_file")

    enable_unity_odom_bridge = LaunchConfiguration("enable_unity_odom_bridge")
    enable_base_scan_tf = LaunchConfiguration("enable_base_scan_tf")
    enable_map_odom_tf = LaunchConfiguration("enable_map_odom_tf")
    unity_odom_publish_tf = LaunchConfiguration("unity_odom_publish_tf")
    unity_pose_topic = LaunchConfiguration("unity_pose_topic")
    unity_scan_topic = LaunchConfiguration("unity_scan_topic")
    nav_scan_topic = LaunchConfiguration("nav_scan_topic")
    enable_unity_scan_bridge = LaunchConfiguration("enable_unity_scan_bridge")
    nav_scan_frame = LaunchConfiguration("nav_scan_frame")
    nav_progress_delta_m = LaunchConfiguration("nav_progress_delta_m")
    nav_progress_stall_timeout_sec = LaunchConfiguration("nav_progress_stall_timeout_sec")
    nav_hard_timeout_multiplier = LaunchConfiguration("nav_hard_timeout_multiplier")
    nav_hard_timeout_min_extra_sec = LaunchConfiguration("nav_hard_timeout_min_extra_sec")
    unity_origin_offset_x = LaunchConfiguration("unity_origin_offset_x")
    unity_origin_offset_y = LaunchConfiguration("unity_origin_offset_y")
    unity_yaw_offset_rad = LaunchConfiguration("unity_yaw_offset_rad")
    unity_scale = LaunchConfiguration("unity_scale")
    enable_clicked_point_recorder = LaunchConfiguration("enable_clicked_point_recorder")
    clicked_point_topic = LaunchConfiguration("clicked_point_topic")
    clicked_point_marker_topic = LaunchConfiguration("clicked_point_marker_topic")
    clicked_point_pose_array_topic = LaunchConfiguration("clicked_point_pose_array_topic")
    clicked_point_persist_file = LaunchConfiguration("clicked_point_persist_file")
    clicked_point_max_points = LaunchConfiguration("clicked_point_max_points")

    enable_initial_pose_publish = LaunchConfiguration("enable_initial_pose_publish")
    initial_pose_x = LaunchConfiguration("initial_pose_x")
    initial_pose_y = LaunchConfiguration("initial_pose_y")
    initial_pose_yaw = LaunchConfiguration("initial_pose_yaw")
    initial_pose_frame = LaunchConfiguration("initial_pose_frame")
    initial_pose_delay_sec = LaunchConfiguration("initial_pose_delay_sec")

    slam_arg = PythonExpression(
        ["'True' if '", use_slam, "'.lower() in ['1','true','yes','on'] else 'False'"]
    )
    sim_time_arg = PythonExpression(
        ["'True' if '", use_sim_time, "'.lower() in ['1','true','yes','on'] else 'False'"]
    )
    autostart_arg = PythonExpression(
        ["'True' if '", autostart, "'.lower() in ['1','true','yes','on'] else 'False'"]
    )
    respawn_arg = PythonExpression(
        ["'True' if '", use_respawn, "'.lower() in ['1','true','yes','on'] else 'False'"]
    )
    initial_pose_condition = IfCondition(
        PythonExpression(
            [
                "'true' if ('",
                enable_initial_pose_publish,
                "'.lower() in ['1','true','yes','on']) and ('",
                use_slam,
                "'.lower() not in ['1','true','yes','on']) else 'false'",
            ]
        )
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_slam", default_value="false"),
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("autostart", default_value="true"),
            DeclareLaunchArgument("use_respawn", default_value="false"),
            DeclareLaunchArgument("map_yaml_file", default_value=map_file_default),
            DeclareLaunchArgument("nav2_params_file", default_value=nav2_params_default),
            DeclareLaunchArgument("waypoints_file", default_value=waypoints_file_default),
            DeclareLaunchArgument("enable_unity_odom_bridge", default_value="true"),
            DeclareLaunchArgument("enable_base_scan_tf", default_value="true"),
            DeclareLaunchArgument("enable_map_odom_tf", default_value="false"),
            DeclareLaunchArgument("unity_odom_publish_tf", default_value="true"),
            DeclareLaunchArgument("unity_pose_topic", default_value="/unity/robot_pose"),
            DeclareLaunchArgument("unity_scan_topic", default_value="/scan"),
            DeclareLaunchArgument("nav_scan_topic", default_value="/scan_nav"),
            DeclareLaunchArgument("enable_unity_scan_bridge", default_value="true"),
            DeclareLaunchArgument("nav_scan_frame", default_value="base_scan"),
            DeclareLaunchArgument("nav_progress_delta_m", default_value="0.08"),
            DeclareLaunchArgument("nav_progress_stall_timeout_sec", default_value="15.0"),
            DeclareLaunchArgument("nav_hard_timeout_multiplier", default_value="3.0"),
            DeclareLaunchArgument("nav_hard_timeout_min_extra_sec", default_value="120.0"),
            DeclareLaunchArgument("unity_origin_offset_x", default_value="0.0"),
            DeclareLaunchArgument("unity_origin_offset_y", default_value="0.0"),
            DeclareLaunchArgument("unity_yaw_offset_rad", default_value="0.0"),
            DeclareLaunchArgument("unity_scale", default_value="1.0"),
            DeclareLaunchArgument("enable_clicked_point_recorder", default_value="true"),
            DeclareLaunchArgument("clicked_point_topic", default_value="/clicked_point"),
            DeclareLaunchArgument(
                "clicked_point_marker_topic",
                default_value="/robot/debug/clicked_points_markers",
            ),
            DeclareLaunchArgument(
                "clicked_point_pose_array_topic",
                default_value="/robot/debug/clicked_points_pose_array",
            ),
            DeclareLaunchArgument("clicked_point_persist_file", default_value=""),
            DeclareLaunchArgument("clicked_point_max_points", default_value="500"),
            DeclareLaunchArgument("enable_initial_pose_publish", default_value="true"),
            DeclareLaunchArgument("initial_pose_x", default_value="-8.010941721272749"),
            DeclareLaunchArgument("initial_pose_y", default_value="10.032504845484937"),
            DeclareLaunchArgument("initial_pose_yaw", default_value="0.01376541107"),
            DeclareLaunchArgument("initial_pose_frame", default_value="map"),
            DeclareLaunchArgument("initial_pose_delay_sec", default_value="2.0"),
            Node(
                package="robot_nav",
                executable="unity_odom_bridge_node",
                name="unity_odom_bridge_node",
                output="screen",
                condition=IfCondition(enable_unity_odom_bridge),
                parameters=[
                    {
                        "source_pose_topic": unity_pose_topic,
                        "odom_topic": "/odom",
                        "odom_frame": "odom",
                        "base_frame": "base_link",
                        "unity_origin_offset_x": unity_origin_offset_x,
                        "unity_origin_offset_y": unity_origin_offset_y,
                        "unity_yaw_offset_rad": unity_yaw_offset_rad,
                        "unity_scale": unity_scale,
                        "unity_frame_prefix": "unity",
                        "publish_tf": unity_odom_publish_tf,
                        "publish_rate_hz": 30.0,
                        "input_timeout_sec": 1.0,
                        "use_sim_time": use_sim_time,
                    }
                ],
            ),
            Node(
                package="robot_nav",
                executable="unity_scan_bridge_node",
                name="unity_scan_bridge_node",
                output="screen",
                condition=IfCondition(enable_unity_scan_bridge),
                parameters=[
                    {
                        "source_scan_topic": unity_scan_topic,
                        "output_scan_topic": nav_scan_topic,
                        "output_frame_id": nav_scan_frame,
                        "watchdog_warn_sec": 2.0,
                        "use_sim_time": use_sim_time,
                    }
                ],
            ),
            Node(
                package="tf2_ros",
                executable="static_transform_publisher",
                name="base_link_to_base_scan_tf",
                output="screen",
                condition=IfCondition(enable_base_scan_tf),
                arguments=["0", "0", "0", "0", "0", "0", "base_link", "base_scan"],
            ),
            Node(
                package="tf2_ros",
                executable="static_transform_publisher",
                name="map_to_odom_tf",
                output="screen",
                condition=IfCondition(enable_map_odom_tf),
                arguments=["0", "0", "0", "0", "0", "0", "map", "odom"],
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(nav2_bringup_launch),
                launch_arguments={
                    "slam": slam_arg,
                    "map": map_yaml_file,
                    "use_sim_time": sim_time_arg,
                    "params_file": nav2_params_file,
                    "autostart": autostart_arg,
                    "use_respawn": respawn_arg,
                    "use_composition": "False",
                }.items(),
            ),
            Node(
                package="robot_nav",
                executable="initial_pose_publisher_node",
                name="initial_pose_publisher_node",
                output="screen",
                condition=initial_pose_condition,
                parameters=[
                    {
                        "initial_pose_x": initial_pose_x,
                        "initial_pose_y": initial_pose_y,
                        "initial_pose_yaw": initial_pose_yaw,
                        "initial_pose_frame": initial_pose_frame,
                        "publish_delay_sec": initial_pose_delay_sec,
                        "use_unity_pose_if_available": False,
                        "source_pose_topic": unity_pose_topic,
                        "unity_frame_prefix": "unity",
                        "unity_origin_offset_x": unity_origin_offset_x,
                        "unity_origin_offset_y": unity_origin_offset_y,
                        "unity_yaw_offset_rad": unity_yaw_offset_rad,
                        "unity_scale": unity_scale,
                        "use_sim_time": use_sim_time,
                    }
                ],
            ),
            Node(
                package="robot_nav",
                executable="clicked_point_recorder_node",
                name="clicked_point_recorder_node",
                output="screen",
                condition=IfCondition(enable_clicked_point_recorder),
                parameters=[
                    {
                        "clicked_point_topic": clicked_point_topic,
                        "marker_topic": clicked_point_marker_topic,
                        "pose_array_topic": clicked_point_pose_array_topic,
                        "persist_file": clicked_point_persist_file,
                        "max_points": clicked_point_max_points,
                        "use_sim_time": use_sim_time,
                    }
                ],
            ),
            Node(
                package="robot_nav",
                executable="nav_adapter_node",
                name="nav_adapter_node",
                output="screen",
                parameters=[
                    {
                        "waypoints_file": waypoints_file,
                        "step_sec": 0.2,
                        "arrival_pos_tol": 0.45,
                        "arrival_yaw_tol_deg": 30.0,
                        "stable_sec": 0.5,
                        "localization_min_score": 0.4,
                        "progress_delta_m": nav_progress_delta_m,
                        "progress_stall_timeout_sec": nav_progress_stall_timeout_sec,
                        "hard_timeout_multiplier": nav_hard_timeout_multiplier,
                        "hard_timeout_min_extra_sec": nav_hard_timeout_min_extra_sec,
                        "default_home_zone": "hq",
                        "cmd_vel_topic": "/cmd_vel",
                        "unity_origin_offset_x": unity_origin_offset_x,
                        "unity_origin_offset_y": unity_origin_offset_y,
                        "unity_yaw_offset_rad": unity_yaw_offset_rad,
                        "unity_scale": unity_scale,
                        "use_sim_time": use_sim_time,
                    }
                ],
            ),
        ]
    )
