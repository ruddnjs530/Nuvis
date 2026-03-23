$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

Write-Host "[check_env] Docker version"
docker --version
docker compose version

Write-Host "[check_env] Compose config validation"
docker compose config | Out-Null

if (Test-Path "ros2_ws/install/setup.bash") {
    Write-Host "[check_env] ros2_ws/install/setup.bash exists"
} else {
    Write-Host "[check_env] ros2_ws/install/setup.bash missing (run build first)"
}

Write-Host "[check_env] Done."
