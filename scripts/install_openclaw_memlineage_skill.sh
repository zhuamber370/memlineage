#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SOURCE_DIR="${REPO_ROOT}/skills/memlineage"
CONFIG_PATH="${OPENCLAW_CONFIG_PATH:-${HOME}/.openclaw/openclaw.json}"
WORKSPACE_DIR="${OPENCLAW_WORKSPACE_DIR:-}"
if [[ -z "${WORKSPACE_DIR}" && -f "${CONFIG_PATH}" ]]; then
  WORKSPACE_DIR="$(node -e 'const fs=require("fs"); try { const c=JSON.parse(fs.readFileSync(process.argv[1],"utf8")); process.stdout.write((c && c.agents && c.agents.defaults && c.agents.defaults.workspace) || ""); } catch (_) {}' "${CONFIG_PATH}")"
fi
if [[ -z "${WORKSPACE_DIR}" ]]; then
  WORKSPACE_DIR="${HOME}/.openclaw/workspace"
fi
TARGET_ROOT="${WORKSPACE_DIR}/skills"
TARGET_DIR="${TARGET_ROOT}/memlineage"
BACKUP_ROOT="${HOME}/.openclaw/skill-backups/$(basename "${WORKSPACE_DIR}")"
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

cp -R "${SOURCE_DIR}" "${TARGET_DIR}"
echo "OpenClaw workspace: ${WORKSPACE_DIR}"
echo "Installed memlineage skill to: ${TARGET_DIR}"

INFO_JSON="$(openclaw skills info memlineage --json)"
if echo "${INFO_JSON}" | rg -q '"error"\s*:\s*"not found"'; then
  echo "ERROR: memlineage skill not discoverable after install." >&2
  exit 1
fi

if echo "${INFO_JSON}" | rg -q '"eligible"\s*:\s*true'; then
  echo "Verification: memlineage skill is discoverable and eligible."
else
  echo "Verification: memlineage skill is discoverable but not eligible yet."
  echo "OpenClaw is still missing runtime env required by the skill."
  echo "Check KMS_BASE_URL and KMS_API_KEY where the OpenClaw gateway actually runs."
  echo "If OpenClaw runs as a macOS LaunchAgent/background service, update its service env and restart the gateway."
  echo "If AFKMS_REQUIRE_AUTH=false, KMS_API_KEY can be any non-empty placeholder such as dev-api-key."
  echo "Re-verify with: openclaw skills info memlineage --json && openclaw skills check --json"
  echo "Docs: README.md#openclaw-integration and docs/reports/2026-02-24-openclaw-memlineage-setup.md"
fi

echo "Done."
