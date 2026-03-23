from setuptools import setup

package_name = "robot_core"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (
            f"share/{package_name}/launch",
            ["launch/robot_core.launch.py", "launch/robot_system.launch.py"],
        ),
        (f"share/{package_name}/config", ["config/robot_core.yaml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="B110 Robot Team",
    maintainer_email="team@example.com",
    description="Core ROS2 robot control package for status, task, sensor, and safety handling.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "state_manager_node = robot_core.state_manager_node:main",
            "heartbeat_node = robot_core.heartbeat_node:main",
            "sensor_fusion_node = robot_core.sensor_fusion_node:main",
            "module_controller_node = robot_core.module_controller_node:main",
            "safety_manager_node = robot_core.safety_manager_node:main",
            "task_executor_node = robot_core.task_executor_node:main",
        ],
    },
)
