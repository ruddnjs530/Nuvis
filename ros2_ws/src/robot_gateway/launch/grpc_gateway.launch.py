from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument("grpc_host", default_value="0.0.0.0"),
            DeclareLaunchArgument("grpc_port", default_value="50051"),
            DeclareLaunchArgument("target_pose_frame", default_value="map"),
            Node(
                package="robot_gateway",
                executable="grpc_gateway_node",
                name="grpc_gateway_node",
                output="screen",
                parameters=[
                    {
                        "grpc_host": LaunchConfiguration("grpc_host"),
                        "grpc_port": LaunchConfiguration("grpc_port"),
                        "target_pose_frame": LaunchConfiguration("target_pose_frame"),
                    }
                ],
            )
        ]
    )
