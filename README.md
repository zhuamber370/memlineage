# MemLineage

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Open Issues](https://img.shields.io/github/issues/zhuamber370/memlineage)](https://github.com/zhuamber370/memlineage/issues)
[![Last Commit](https://img.shields.io/github/last-commit/zhuamber370/memlineage)](https://github.com/zhuamber370/memlineage/commits/main)

MemLineage is an **open-source work control layer** for humans who run meaningful work through agents.
It works with OpenClaw, Codex, and custom agent runtimes.

It keeps five kinds of state visible in one place:
- goals
- tasks and next steps
- durable knowledge
- governed writes and review state
- local runtime skill state

MemLineage is for the human operator. It is not another chat window, and it is not an agent-side task planner.
It adds a PR-like control loop in front of agent writes:
**dry-run -> diff preview -> human approve/reject -> commit -> audit (+ undo)**.

Quick links:
- Run full stack: [Quickstart (Local)](#quickstart-local)
- Try locally in 60 seconds: [Dry-Run Demo](#60-second-dry-run-demo)
- See the UI: [UI Preview](#ui-preview)
- Manage skills in UI: <http://127.0.0.1:3000/skills>
- Agent integration guide: [INTEGRATION.md](INTEGRATION.md)
- Integrate with Codex: [Codex Integration](#codex-integration)
- Prompt examples: [How to Talk to Your Agent](#how-to-talk-to-your-agent-skill-examples)
- Runtime/API contract: [docs/guides/agent-api-surface.md](docs/guides/agent-api-surface.md)
- Production controls: [Safe-to-Write Checklist](docs/guides/safe-to-write-checklist.md)
- Operator feedback thread: [GitHub Discussion #20](https://github.com/zhuamber370/memlineage/discussions/20)

## If This Feels Familiar

- The agents are productive, but I am losing track of the overall state.
- Important goals, tasks, and next steps keep disappearing into chat history.
- I want risky writes to be reviewable and reversible before they land.
- I need a clearer control surface than raw conversation logs.
- I want local Codex / OpenClaw skill setup and health to be visible in one place.

## What You Get Today

- **Home control surface**: `/` aggregates task focus, recent knowledge, pending changes, and local database safety actions
- **Operational workspace**: `/tasks` + `/knowledge` keep day-to-day execution outside raw chat history
- **Human review inbox**: `/changes` handles dry-run diff preview, commit / reject, undo-last, and audit-backed change review
- **Runtime skill operations**: `/skills` manages detect / install / enable / disable / update / health for OpenClaw and Codex
- **Self-hostable core**: FastAPI backend + Next.js frontend with SQLite or PostgreSQL backing storage

## What MemLineage Is Not

- Not a generic note-taking or personal knowledge app
- Not a hidden agent planner where tasks exist only for the model
- Not a fully autonomous write pipeline with no human review gate
- Not a SaaS product with multi-tenant billing / OAuth today

## Who It Is For

- Solo builders and developer-operators using OpenClaw, Codex, or custom agents as part of daily work
- People who need one place to track goals, tasks, durable knowledge, runtime state, and reviewable changes
- Workflows that require human approval, audit trail, and rollback for risky agent-generated updates

## Operating Model Today

- **Open source first**: the core project is open source and self-hostable
- **Single-user trust boundary**: optimized for local or personal operator workflows today
- **Review-first writes**: risky changes go through dry-run, human review, audit, and undo
- **Optional pilot support**: onboarding and workflow design help can be layered on top when needed

## Start Here

- **OpenClaw user**: jump to [OpenClaw Integration](#openclaw-integration).
- **Codex user**: jump to [Codex Integration](#codex-integration).
- **Other agent runtime user**: start with [Quickstart (Local)](#quickstart-local), then follow [Runtime/API contract](docs/guides/agent-api-surface.md).
- **Skill operations first**: open <http://127.0.0.1:3000/skills>.
- **Fast product check**: run [Quickstart (Local)](#quickstart-local), then follow [60-Second Dry-Run Demo](#60-second-dry-run-demo).

## Product Snapshot

- **Human-first control model**: built to help the person stay oriented while agents execute
- **Core promise**: help heavy agent users stay in control of goals, tasks, knowledge, and risky writes
- **Governance loop**: `dry-run -> diff -> approve/reject -> commit -> audit -> undo`
- **Primary surfaces**: `/` (dashboard), `/tasks`, `/knowledge`, `/changes`, `/skills`
- **Runtime coverage**: OpenClaw + Codex out of the box, plus custom runtimes via API contract
- **Storage model**: SQLite for quick local start, PostgreSQL for stronger persistent setups

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

## UI Preview

> Screenshots use synthetic test data.

![Home dashboard (synthetic test data)](docs/assets/screenshots/home-dashboard.png)

![Changes UI: dry-run diff preview](docs/assets/screenshots/changes-ui-dryrun.png)

![Tasks dashboard (synthetic test data)](docs/assets/screenshots/tasks-dashboard.png)

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

Option B: install via script:

```bash
bash scripts/install_openclaw_memlineage_skill.sh
openclaw skills info memlineage --json
openclaw skills check --json
```

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
