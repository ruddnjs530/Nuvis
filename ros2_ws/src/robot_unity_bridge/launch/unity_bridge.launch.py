from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    config = PathJoinSubstitution(
        [FindPackageShare("robot_unity_bridge"), "config", "unity_bridge.yaml"]
    )
    unity_host_arg = DeclareLaunchArgument(
        "unity_host",
        default_value=EnvironmentVariable("UNITY_HOST", default_value="127.0.0.1"),
    )
    unity_tx_port_arg = DeclareLaunchArgument(
        "unity_tx_port",
        default_value=EnvironmentVariable("UNITY_TX_PORT", default_value="9001"),
    )
    unity_rx_port_arg = DeclareLaunchArgument(
        "unity_rx_port",
        default_value=EnvironmentVariable("UNITY_RX_PORT", default_value="9002"),
    )

    return LaunchDescription(
        [
            unity_host_arg,
            unity_tx_port_arg,
            unity_rx_port_arg,
            Node(
                package="robot_unity_bridge",
                executable="unity_bridge_node",
                name="unity_bridge_node",
                output="screen",
                parameters=[
                    config,
                    {
                        "unity_host": LaunchConfiguration("unity_host"),
                        "unity_tx_port": LaunchConfiguration("unity_tx_port"),
                        "unity_rx_port": LaunchConfiguration("unity_rx_port"),
                    },
                ],
            )
        ]
    )
