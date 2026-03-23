#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "[check_env] Docker version"
docker --version
docker compose version

echo "[check_env] Compose config validation"
docker compose config >/dev/null

if [ -f "ros2_ws/install/setup.bash" ]; then
  echo "[check_env] ros2_ws/install/setup.bash exists"
else
  echo "[check_env] ros2_ws/install/setup.bash missing (run build first)"
fi

echo "[check_env] Done."
