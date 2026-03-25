from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    core_launch = PathJoinSubstitution(
        [FindPackageShare("robot_core"), "launch", "robot_core.launch.py"]
    )
    nav_launch = PathJoinSubstitution(
        [FindPackageShare("robot_nav"), "launch", "robot_nav.launch.py"]
    )
    gateway_launch = PathJoinSubstitution(
        [FindPackageShare("robot_gateway"), "launch", "grpc_gateway.launch.py"]
    )

    actions = [
        DeclareLaunchArgument("nav_use_slam", default_value="false"),
        DeclareLaunchArgument("nav_use_sim_time", default_value="true"),
        DeclareLaunchArgument("nav_autostart", default_value="true"),
        DeclareLaunchArgument("nav_use_respawn", default_value="false"),
        DeclareLaunchArgument("nav_enable_map_odom_tf", default_value="false"),
        DeclareLaunchArgument(
            "map_yaml_file",
            default_value=PathJoinSubstitution(
                [FindPackageShare("robot_nav"), "maps", "my_map.yaml"]
            ),
        ),
        DeclareLaunchArgument(
            "nav2_params_file",
            default_value=PathJoinSubstitution(
                [FindPackageShare("robot_nav"), "config", "nav2_params.yaml"]
            ),
        ),
        DeclareLaunchArgument(
            "nav_waypoints_file",
            default_value=PathJoinSubstitution(
                [FindPackageShare("robot_nav"), "config", "waypoints.yaml"]
            ),
        ),
        DeclareLaunchArgument(
            "nav_routes_file",
            default_value=PathJoinSubstitution(
                [FindPackageShare("robot_nav"), "config", "routes.yaml"]
            ),
        ),
        DeclareLaunchArgument(
            "nav_graph_file",
            default_value=PathJoinSubstitution(
                [FindPackageShare("robot_nav"), "config", "graph.yaml"]
            ),
        ),
        DeclareLaunchArgument(
            "nav_rooms_file",
            default_value=PathJoinSubstitution(
                [FindPackageShare("robot_nav"), "config", "rooms.yaml"]
            ),
        ),
        DeclareLaunchArgument("nav_path_mode", default_value="graph"),
        DeclareLaunchArgument("nav_execution_mode", default_value="through_poses"),
        DeclareLaunchArgument("nav_graph_snap_radius", default_value="2.5"),
        DeclareLaunchArgument("nav_graph_stick_radius", default_value="0.8"),
        DeclareLaunchArgument("nav_default_home_zone", default_value="hq"),
        DeclareLaunchArgument("unity_odom_publish_tf", default_value="true"),
        DeclareLaunchArgument("unity_pose_topic", default_value="/unity/robot_pose"),
        DeclareLaunchArgument("unity_scan_topic", default_value="/scan"),
        DeclareLaunchArgument("nav_scan_topic", default_value="/scan_nav"),
        DeclareLaunchArgument("enable_unity_scan_bridge", default_value="true"),
        DeclareLaunchArgument("nav_scan_frame", default_value="base_scan"),
        DeclareLaunchArgument("unity_origin_offset_x", default_value="0.0"),
        DeclareLaunchArgument("unity_origin_offset_y", default_value="0.0"),
        DeclareLaunchArgument("unity_yaw_offset_rad", default_value="0.0"),
        DeclareLaunchArgument("unity_scale", default_value="1.0"),
        DeclareLaunchArgument("initial_pose_x", default_value="-8.010941721272749"),
        DeclareLaunchArgument("initial_pose_y", default_value="10.032504845484937"),
        DeclareLaunchArgument("initial_pose_yaw", default_value="0.01376541107"),
        DeclareLaunchArgument("initial_pose_frame", default_value="map"),
        DeclareLaunchArgument("initial_pose_delay_sec", default_value="2.0"),
        DeclareLaunchArgument("enable_initial_pose_publish", default_value="true"),
        DeclareLaunchArgument("grpc_target_pose_frame", default_value="map"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(core_launch),
            launch_arguments={
                "use_sim_time": LaunchConfiguration("nav_use_sim_time"),
                "unity_pose_topic": LaunchConfiguration("unity_pose_topic"),
                "unity_origin_offset_x": LaunchConfiguration("unity_origin_offset_x"),
                "unity_origin_offset_y": LaunchConfiguration("unity_origin_offset_y"),
                "unity_yaw_offset_rad": LaunchConfiguration("unity_yaw_offset_rad"),
                "unity_scale": LaunchConfiguration("unity_scale"),
                "navigation_path_mode": LaunchConfiguration("nav_path_mode"),
                "nav_execution_mode": LaunchConfiguration("nav_execution_mode"),
                "waypoints_file": LaunchConfiguration("nav_waypoints_file"),
                "routes_file": LaunchConfiguration("nav_routes_file"),
                "graph_file": LaunchConfiguration("nav_graph_file"),
                "rooms_file": LaunchConfiguration("nav_rooms_file"),
                "graph_snap_radius": LaunchConfiguration("nav_graph_snap_radius"),
                "graph_stick_radius": LaunchConfiguration("nav_graph_stick_radius"),
                "default_home_zone": LaunchConfiguration("nav_default_home_zone"),
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav_launch),
            launch_arguments={
                "use_slam": LaunchConfiguration("nav_use_slam"),
                "use_sim_time": LaunchConfiguration("nav_use_sim_time"),
                "autostart": LaunchConfiguration("nav_autostart"),
                "use_respawn": LaunchConfiguration("nav_use_respawn"),
                "map_yaml_file": LaunchConfiguration("map_yaml_file"),
                "nav2_params_file": LaunchConfiguration("nav2_params_file"),
                "waypoints_file": LaunchConfiguration("nav_waypoints_file"),
                "enable_map_odom_tf": LaunchConfiguration("nav_enable_map_odom_tf"),
                "unity_odom_publish_tf": LaunchConfiguration("unity_odom_publish_tf"),
                "unity_pose_topic": LaunchConfiguration("unity_pose_topic"),
                "unity_scan_topic": LaunchConfiguration("unity_scan_topic"),
                "nav_scan_topic": LaunchConfiguration("nav_scan_topic"),
                "enable_unity_scan_bridge": LaunchConfiguration("enable_unity_scan_bridge"),
                "nav_scan_frame": LaunchConfiguration("nav_scan_frame"),
                "unity_origin_offset_x": LaunchConfiguration("unity_origin_offset_x"),
                "unity_origin_offset_y": LaunchConfiguration("unity_origin_offset_y"),
                "unity_yaw_offset_rad": LaunchConfiguration("unity_yaw_offset_rad"),
                "unity_scale": LaunchConfiguration("unity_scale"),
                "initial_pose_x": LaunchConfiguration("initial_pose_x"),
                "initial_pose_y": LaunchConfiguration("initial_pose_y"),
                "initial_pose_yaw": LaunchConfiguration("initial_pose_yaw"),
                "initial_pose_frame": LaunchConfiguration("initial_pose_frame"),
                "initial_pose_delay_sec": LaunchConfiguration("initial_pose_delay_sec"),
                "enable_initial_pose_publish": LaunchConfiguration(
                    "enable_initial_pose_publish"
                ),
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gateway_launch),
            launch_arguments={
                "target_pose_frame": LaunchConfiguration("grpc_target_pose_frame"),
            }.items(),
        ),
        DeclareLaunchArgument("enable_ros_tcp_endpoint", default_value="true"),
        DeclareLaunchArgument(
            "ros_tcp_port",
            default_value=EnvironmentVariable("ROS_TCP_ENDPOINT_PORT", default_value="10000"),
        ),
    ]

    try:
        get_package_share_directory("ros_tcp_endpoint")
        actions.append(
            Node(
                package="ros_tcp_endpoint",
                executable="default_server_endpoint",
                name="ros_tcp_endpoint",
                output="screen",
                parameters=[{"ROS_TCP_PORT": LaunchConfiguration("ros_tcp_port")}],
                condition=IfCondition(LaunchConfiguration("enable_ros_tcp_endpoint")),
            )
        )
    except PackageNotFoundError:
        actions.append(
            LogInfo(
                msg=(
                    "[robot_system.launch] ros_tcp_endpoint package not found. "
                    "Install Unity ROS-TCP-Endpoint in ros2_ws/src to enable Unity TCP bridge."
                )
            )
        )

    return LaunchDescription(actions)
