from setuptools import setup

package_name = "robot_gateway"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/proto", ["proto/robot_gateway.proto"]),
        (f"share/{package_name}/launch", ["launch/grpc_gateway.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="B110 Robot Team",
    maintainer_email="team@example.com",
    description="gRPC gateway node and test client for robot control",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "grpc_gateway_node = robot_gateway.grpc_gateway_node:main",
            "grpc_test_client = robot_gateway.grpc_test_client:main",
        ],
    },
)
