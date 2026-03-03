# MemLineage Integration (OpenClaw + Codex)

MemLineage is designed to be the **governed memory & change-governance layer** for OpenClaw and Codex workflows.

It helps you prevent "agent writes" from silently polluting memory/knowledge by enforcing a PR-like loop:

**dry-run → diff preview → human approve/reject → commit → audit (+ undo)**

---

## What you integrate

Integrate MemLineage at the boundary of *writes*:

Agent/Skill wants to write → MemLineage **dry-run** (diff) → human review → **commit** → data applied + audit trail.

Reads are safe by default.

---

## Minimal setup

1) Run MemLineage backend + frontend (see `README.md` Quickstart)

2) Option A (recommended): use Skill Management UI

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

5) Configure env (where OpenClaw/Codex runs)

- `KMS_BASE_URL=http://127.0.0.1:8000`
- `KMS_API_KEY=...`

Quick uninstall commands (script path):

```bash
bash scripts/uninstall_openclaw_memlineage_skill.sh
bash scripts/uninstall_codex_memlineage_skill.sh
```

---

## How the control loop works (PR-like changes)

### Reads
- Safe by default (no writes).

### Writes
- Always go through: **dry-run → confirm → commit**.

### Human approval
- Use `/changes` UI to review diff and commit/reject.

### Rollback
- If a commit goes wrong, use **undo** to roll back the last commit.

---

## Integration checklist (for OpenClaw/Codex skill authors)

- [ ] Every write path is routed through MemLineage changes pipeline
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
