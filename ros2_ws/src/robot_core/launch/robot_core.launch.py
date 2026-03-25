from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    config = PathJoinSubstitution(
        [FindPackageShare("robot_core"), "config", "robot_core.yaml"]
    )
    unity_pose_topic = LaunchConfiguration("unity_pose_topic")
    unity_origin_offset_x = LaunchConfiguration("unity_origin_offset_x")
    unity_origin_offset_y = LaunchConfiguration("unity_origin_offset_y")
    unity_yaw_offset_rad = LaunchConfiguration("unity_yaw_offset_rad")
    unity_scale = LaunchConfiguration("unity_scale")
    use_sim_time = LaunchConfiguration("use_sim_time")
    navigation_path_mode = LaunchConfiguration("navigation_path_mode")
    nav_execution_mode = LaunchConfiguration("nav_execution_mode")
    waypoints_file = LaunchConfiguration("waypoints_file")
    routes_file = LaunchConfiguration("routes_file")
    graph_file = LaunchConfiguration("graph_file")
    rooms_file = LaunchConfiguration("rooms_file")
    graph_snap_radius = LaunchConfiguration("graph_snap_radius")
    graph_stick_radius = LaunchConfiguration("graph_stick_radius")
    default_home_zone = LaunchConfiguration("default_home_zone")

    return LaunchDescription(
        [
            DeclareLaunchArgument("unity_pose_topic", default_value="/unity/robot_pose"),
            DeclareLaunchArgument("unity_origin_offset_x", default_value="0.0"),
            DeclareLaunchArgument("unity_origin_offset_y", default_value="0.0"),
            DeclareLaunchArgument("unity_yaw_offset_rad", default_value="0.0"),
            DeclareLaunchArgument("unity_scale", default_value="1.0"),
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("navigation_path_mode", default_value="graph"),
            DeclareLaunchArgument("nav_execution_mode", default_value="through_poses"),
            DeclareLaunchArgument(
                "waypoints_file",
                default_value=PathJoinSubstitution(
                    [FindPackageShare("robot_nav"), "config", "waypoints.yaml"]
                ),
            ),
            DeclareLaunchArgument(
                "routes_file",
                default_value=PathJoinSubstitution(
                    [FindPackageShare("robot_nav"), "config", "routes.yaml"]
                ),
            ),
            DeclareLaunchArgument(
                "graph_file",
                default_value=PathJoinSubstitution(
                    [FindPackageShare("robot_nav"), "config", "graph.yaml"]
                ),
            ),
            DeclareLaunchArgument(
                "rooms_file",
                default_value=PathJoinSubstitution(
                    [FindPackageShare("robot_nav"), "config", "rooms.yaml"]
                ),
            ),
            DeclareLaunchArgument("graph_snap_radius", default_value="2.5"),
            DeclareLaunchArgument("graph_stick_radius", default_value="0.8"),
            DeclareLaunchArgument("default_home_zone", default_value="hq"),
            Node(
                package="robot_core",
                executable="state_manager_node",
                name="state_manager_node",
                output="screen",
                parameters=[
                    config,
                    {
                        "unity_pose_topic": unity_pose_topic,
                        "unity_origin_offset_x": unity_origin_offset_x,
                        "unity_origin_offset_y": unity_origin_offset_y,
                        "unity_yaw_offset_rad": unity_yaw_offset_rad,
                        "unity_scale": unity_scale,
                        "use_sim_time": use_sim_time,
                    },
                ],
            ),
            Node(
                package="robot_core",
                executable="heartbeat_node",
                name="heartbeat_node",
                output="screen",
                parameters=[config, {"use_sim_time": use_sim_time}],
            ),
            Node(
                package="robot_core",
                executable="sensor_fusion_node",
                name="sensor_fusion_node",
                output="screen",
                parameters=[config, {"use_sim_time": use_sim_time}],
            ),
            Node(
                package="robot_core",
                executable="module_controller_node",
                name="module_controller_node",
                output="screen",
                parameters=[config, {"use_sim_time": use_sim_time}],
            ),
            Node(
                package="robot_core",
                executable="safety_manager_node",
                name="safety_manager_node",
                output="screen",
                parameters=[config, {"use_sim_time": use_sim_time}],
            ),
            Node(
                package="robot_core",
                executable="task_executor_node",
                name="task_executor_node",
                output="screen",
                parameters=[
                    config,
                    {
                        "use_sim_time": use_sim_time,
                        "navigation_path_mode": navigation_path_mode,
                        "nav_execution_mode": nav_execution_mode,
                        "waypoints_file": waypoints_file,
                        "routes_file": routes_file,
                        "graph_file": graph_file,
                        "rooms_file": rooms_file,
                        "graph_snap_radius": graph_snap_radius,
                        "graph_stick_radius": graph_stick_radius,
                        "default_home_zone": default_home_zone,
                    },
                ],
            ),
        ]
    )
