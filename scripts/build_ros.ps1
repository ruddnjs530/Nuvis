$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

Write-Host "[build_ros] Building ros2-dev image and workspace..."
docker compose run --rm ros2-dev bash -lc "cd /workspace/ros2_ws && colcon build --symlink-install --packages-select ros_tcp_endpoint robot_msgs robot_core robot_nav robot_gateway"
Write-Host "[build_ros] Done."
