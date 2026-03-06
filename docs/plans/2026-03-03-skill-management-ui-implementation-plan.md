# Skill Management UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task by task.

**Goal:** Deliver a first-class `/skills` management experience in MemLineage UI for OpenClaw and Codex, covering install/uninstall, health check, version/update, and enable/disable.

**Architecture:** Keep `skills/memlineage` as the single source bundle and add a backend skill-runtime layer that performs safe local filesystem operations plus limited CLI probes. Frontend calls backend APIs only (no direct shell from browser), and presents human-readable status/actions.

**Tech Stack:** FastAPI + Pydantic + SQLAlchemy runtime style (no DB schema changes required), Next.js App Router (client page), local shell/file operations via Python stdlib.

---

## Scope and Assumptions

- Scope includes exactly four capability groups:
  - Install / Uninstall / Reinstall
  - Health Check
  - Version / Update
  - Enable / Disable
- Target agents for V1: `openclaw`, `codex`.
- Deployment model for V1: MemLineage backend runs on the same machine that hosts OpenClaw/Codex skill directories.
- No DB migration required for V1 (state inferred from filesystem + probe commands).
- Non-goal: remote-host skill installation (backend machine != agent machine).

## API Contract (V1)

- `GET /api/v1/skills`
  - list status for all targets (`openclaw`, `codex`)
- `GET /api/v1/skills/{agent}`
  - detailed status for one target
- `POST /api/v1/skills/{agent}/install`
  - install or reinstall from repo `skills/memlineage`
- `DELETE /api/v1/skills/{agent}`
  - uninstall skill from target
- `POST /api/v1/skills/{agent}/enable`
  - re-enable previously disabled skill
- `POST /api/v1/skills/{agent}/disable`
  - disable skill without deleting backup
- `GET /api/v1/skills/{agent}/health`
  - runtime health probe + actionable diagnostics
- `GET /api/v1/skills/{agent}/version`
  - installed version vs bundled version + update availability
- `POST /api/v1/skills/{agent}/update`
  - apply bundled version to target (safe backup first)

## Error Codes (additive)

- `SKILL_TARGET_UNSUPPORTED`
- `SKILL_SOURCE_NOT_FOUND`
- `SKILL_NOT_INSTALLED`
- `SKILL_ALREADY_INSTALLED`
- `SKILL_ALREADY_DISABLED`
- `SKILL_ALREADY_ENABLED`
- `SKILL_CLI_NOT_FOUND`
- `SKILL_OPERATION_FAILED`

---

### Task 1: Define Backend Skill Schemas

**Files:**
- Modify: `backend/src/schemas.py`

**Step 1: Write failing test**

- Create a test assertion in `backend/tests/test_skills_api.py` (new file in Task 4) that expects strict response fields for `GET /api/v1/skills`.

**Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest -q tests/test_skills_api.py::test_list_skill_targets_schema`
Expected: FAIL (schema/route not implemented).

**Step 3: Write minimal implementation**

Add Pydantic models (strict `extra="forbid"`) for:
- target enum: `openclaw | codex`
- status snapshot: installed/enabled/paths/last_operation
- health snapshot: `ok`, `checks[]`, `warnings[]`
- version snapshot: bundled vs installed, `update_available`
- operation result envelope.

**Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest -q tests/test_skills_api.py::test_list_skill_targets_schema`
Expected: PASS.

**Step 5: Commit**

```bash
git add backend/src/schemas.py backend/tests/test_skills_api.py
git commit -m "feat(api): add skill-management response schemas"
```

---

### Task 2: Implement Skill Runtime Service (OpenClaw + Codex)

**Files:**
- Create: `backend/src/services/skill_service.py`
- Modify: `backend/src/services/__init__.py`

**Step 1: Write failing tests**

Add unit-level API tests (Task 4) that fail until service supports:
- install/uninstall
- enable/disable
- health/version/update.

**Step 2: Run tests to verify failures**

Run: `cd backend && python3 -m pytest -q tests/test_skills_api.py -k "install or disable or version or health"`
Expected: FAIL.

**Step 3: Write minimal implementation**

Implement `SkillService` with:
- source bundle path: `<repo>/skills/memlineage`
- target path resolution:
  - OpenClaw: detect workspace from `OPENCLAW_WORKSPACE_DIR`, else `~/.openclaw/openclaw.json`, else `~/.openclaw/workspace`
  - Codex: `~/.codex/skills/memlineage` (respect `CODEX_HOME` if present)
