# OpenClaw Skill Environment Guidance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make OpenClaw MemLineage setup self-explanatory by surfacing missing gateway environment configuration in health checks and documentation.

**Architecture:** Keep the install flow non-destructive: install scripts continue to copy the skill bundle only, while backend health checks diagnose the most common failure mode for OpenClaw (`launchd` gateway missing `KMS_*` env). Documentation becomes the source of truth for how to wire environment variables into the OpenClaw runtime and how to verify the result.

**Tech Stack:** Python (FastAPI service layer + pytest), Markdown docs, bash installer messaging

---

### Task 1: Add failing health-check coverage for missing OpenClaw gateway env

**Files:**
- Modify: `backend/tests/test_skills_api.py`
- Test: `backend/tests/test_skills_api.py`

**Step 1: Write the failing test**

Add a test that:
- creates an isolated `~/Library/LaunchAgents/ai.openclaw.gateway.plist`
- omits `KMS_BASE_URL` and `KMS_API_KEY` from the plist env
- mocks `openclaw skills info memlineage --json` to return `eligible=false` with missing env
- asserts `/api/v1/skills/openclaw/health` returns a warning with actionable guidance

**Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_skills_api.py -k missing_openclaw_gateway_env -q`

Expected: FAIL because health does not yet emit the warning.

### Task 2: Implement backend diagnostics for OpenClaw gateway env drift

**Files:**
- Modify: `backend/src/services/skill_service.py`
- Test: `backend/tests/test_skills_api.py`

**Step 1: Add minimal implementation**

Implement helper logic that:
- parses `openclaw skills info memlineage --json`
- detects missing `KMS_BASE_URL` / `KMS_API_KEY`
- inspects `~/Library/LaunchAgents/ai.openclaw.gateway.plist` when present
- emits a specific warning when the launch agent exists but its environment does not define the required keys

**Step 2: Re-run focused test**

Run: `cd backend && python3 -m pytest tests/test_skills_api.py -k missing_openclaw_gateway_env -q`

Expected: PASS

**Step 3: Run broader health/skills coverage**

Run: `cd backend && python3 -m pytest tests/test_skills_api.py -q`

Expected: PASS

### Task 3: Improve OpenClaw install and troubleshooting docs

**Files:**
- Modify: `README.md`
- Modify: `INTEGRATION.md`
- Modify: `docs/reports/2026-02-24-openclaw-memlineage-setup.md`

**Step 1: Document the real OpenClaw runtime flow**

Update docs to separate:
- skill installation
- gateway runtime env configuration
- gateway restart
- verification commands (`openclaw skills info`, `openclaw skills check`)

**Step 2: Add launchd-specific guidance**

Include a concrete example for macOS users running OpenClaw via `launchd`, making it explicit that exporting vars in a shell is not enough for a background gateway service.

**Step 3: Add failure interpretation**

Document what `eligible=false` means and how to map it to missing runtime env vs. missing skill files.

### Task 4: Improve installer script messaging without writing secrets

**Files:**
- Modify: `scripts/install_openclaw_memlineage_skill.sh`

**Step 1: Update post-install output**

When OpenClaw reports the skill is discoverable but not eligible, print a short explanation that the missing requirement is usually the gateway runtime environment and point users to the docs/verification commands.

**Step 2: Verify script content only**

Run: `sed -n '1,120p' scripts/install_openclaw_memlineage_skill.sh`

Expected: messaging mentions runtime env and restart, but does not write secrets automatically.

### Task 5: Final verification

**Files:**
- Modify: `backend/src/services/skill_service.py`
- Modify: `backend/tests/test_skills_api.py`
- Modify: `README.md`
- Modify: `INTEGRATION.md`
- Modify: `docs/reports/2026-02-24-openclaw-memlineage-setup.md`
- Modify: `scripts/install_openclaw_memlineage_skill.sh`

**Step 1: Run focused backend verification**

Run: `cd backend && python3 -m pytest tests/test_skills_api.py -q`

Expected: PASS

**Step 2: Sanity-check docs references**

Run: `rg -n "KMS_BASE_URL|launchd|eligible=false|skills info memlineage|skills check" README.md INTEGRATION.md docs/reports/2026-02-24-openclaw-memlineage-setup.md scripts/install_openclaw_memlineage_skill.sh`

Expected: updated flow appears consistently across the install and troubleshooting docs.
