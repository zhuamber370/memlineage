# MemLineage Integration (OpenClaw + Codex)

MemLineage is a shared workspace for solo developers working with agents.
Humans manage tasks and knowledge in the web UI, while agents access the same backend through the MemLineage skill.

For day-to-day work, this means you can keep simple CRUD in the UI and let agents read the same data directly.
When an agent needs to write, MemLineage can enforce a review loop:

**dry-run → diff preview → human approve/reject → commit → audit (+ undo)**

---

## What you integrate

Integrate MemLineage as the shared data layer between your human workflow and your agent runtime:

- Human: use the web UI for direct task and knowledge operations.
- Agent: use the MemLineage skill for reads and explicit writes.
- Agent write path: MemLineage **dry-run** → human review → **commit** → data applied + audit trail.

Reads are safe by default.

Use this document when you want Codex or OpenClaw to share the same MemLineage workspace as the web UI.
If you only need product overview or local app setup, start with [README.md](README.md).

---

## Minimal setup

1) Run MemLineage backend + frontend (see `README.md` Quickstart)

2) Option A (recommended): use the Skill Management UI

- Open `http://127.0.0.1:3000/skills`
- Manage install / uninstall / enable / disable / update for OpenClaw and Codex
- Click `Detect` to auto-resolve default runtime path for each agent
- If auto-detect fails, provide manual runtime root path, then click `Save Path` and `Detect` again
- Constraint: backend host and agent runtime host must be the same machine

3) Option B (CLI scripts): Install OpenClaw skill

```bash
bash scripts/install_openclaw_memlineage_skill.sh
```

4) Install Codex skill:

```bash
bash scripts/install_codex_memlineage_skill.sh
```

5) Configure env (where OpenClaw/Codex actually runs)

- `KMS_BASE_URL=http://127.0.0.1:8000`
- `KMS_API_KEY=...`

Notes:

- Install/detect only manage skill files. They do not inject secrets into the runtime process.
- If `AFKMS_REQUIRE_AUTH=false`, use any non-empty placeholder for `KMS_API_KEY` so the skill becomes eligible.
- If OpenClaw runs as a background macOS `launchd` service, update `~/Library/LaunchAgents/ai.openclaw.gateway.plist`, then reload/restart the gateway. Shell `export` commands do not retroactively change the environment of an already-running LaunchAgent service.

6) Verify the runtime after install

For OpenClaw, verify from the same runtime after restart:

```bash
openclaw skills info memlineage --json
openclaw skills check --json
```

If `eligible=false`, the most common cause is missing `KMS_BASE_URL` / `KMS_API_KEY` in the gateway runtime environment rather than a missing skill install.

For Codex:

- start a new Codex session after install or update
- confirm the `memlineage` skill is available in that new session

Quick uninstall commands (script path):

```bash
bash scripts/uninstall_openclaw_memlineage_skill.sh
bash scripts/uninstall_codex_memlineage_skill.sh
```

---

## How Agent Writes Work

Simple human CRUD does not need this flow; use the web UI directly for that.
This section is specifically about agent-originated writes.

### Reads
- Safe by default (no writes).

### Writes
- Agent-originated writes should go through: **dry-run → confirm → commit**.

### Human approval
- Use `/changes` UI to review diff and commit/reject.

### Rollback
- If a commit goes wrong, use **undo** to roll back the last commit.

---

## Integration checklist (for OpenClaw/Codex skill authors)

- [ ] Every write path is routed through MemLineage changes pipeline
- [ ] Read paths use MemLineage as the shared source of task/knowledge state
- [ ] You can display: `change_set_id`, `summary`, `diff_items`
- [ ] You can trigger: commit (`approved_by` + `client_request_id`)
- [ ] You can audit: commit id / who approved / when
- [ ] You have a rollback story (undo)

---

## Need help integrating?

Open an **Integration Request** issue (template included):
- https://github.com/zhuamber370/memlineage/issues/new?template=integration_request.yml

Please include:

- Your target workflow (what is writing what)
- Where you want human approval to happen
- What you want the diff to look like
- Your environment (OS / MemLineage version / OpenClaw/Codex version)
