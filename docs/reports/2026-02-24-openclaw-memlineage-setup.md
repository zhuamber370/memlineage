> Documentation Status: Current
> Last synced: 2026-02-27

# OpenClaw x MemLineage Setup Guide (workspace skill flow)

## Goal

Use MemLineage as the governed persistence layer for OpenClaw:
- read/write tasks, journals, notes, knowledge, and route data through MemLineage
- use proposal-first governance (`dry-run -> commit/reject`)
- keep rollback available (`undo_last_commit`)

## Prerequisites

1. Start backend
```bash
cd <repo_root>/backend
python3 -m uvicorn src.app:app --reload --port 8000
```

2. Expose runtime env for OpenClaw
```bash
export KMS_BASE_URL="http://127.0.0.1:8000"
export KMS_API_KEY="dev-api-key"
```

If `AFKMS_REQUIRE_AUTH=false`, any non-empty `KMS_API_KEY` value is enough for skill eligibility in local mode.
If `AFKMS_REQUIRE_AUTH=true`, use the real backend API key.

If OpenClaw is running as a macOS LaunchAgent, editing your current shell env is not enough. Add the same keys to `~/Library/LaunchAgents/ai.openclaw.gateway.plist` under `EnvironmentVariables`, then reload the service:

```bash
launchctl bootout gui/$(id -u) ai.openclaw.gateway || true
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.openclaw.gateway.plist
launchctl kickstart -k gui/$(id -u)/ai.openclaw.gateway
```

## Install workspace skill

```bash
cd <repo_root>
bash scripts/install_openclaw_memlineage_skill.sh
```

The installer auto-detects OpenClaw workspace from `~/.openclaw/openclaw.json` (`agents.defaults.workspace`) and installs to `<workspace>/skills/memlineage`.

Verify:

```bash
openclaw skills info memlineage --json
openclaw skills check --json
```

If `eligible=false`, check `KMS_BASE_URL` and `KMS_API_KEY` in the gateway runtime environment, then restart OpenClaw gateway.
When OpenClaw is service-managed, shell `export` alone will not fix an already-running gateway.

## Natural-language usage examples

1. Record a todo (proposal)
```text
Record todo:
Title=Ship API docs sync
Description=Align README and backend docs
Priority=P1
Due=2026-03-02
```

2. Append a journal entry (proposal)
```text
Append journal:
Date=2026-02-27
Content=Finished doc/runtime alignment and validated tests.
```

3. Upsert note-style knowledge (proposal)
```text
Record topic:
Title=Release checklist conventions
Body increment=Always run backend tests before merge.
Tags=release,quality
```

4. Create structured knowledge record via knowledge API (proposal)
```text
Create knowledge:
Title=Dry-run governance policy
Body=All agent writes must go through dry-run first.
Category=decision_record
```

5. Capture inbox item (proposal)
```text
Capture inbox:
Content=Evaluate MCP integration timeline next sprint.
```

6. Read context
```text
Get context:
Intent=planning
Window days=14
```

7. Governance actions
```text
Commit proposal change_set_id=<id>
Reject proposal change_set_id=<id>
Undo last commit reason=<reason>
```

## Uninstall skill

```bash
cd <repo_root>
bash scripts/uninstall_openclaw_memlineage_skill.sh
```

## Troubleshooting

1. On write failures, inspect dry-run output and API error codes first.
2. Use `reject_changes` for explicit user rejection.
3. Use `undo_last_commit` for rollback.
4. If data seems missing, verify the corresponding read endpoint in `docs/guides/agent-api-surface.md`.
