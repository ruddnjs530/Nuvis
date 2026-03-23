FROM osrf/ros:humble-desktop

SHELL ["/bin/bash", "-c"]

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble
ENV ROS_WS=/workspace/ros2_ws

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-colcon-common-extensions \
    python3-vcstool \
    python3-rosdep \
    python3-argcomplete \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-slam-toolbox \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir \
    "setuptools==79.0.1" \
    "packaging>=24.2" \
    "grpcio==1.78.0" \
    "protobuf==6.33.6"

RUN rosdep init 2>/dev/null || true

WORKDIR /workspace

COPY docker/ros2/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 50051 10000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