- backup strategy: timestamped rename before overwrite/uninstall
- disable strategy: move installed dir to sibling disabled location (e.g. `<target_root>/.disabled/memlineage`)
- enable strategy: restore from disabled location
- health checks:
  - common: required files in installed skill folder (`SKILL.md`, `index.js`, `lib/client.js`, `package.json`)
  - openclaw: probe `openclaw skills info memlineage --json` and `openclaw skills check --json` if CLI exists
  - codex: static checks only (no native `codex skills` subcommand)
- version checks:
  - bundled version from repo `skills/memlineage/package.json`
  - installed version from target `package.json`
  - fallback parse `SKILL.md` front matter `version`
- update: reinstall with backup when versions differ.

Safety requirements:
- never use `shell=True`
- allowlist exact CLI probes
- normalize and validate all filesystem paths
- return structured failure payload with stable error codes.

**Step 4: Run tests to verify pass**

Run: `cd backend && python3 -m pytest -q tests/test_skills_api.py -k "install or disable or version or health"`
Expected: PASS.

**Step 5: Commit**

```bash
git add backend/src/services/skill_service.py backend/src/services/__init__.py backend/tests/test_skills_api.py
git commit -m "feat(skill): add local runtime service for openclaw/codex skill lifecycle"
```

---

### Task 3: Expose Skill Management REST Endpoints

**Files:**
- Create: `backend/src/routes/skills.py`
- Modify: `backend/src/app.py`

**Step 1: Write failing test**

Add route-level tests for:
- `GET /api/v1/skills`
- `POST /api/v1/skills/codex/install`
- `POST /api/v1/skills/codex/disable`
- `POST /api/v1/skills/codex/enable`
- `GET /api/v1/skills/codex/version`
- `GET /api/v1/skills/openclaw/health`.

**Step 2: Run tests to verify failures**

Run: `cd backend && python3 -m pytest -q tests/test_skills_api.py`
Expected: FAIL (404).

**Step 3: Write minimal implementation**

- Add new router under `/api/v1/skills`.
- Convert service `ValueError(code)` to existing error-handler format (`{"code": ..., "message": ...}`).
- Include router in app startup.

**Step 4: Run tests to verify pass**

Run: `cd backend && python3 -m pytest -q tests/test_skills_api.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add backend/src/routes/skills.py backend/src/app.py backend/tests/test_skills_api.py
git commit -m "feat(api): expose skill management endpoints for openclaw and codex"
```

---

### Task 4: Add Backend Test Coverage

**Files:**
- Create: `backend/tests/test_skills_api.py`
- Modify: `backend/tests/test_agent_api_exposure.py` (only if endpoint exposure assertions exist)

**Step 1: Write tests first**

Cover:
- list/detail/status payload shape
- install/uninstall happy path
- reinstall backup behavior
- disable/enable idempotency
- version/update behavior
- health behavior when OpenClaw CLI missing (degraded warning, not crash)
- unsupported agent returns validation or `SKILL_TARGET_UNSUPPORTED`.

**Step 2: Run tests to verify failing start**

Run: `cd backend && python3 -m pytest -q tests/test_skills_api.py`
Expected: FAIL before implementation.

**Step 3: Complete implementation and fixtures**

- Use temporary directories via `tmp_path` and monkeypatch `HOME`/env.
- Avoid touching real `~/.openclaw` / `~/.codex` during tests.

**Step 4: Run full relevant backend checks**

Run:
- `cd backend && python3 -m pytest -q tests/test_skills_api.py`
- `cd backend && python3 -m pytest -q tests/test_db_config.py tests/test_auth_api.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add backend/tests/test_skills_api.py backend/tests/test_agent_api_exposure.py
git commit -m "test(api): cover skill management lifecycle endpoints"
```

---

### Task 5: Build Skills UI Page (`/skills`)

