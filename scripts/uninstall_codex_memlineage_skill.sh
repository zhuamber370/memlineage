#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME_DIR="${CODEX_HOME:-${HOME}/.codex}"
TARGET_ROOT="${CODEX_HOME_DIR}/skills"
TARGET_DIR="${TARGET_ROOT}/memlineage"
DISABLED_DIR="${TARGET_ROOT}/.disabled/memlineage"

if [[ -d "${TARGET_DIR}" ]]; then
  rm -rf "${TARGET_DIR}"
  echo "Removed: ${TARGET_DIR}"
else
  echo "No installed memlineage skill found at: ${TARGET_DIR}"
fi

if [[ -d "${DISABLED_DIR}" ]]; then
  rm -rf "${DISABLED_DIR}"
  echo "Removed disabled snapshot: ${DISABLED_DIR}"
fi

echo "Done."
