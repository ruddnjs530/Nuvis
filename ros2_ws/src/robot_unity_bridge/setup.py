from setuptools import setup

package_name = "robot_unity_bridge"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", ["launch/unity_bridge.launch.py"]),
        (f"share/{package_name}/config", ["config/unity_bridge.yaml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="B110 Robot Team",
    maintainer_email="team@example.com",
    description="UDP bridge between ROS2 robot stack and Unity simulator.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "unity_bridge_node = robot_unity_bridge.unity_bridge_node:main",
        ],
    },
)
