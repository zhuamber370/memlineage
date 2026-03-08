# MemLineage

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Open Issues](https://img.shields.io/github/issues/zhuamber370/memlineage)](https://github.com/zhuamber370/memlineage/issues)
[![Last Commit](https://img.shields.io/github/last-commit/zhuamber370/memlineage)](https://github.com/zhuamber370/memlineage/commits/main)

MemLineage is an **open-source control layer** for humans running agent-heavy workflows.
It works with OpenClaw, Codex, and custom agent runtimes.

When work starts to span multiple agent conversations, chat alone stops being enough.
MemLineage gives the human operator one place to keep goals, tasks, durable knowledge, governed writes, and runtime state visible outside raw chat history.

Governed writes follow a PR-like control loop:
**dry-run -> diff preview -> human approve/reject -> commit -> audit (+ undo)**.

Quick links:
- Try locally in 60 seconds: [Dry-Run Demo](#60-second-dry-run-demo)
- Run the full stack: [Quickstart (Local)](#quickstart-local)
- Integrate with OpenClaw: [OpenClaw Integration](#openclaw-integration)
- Integrate with Codex: [Codex Integration](#codex-integration)
- Build another runtime: [Runtime/API contract](docs/guides/agent-api-surface.md)
- Review safety controls: [Safe-to-Write Checklist](docs/guides/safe-to-write-checklist.md)
- Join the discussion: [GitHub Discussion #20](https://github.com/zhuamber370/memlineage/discussions/20)

## Why MemLineage

Agent-heavy workflows often break in familiar ways:

- goals and next steps disappear into chat history
- reusable knowledge and day-to-day execution drift apart
- risky writes change memory or docs without a clear review loop
- local runtime setup becomes harder to inspect once skills and installs drift

MemLineage is built to give the human operator a stable control surface outside raw conversation logs.

## What You Can Do Today

- **See the overall state on `/`**: focus tasks, recent knowledge, pending changes, and local database safety actions
- **Run day-to-day work on `/tasks` and `/knowledge`**: keep execution and durable context outside raw chat history
- **Review risky writes on `/changes`**: use dry-run, diff preview, commit / reject, undo-last, and audit-backed history
- **Manage local runtime integrations on `/skills`**: detect, install, enable, disable, update, and check health for OpenClaw and Codex
- **Self-host locally**: run the FastAPI backend and Next.js frontend with SQLite by default and PostgreSQL support

## UI Preview

> Screenshots use synthetic test data.

![Home dashboard (synthetic test data)](docs/assets/screenshots/home-dashboard.png)

![Changes UI: dry-run diff preview](docs/assets/screenshots/changes-ui-dryrun.png)

![Tasks dashboard (synthetic test data)](docs/assets/screenshots/tasks-dashboard.png)

## Who It Helps

- Solo builders and developer-operators using OpenClaw, Codex, or custom agents as part of daily work
- People who want one place to track goals, tasks, durable knowledge, runtime state, and reviewable changes
- Workflows that require human approval, audit trail, and rollback for risky agent-generated updates

## Choose Your Path

- **Want the fastest product check?** Start with the [60-Second Dry-Run Demo](#60-second-dry-run-demo)
- **Want to run the full app locally?** Follow [Quickstart (Local)](#quickstart-local)
- **Using OpenClaw today?** Go to [OpenClaw Integration](#openclaw-integration)
- **Using Codex today?** Go to [Codex Integration](#codex-integration)
- **Building another runtime?** Read the [Runtime/API contract](docs/guides/agent-api-surface.md)
- **Want real-world operator context?** Join [GitHub Discussion #20](https://github.com/zhuamber370/memlineage/discussions/20)

## At a Glance

- **Human-first control model**: built to help the person stay oriented while agents execute
- **Open source and self-hosted first**: optimized for local or personal operator workflows today
- **Core promise**: help heavy agent users stay in control of goals, tasks, knowledge, and risky writes
- **Governance loop**: `dry-run -> diff -> approve/reject -> commit -> audit -> undo`
- **Primary surfaces**: `/` (dashboard), `/tasks`, `/knowledge`, `/changes`, `/skills`
- **Runtime coverage**: OpenClaw + Codex out of the box, plus custom runtimes via API contract
- **Storage model**: SQLite by default, PostgreSQL supported

## 60-Second Dry-Run Demo

### 0) Prereq

Start backend + frontend first (see [Quickstart (Local)](#quickstart-local)). Then verify backend health:

```bash
curl -sS http://127.0.0.1:8000/health
```

### 1) Create a proposal (dry-run)

```bash
curl -sS -X POST http://127.0.0.1:8000/api/v1/changes/dry-run \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "cli",
    "actor": { "type": "user", "id": "local" },
    "actions": [
      {
        "type": "create_knowledge",
        "payload": {
          "title": "MemLineage dry-run demo",
          "body": "Hello from dry-run. This is only written after commit.",
          "category": "mechanism_spec"
        }
      }
    ]
  }'
```

Expected: response includes `change_set_id`, `summary`, and `diff_items`.

### 2) Commit only after human approval

```bash
CHG_ID="chg_..."  # replace with returned change_set_id

curl -sS -X POST "http://127.0.0.1:8000/api/v1/changes/${CHG_ID}/commit" \
  -H "Content-Type: application/json" \
  -d '{
    "approved_by": { "type": "user", "id": "local" },
    "client_request_id": "readme-dryrun-quickstart"
  }'
```

If you do not approve, reject it in `/changes` (or just do not commit).

## Quickstart (Local)

### 1) Clone

```bash
git clone https://github.com/zhuamber370/memlineage.git
cd memlineage
```

### 2) Configure env

```bash
cp .env.example .env
cp .env frontend/.env.local
```

Default local mode:
- `AFKMS_DB_BACKEND=sqlite`
- `AFKMS_REQUIRE_AUTH=false`

### 3) Run backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn src.app:app --reload --port 8000
```

### 4) Run frontend

```bash
cd frontend
npm install
npm run dev
```

### 5) Verify

- Backend: <http://127.0.0.1:8000/health>
- Frontend: <http://127.0.0.1:3000>

For PostgreSQL setup and deeper runtime options, see:
- [backend/README.md](backend/README.md)
- [frontend/README.md](frontend/README.md)

## OpenClaw Integration

Option A (recommended): manage install/uninstall/enable/disable/update from UI:

- Open <http://127.0.0.1:3000/skills>
- Use the `OpenClaw` card actions
- Click `Detect` to auto-resolve runtime path (OPENCLAW_WORKSPACE_DIR -> OPENCLAW_CONFIG_PATH/openclaw.json -> ~/.openclaw/workspace)
- If auto-detect fails, provide manual runtime root path, then click `Save Path` and `Detect` again
- Note: this requires MemLineage backend and OpenClaw runtime on the same machine
- Note: Detect/Install only manage the skill files. They do not inject `KMS_BASE_URL` or `KMS_API_KEY` into the OpenClaw gateway runtime.

Option B: install via script:

```bash
bash scripts/install_openclaw_memlineage_skill.sh
```

Set runtime env where the OpenClaw gateway actually runs:

- If `AFKMS_REQUIRE_AUTH=false` in local quickstart mode, `KMS_API_KEY` can be any non-empty placeholder such as `dev-api-key`.
- If `AFKMS_REQUIRE_AUTH=true`, `KMS_API_KEY` must match the backend key.

If you start OpenClaw manually from your shell:

```bash
export KMS_BASE_URL="http://127.0.0.1:8000"
export KMS_API_KEY="dev-api-key"
openclaw gateway restart
```

If OpenClaw runs as a macOS `launchd` service, update `~/Library/LaunchAgents/ai.openclaw.gateway.plist` under `EnvironmentVariables` and then reload it:

```bash
plutil -p ~/Library/LaunchAgents/ai.openclaw.gateway.plist

launchctl bootout gui/$(id -u) ai.openclaw.gateway || true
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.openclaw.gateway.plist
launchctl kickstart -k gui/$(id -u)/ai.openclaw.gateway
```

Verify after install and gateway restart:

```bash
openclaw skills info memlineage --json
openclaw skills check --json
```

Interpretation:

- `eligible=true` means the skill files and required env are both visible to OpenClaw.
- `eligible=false` after install usually means the gateway runtime still cannot see `KMS_BASE_URL` / `KMS_API_KEY`.
- On macOS `launchd`, exporting vars in your current terminal is not enough for a background gateway that was started earlier as a service.

Uninstall:

```bash
bash scripts/uninstall_openclaw_memlineage_skill.sh
```

## Codex Integration

Option A (recommended): manage install/uninstall/enable/disable/update from UI:

- Open <http://127.0.0.1:3000/skills>
- Use the `Codex` card actions
- Click `Detect` to auto-resolve runtime path (CODEX_HOME -> ~/.codex)
- If auto-detect fails, provide manual runtime root path, then click `Save Path` and `Detect` again
- Note: this requires MemLineage backend and Codex runtime on the same machine

Option B: install via script:

```bash
bash scripts/install_codex_memlineage_skill.sh
```

Uninstall:

```bash
bash scripts/uninstall_codex_memlineage_skill.sh
```

After install, start a new Codex session to load the updated skill list.

## How to Talk to Your Agent (Skill Examples)

These examples work for both OpenClaw and Codex after the MemLineage skill is enabled.
You can use natural language; you do not need to mention API endpoints or action names.

These prompts are phrased to match the skill routing domains in `skills/memlineage/SKILL.md`
(`tasks`, `journals`, `notes`, `knowledge`, `routes/DAG`, `changes`, `audit`).

Read intent examples (no write):

```text
What should I prioritize today? Show my top tasks with blocked status, due dates, and quick rationale.
```

```text
For task "Release v0.1.2", where am I in the DAG right now? Show current node, previous step, and next dependency.
```

```text
Show recent knowledge and note updates for onboarding and release topics from the last 7 days.
```

```text
Who changed task statuses in the last 24 hours? Give me a short audit timeline by actor and action.
```

Explicit write intent examples (proposal first):

```text
Please create a todo proposal for me: "Prepare v0.1.3 changelog", priority P1, due this week. Do not commit yet.
```

```text
Append a journal entry proposal for today: "Finished dashboard polish and verified release notes." Keep it as proposal only.
```

```text
Create a knowledge proposal titled "Safe-to-write policy" under decision_record, saying all agent writes require dry-run and human approval.
```

Review / commit / reject / undo examples:

```text
Show me the latest proposed change and summarize its impact before I decide.
```

```text
Commit proposal change_set_id=<id>. I approve this change.
```

```text
Reject proposal change_set_id=<id> because the title and tags are still unclear.
```

```text
Undo the last commit. Reason: wrong task target.
```

Safety instruction you can keep as a standing rule:

```text
For any write request, always create a proposal first and wait for my explicit "commit" confirmation.
```

Integration references:
- Agent integration guide: [INTEGRATION.md](INTEGRATION.md)
- Skill contract: [skills/memlineage/SKILL.md](skills/memlineage/SKILL.md)

## Latest Release (v0.1.2)

- Release page: [MemLineage v0.1.2](https://github.com/zhuamber370/memlineage/releases/tag/v0.1.2)
- Home Dashboard (`/`) now provides a global snapshot with focused `Task / Knowledge` boards.
- Changes reminders moved to the left sidebar `Changes` nav badge (with pending count) instead of a dedicated home-board panel.
- Dashboard cards and focus actions support query-driven deep links into `/tasks`, `/changes`, and `/knowledge`.
- Post-release stabilization fixed `Open Studio` task selection race and stale DAG/log replay under rapid task switching.
- Dashboard polish improved chart readability and focus-board scanning for daily operation.

Supporting release docs:
- [MVP Release Notes](docs/reports/mvp-release-notes.md)
- [Home Dashboard Changelog (2026-03-01)](docs/reports/2026-03-01-home-dashboard-changelog.md)

## Latest on main (Unreleased)

- Added manual detect flow with auto runtime path fallback for skill operations.
- Added Skill Management UI runtime actions for both OpenClaw and Codex:
  - install / uninstall
  - enable / disable
  - update / health check
- Added backend Skill Management API surface under `/api/v1/skills/*` for status, detect, path config, install, enable, update, and health.
- Updated Home dashboard layout by removing duplicated `Changes Board` and tightening task/knowledge panel density.
- Added left-sidebar `Changes` pending badge reminder and fixed immediate count refresh after commit/reject/undo.
- Added Home `Database Safety` card with:
  - local backup download (`.mlbk`)
  - local file restore (direct DB overwrite after explicit confirmation)
- Expanded the Home dashboard global snapshot to include `News Total`.
- Rebalanced Home board layout into a working row of `Task / Knowledge / News`, with `Database Safety` moved to a full-width lower panel.
- Added `/news` published-date filtering with single-day bounds and quick actions:
  - `Today`
  - `Previous Day`
  - `Next Day`
- Backup download now keeps timestamped filename from backend (`memlineage-backup-YYYYMMDD-HHMMSS.mlbk`) in browser fetch flow.
- PostgreSQL backup/restore now targets business schema only (`public`) to avoid extension ownership conflicts during restore, and logs command stderr summary on failure.

## Evaluation Flow (after stack is running)

If you need to assess write safety quickly:

1. Run the [60-Second Dry-Run Demo](#60-second-dry-run-demo).
2. Open `/changes` and review one proposed diff.
3. Commit once, then run an undo to verify rollback + audit behavior.

If you run agents in production, please share your checklist in [Discussion #20](https://github.com/zhuamber370/memlineage/discussions/20).

## Docs and Proof

- Full docs index: [docs/README.md](docs/README.md)
- Safe-to-Write checklist: [docs/guides/safe-to-write-checklist.md](docs/guides/safe-to-write-checklist.md)
- Runtime/API contract: [docs/guides/agent-api-surface.md](docs/guides/agent-api-surface.md)
- Proof pack: [docs/proof/README.md](docs/proof/README.md)

## Community

- Operator feedback thread: [What is your minimum safe-to-write checklist for production AI agents?](https://github.com/zhuamber370/memlineage/discussions/20)
- Current focus questions:
  1. Which approval/audit fields are non-negotiable before commit?
  2. Where should approval happen in practice (app layer, queue boundary, CI gate, or elsewhere)?
  3. Which failure mode is most important to defend first?

## Contributing

- Start guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Contributor dev setup: [docs/contributing/dev-setup.md](docs/contributing/dev-setup.md)
- Good first issues: <https://github.com/zhuamber370/memlineage/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22>

## Security

Please follow [SECURITY.md](SECURITY.md) for responsible disclosure.

## License

Apache-2.0. See [LICENSE](LICENSE).
