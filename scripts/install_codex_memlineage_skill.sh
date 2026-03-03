#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SOURCE_DIR="${REPO_ROOT}/skills/memlineage"
CODEX_HOME_DIR="${CODEX_HOME:-${HOME}/.codex}"
TARGET_ROOT="${CODEX_HOME_DIR}/skills"
TARGET_DIR="${TARGET_ROOT}/memlineage"
DISABLED_DIR="${TARGET_ROOT}/.disabled/memlineage"
BACKUP_ROOT="${CODEX_HOME_DIR}/skill-backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

if [[ ! -d "${SOURCE_DIR}" ]]; then
  echo "ERROR: source skill directory not found: ${SOURCE_DIR}" >&2
  exit 1
fi

mkdir -p "${TARGET_ROOT}"

if [[ -d "${TARGET_DIR}" ]]; then
  mkdir -p "${BACKUP_ROOT}"
  BACKUP_DIR="${BACKUP_ROOT}/memlineage.${TIMESTAMP}"
  mv "${TARGET_DIR}" "${BACKUP_DIR}"
  echo "Backed up existing memlineage skill to: ${BACKUP_DIR}"
fi

if [[ -d "${DISABLED_DIR}" ]]; then
  rm -rf "${DISABLED_DIR}"
fi

cp -R "${SOURCE_DIR}" "${TARGET_DIR}"

for rel in "SKILL.md" "index.js" "lib/client.js" "package.json"; do
  if [[ ! -f "${TARGET_DIR}/${rel}" ]]; then
    echo "ERROR: install verification failed; missing ${rel}" >&2
    exit 1
  fi
done

echo "Codex home: ${CODEX_HOME_DIR}"
echo "Installed memlineage skill to: ${TARGET_DIR}"
echo "Done."
