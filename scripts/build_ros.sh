#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "[build_ros] Building ros2-dev image and workspace..."
docker compose run --rm ros2-dev bash -lc "cd /workspace/ros2_ws && colcon build --symlink-install --packages-select ros_tcp_endpoint robot_msgs robot_core robot_nav robot_gateway"
echo "[build_ros] Done."
