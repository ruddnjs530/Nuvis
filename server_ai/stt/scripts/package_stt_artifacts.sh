#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_AI_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_DIR="$(cd "${SERVER_AI_DIR}/.." && pwd)"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUTPUT_BASE="${1:-${SERVER_AI_DIR}/stt/artifacts}"
STAGING_DIR="${OUTPUT_BASE}/stt_backup_${TIMESTAMP}"
ARCHIVE_PATH="${OUTPUT_BASE}/stt_backup_${TIMESTAMP}.tar.gz"

MODEL_DIR="${SERVER_AI_DIR}/stt/model/v2_full"
METADATA_PATH="${SERVER_AI_DIR}/stt/data/processed/metadata.csv"
TRAIN_LOG_PATH="${SERVER_AI_DIR}/stt_train.log"
BENCHMARK_DOC_PATH="${SERVER_AI_DIR}/docs/shared/stt_benchmark_results.md"
OPS_GUIDE_PATH="${SERVER_AI_DIR}/docs/shared/stt_training_operations_guide.md"

mkdir -p "${OUTPUT_BASE}"
rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}/model" "${STAGING_DIR}/docs" "${STAGING_DIR}/data"

if [[ ! -d "${MODEL_DIR}" ]]; then
  echo "Model directory not found: ${MODEL_DIR}" >&2
  exit 1
fi

cp -R "${MODEL_DIR}" "${STAGING_DIR}/model/"

if [[ -f "${METADATA_PATH}" ]]; then
  cp "${METADATA_PATH}" "${STAGING_DIR}/data/"
fi

if [[ -f "${TRAIN_LOG_PATH}" ]]; then
  cp "${TRAIN_LOG_PATH}" "${STAGING_DIR}/"
fi

if [[ -f "${BENCHMARK_DOC_PATH}" ]]; then
  cp "${BENCHMARK_DOC_PATH}" "${STAGING_DIR}/docs/"
fi

if [[ -f "${OPS_GUIDE_PATH}" ]]; then
  cp "${OPS_GUIDE_PATH}" "${STAGING_DIR}/docs/"
fi

{
  echo "timestamp=${TIMESTAMP}"
  echo "server_ai_dir=${SERVER_AI_DIR}"
  echo "model_dir=stt/model/v2_full"
  echo "metadata_path=stt/data/processed/metadata.csv"
  echo "train_log_path=stt_train.log"
  echo "benchmark_doc=docs/shared/stt_benchmark_results.md"
  echo "ops_guide=docs/shared/stt_training_operations_guide.md"
  echo "git_branch=$(git -C "${REPO_DIR}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
  echo "git_commit=$(git -C "${REPO_DIR}" rev-parse HEAD 2>/dev/null || echo unknown)"
} > "${STAGING_DIR}/manifest.txt"

tar -czf "${ARCHIVE_PATH}" -C "${OUTPUT_BASE}" "$(basename "${STAGING_DIR}")"

echo "Backup package created: ${ARCHIVE_PATH}"
echo "Staging directory: ${STAGING_DIR}"
