#!/usr/bin/env bash

# ==============================================================================
# [교육용 주석] STT 모델 배포 패키징 스크립트 (Artifact Archiver)
# ==============================================================================
# 목적: GPU 서버에서 며칠간 고생해서 파인튜닝 시킨 소중한 인공지능 모델(v2_full) 결과물과
#       관련 설정/운영 문서들을 단 하나의 압축 파일(tar.gz)로 예쁘게 묶어주는 유틸리티입니다.
#       이렇게 묶어놔야 다른 클라우드 서버로 배포하거나 포트폴리오로 제출할 때 누락이 없습니다.
# ==============================================================================

# 에러 발생 시 스크립트를 즉시 중단(e), 초기화 안된 변수 사용금지(u), 파이프라인 중간 에러도 철저히 감지(o pipefail)
set -euo pipefail

# 1. 경로 자동 탐지 (동적 절대 경로 세팅)
# 이 쉘 스크립트를 서버의 어떤 위치에서 실행하더라도 무조건 이 스크립트가 있는 현재 폴더를 기준으로 계산하게 만듭니다.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_AI_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_DIR="$(cd "${SERVER_AI_DIR}/.." && pwd)"

# 백업 파일명에 쓰일 현재 시간(예: 20260325_091530 형식)
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

# 첫 번째 인자가 없으면 기본값으로 artifacts 폴더를 씁니다. (${1:-기본값} 문법)
OUTPUT_BASE="${1:-${SERVER_AI_DIR}/stt/artifacts}"
STAGING_DIR="${OUTPUT_BASE}/stt_backup_${TIMESTAMP}"
ARCHIVE_PATH="${OUTPUT_BASE}/stt_backup_${TIMESTAMP}.tar.gz"

# 압축할 대상 원본들 절대 경로 매핑
MODEL_DIR="${SERVER_AI_DIR}/stt/model/v2_full"
METADATA_PATH="${SERVER_AI_DIR}/stt/data/processed/metadata.csv"
TRAIN_LOG_PATH="${SERVER_AI_DIR}/stt_train.log"
BENCHMARK_DOC_PATH="${SERVER_AI_DIR}/docs/shared/stt_benchmark_results.md"
OPS_GUIDE_PATH="${SERVER_AI_DIR}/docs/shared/stt_training_operations_guide.md"

# 최종 압축파일이 들어갈 폴더 생성 및 일회성 임시 작업 폴더(Staging Dir) 뼈대 잡기
mkdir -p "${OUTPUT_BASE}"
rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}/model" "${STAGING_DIR}/docs" "${STAGING_DIR}/data"

# 가장 중요한 AI 모델 자체가 없으면 아예 백업의 의미가 없으므로 에러 메시지 뱉고 강제 종료(Exit 1)
if [[ ! -d "${MODEL_DIR}" ]]; then
  echo "Model directory not found: ${MODEL_DIR}" >&2
  exit 1
fi

# 2. 파일 복사 모으기 (Copy to Staging)
# -R 옵션: 모델 디렉토리 하위의 수많은 가중치/설정 파일들(.safetensors, .json 등)을 통째로 재귀 복사
cp -R "${MODEL_DIR}" "${STAGING_DIR}/model/"

# 부가적인 문서나 로그파일들은 있으면(-f) 복사하고 없으면 넘어가는 유연한 구조
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

# 3. 메타데이터 (Manifest) 영수증 발행
# 나중에 압축을 풀었을 때 "어 이 모델 언제, 코드셋 어디 시점에서 구워진거지?" 추적할 수 있도록 꼬리표 증명서를 발급합니다.
{
  echo "timestamp=${TIMESTAMP}"
  echo "server_ai_dir=${SERVER_AI_DIR}"
  echo "model_dir=stt/model/v2_full"
  echo "metadata_path=stt/data/processed/metadata.csv"
  echo "train_log_path=stt_train.log"
  echo "benchmark_doc=docs/shared/stt_benchmark_results.md"
  echo "ops_guide=docs/shared/stt_training_operations_guide.md"
  # 현장 Git 레포지토리의 버전(Branch, Hash)을 다이렉트로 찍어넣어 추적성을 100% 확보합니다. (실패시 unknown)
  echo "git_branch=$(git -C "${REPO_DIR}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
  echo "git_commit=$(git -C "${REPO_DIR}" rev-parse HEAD 2>/dev/null || echo unknown)"
} > "${STAGING_DIR}/manifest.txt"

# 4. 최종 압축 패키징 (tar 묶기 + gzip 압축)
# -c (create 새로 묶기), -z (gzip 수준 압축률 뽐내기), -f (파일명 지정) 옵션 적용
tar -czf "${ARCHIVE_PATH}" -C "${OUTPUT_BASE}" "$(basename "${STAGING_DIR}")"

# 터미널에 깔끔한 결과물 안내
echo "Backup package created: ${ARCHIVE_PATH}"
echo "Staging directory: ${STAGING_DIR}"