**Files:**
- Create: `frontend/app/skills/page.tsx`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/components/shell.tsx`
- Modify: `frontend/src/i18n.tsx`
- Modify: `frontend/app/globals.css`

**Step 1: Write failing frontend check**

- Add route and reference it in sidebar.
- Run build before implementation to confirm missing symbols fail.

Run: `cd frontend && npm run build`
Expected: FAIL initially.

**Step 2: Implement minimal UI**

- Add “Skills” navigation entry.
- Add `/skills` page with two target cards (`openclaw`, `codex`).
- Each card shows:
  - install status + enabled status
  - installed/bundled version + update badge
  - last health check summary
- Add action buttons:
  - install/reinstall
  - uninstall
  - enable/disable
  - health check
  - update
- Add operation log area (human-readable lines; no raw JSON by default).
- Add confirmation prompt for uninstall/disable/update.

**Step 3: API wiring**

In `frontend/src/lib/api.ts`, add typed wrappers:
- `listSkills`, `getSkillStatus`, `installSkill`, `uninstallSkill`
- `enableSkill`, `disableSkill`, `healthSkill`, `versionSkill`, `updateSkill`.

**Step 4: Run frontend checks**

Run:
- `cd frontend && npm run build`
Expected: PASS.

**Step 5: Commit**

```bash
git add frontend/app/skills/page.tsx frontend/src/lib/api.ts frontend/src/components/shell.tsx frontend/src/i18n.tsx frontend/app/globals.css
git commit -m "feat(ui): add skill management page for openclaw and codex"
```

---

### Task 6: Codex Install/Uninstall Script Parity (Optional but Recommended)

**Files:**
- Create: `scripts/install_codex_memlineage_skill.sh`
- Create: `scripts/uninstall_codex_memlineage_skill.sh`

**Step 1: Write shell check first**

Run: `bash -n scripts/install_codex_memlineage_skill.sh scripts/uninstall_codex_memlineage_skill.sh`
Expected: FAIL before files exist.

**Step 2: Implement scripts**

- Install script:
  - detect `CODEX_HOME` else `~/.codex`
  - backup existing `skills/memlineage`
  - copy bundle from repo
  - print deterministic output lines for backend parser reuse.
- Uninstall script:
  - remove target skill dir
  - optionally prune old local backups by retention count.

**Step 3: Run shell validation**

Run: `bash -n scripts/install_codex_memlineage_skill.sh scripts/uninstall_codex_memlineage_skill.sh`
Expected: PASS.

**Step 4: Smoke test locally**

Run:
- `bash scripts/install_codex_memlineage_skill.sh`
- `bash scripts/uninstall_codex_memlineage_skill.sh`
Expected: directory installed then removed.

**Step 5: Commit**

```bash
git add scripts/install_codex_memlineage_skill.sh scripts/uninstall_codex_memlineage_skill.sh
git commit -m "chore(skill): add codex install/uninstall helper scripts"
```

---

### Task 7: Documentation Sync

**Files:**
- Modify: `README.md`
- Modify: `INTEGRATION.md`
- Modify: `docs/README.md`

**Step 1: Write doc diff goals**

Ensure docs clearly state:
- new `/skills` page
- same-machine requirement for UI-managed install
- OpenClaw/Codex differences (Codex has no native skills subcommand).

**Step 2: Update docs**

Add concise operational steps and troubleshooting table.

**Step 3: Verify links and consistency**

Run:
- `rg -n "skills page|/skills|install|disable|update" README.md INTEGRATION.md docs/README.md`
Expected: consistent wording and no stale references.

**Step 4: Commit**

```bash
git add README.md INTEGRATION.md docs/README.md
git commit -m "docs: document UI-based skill lifecycle management"
```

---

## Final Verification Checklist

Run in order:

```bash
cd backend && python3 -m pytest -q tests/test_skills_api.py
cd backend && python3 -m pytest -q
cd frontend && npm run build
```

Manual smoke:
- Open UI `/skills`
- Test Codex: install -> disable -> enable -> check health -> update -> uninstall
- Test OpenClaw: install -> `openclaw skills info memlineage --json` -> disable -> enable -> uninstall

Expected:
- No destructive operations outside configured target roots
- Each action returns stable JSON envelope
- UI shows natural-language status and next-step hints

---

## Implementation Risks and Mitigations

- Risk: backend host differs from agent host
  - Mitigation: surface explicit warning in `/skills` page and health check (`local-host-only`).
- Risk: OpenClaw CLI unavailable in runtime PATH
  - Mitigation: health degrades with `SKILL_CLI_NOT_FOUND` warning, keep filesystem checks functional.
- Risk: accidental deletion outside target directory
  - Mitigation: canonical path checks + target-root allowlist before any remove/move.
- Risk: concurrent operations on same target
  - Mitigation: per-target lock file or process mutex around install/update/disable/uninstall.

---

Plan complete and saved to `docs/plans/2026-03-03-skill-management-ui-implementation-plan.md`. Two execution options:

**1. Subagent-Driven (this session)** - task-by-task implementation with checkpoints and quick feedback.

**2. Parallel Session (separate)** - execute in a fresh session strictly following this plan.

