$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

Write-Host "[start_all] Starting ROS2 runtime container..."
docker compose up --build ros2-run
