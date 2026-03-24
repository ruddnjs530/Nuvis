from setuptools import setup

package_name = "robot_nav"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", ["launch/robot_nav.launch.py"]),
        (
            f"share/{package_name}/config",
            ["config/waypoints.yaml", "config/nav2_params.yaml"],
        ),
        (f"share/{package_name}/maps", ["maps/my_map.yaml", "maps/my_map.pgm"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="B110 Robot Team",
    maintainer_email="team@example.com",
    description="Navigation adapter and waypoint manager for robot control MVP.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "nav_adapter_node = robot_nav.nav_adapter_node:main",
            "unity_odom_bridge_node = robot_nav.unity_odom_bridge_node:main",
            "unity_scan_bridge_node = robot_nav.unity_scan_bridge_node:main",
            "initial_pose_publisher_node = robot_nav.initial_pose_publisher_node:main",
        ],
    },
)
