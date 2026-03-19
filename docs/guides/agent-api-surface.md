> Documentation Status: Current
> Last synced: 2026-03-19

# Agent API Surface (MemLineage)

This document defines the current agent-facing API contract.
Use it when implementing or verifying a MemLineage agent integration.
This is a runtime contract document, not a product overview.

## 1) Read APIs (direct read)

### Tasks / Topics
- `GET /api/v1/tasks`
- `GET /api/v1/tasks/views/summary`
- `GET /api/v1/tasks/{task_id}/sources`
- `GET /api/v1/topics`

### Notes / Knowledge / Links / Inbox
- `GET /api/v1/notes/search`
- `GET /api/v1/notes/{note_id}/sources`
- `GET /api/v1/notes/topic-summary`
- `GET /api/v1/knowledge`
- `GET /api/v1/knowledge/{item_id}`
- `GET /api/v1/links`
- `GET /api/v1/inbox`
- `GET /api/v1/inbox/{inbox_id}`

### News
- `GET /api/v1/news`
- `GET /api/v1/news/{news_id}`

### Journals
- `GET /api/v1/journals`
- `GET /api/v1/journals/{journal_date}`
- `GET /api/v1/journals/{journal_date}/items`

### Idea / Route graph
- `GET /api/v1/ideas`
- `GET /api/v1/routes`
- `GET /api/v1/routes/{route_id}/graph`
- `GET /api/v1/routes/{route_id}/nodes/{node_id}/logs`

### Governance / Context / Audit
- `GET /api/v1/changes`
- `GET /api/v1/changes/{change_set_id}`
- `GET /api/v1/context/bundle`
- `GET /api/v1/audit/events`

## 2) Agent Write Governance Flow

All agent-originated writes should use the governed write flow:

1. `POST /api/v1/changes/dry-run`
2. Wait for human approval
3. Commit: `POST /api/v1/changes/{change_set_id}/commit`
4. Or reject: `DELETE /api/v1/changes/{change_set_id}`
5. Rollback when needed: `POST /api/v1/commits/undo-last`

## 3) Dry-Run Action Types

`actions[].type` currently supports:

- `create_task`
- `append_note`
- `update_task`
- `patch_note`
- `upsert_journal_append`
- `link_entities`
- `create_idea`
- `patch_idea`
- `promote_idea`
- `create_route`
- `patch_route`
- `create_route_node`
- `patch_route_node`
- `delete_route_node`
- `create_route_edge` (connector-only)
- `delete_route_edge` (connector-only)
- `append_route_node_log`
- `create_knowledge`
- `patch_knowledge`
- `archive_knowledge`
- `delete_knowledge`
- `create_news`
- `patch_news`
- `archive_news`
- `delete_news`
- `create_link`
- `delete_link`
- `capture_inbox`

## 4) Action Family Notes

### Task + note basics
- `create_task`: create a new task.
- `update_task`: patch one existing task.
- `append_note`: create a note with sources.
- `patch_note`: append/patch note body/tags/topic/status.

### Journal
- `upsert_journal_append`: append a journal item under one date.

### Knowledge
- `create_knowledge`, `patch_knowledge`, `archive_knowledge`, `delete_knowledge`
- Knowledge is currently note-backed in runtime.
- Valid categories: `ops_manual | mechanism_spec | decision_record`.

### News
- `create_news`, `patch_news`, `archive_news`, `delete_news`
- News is a dedicated runtime domain backed by `news_items + news_sources`.
- Each news item stores one primary source and optional reference sources.
- News does not carry `topic_id` and does not support downstream promotion/linkage.
- `GET /api/v1/news` supports `status`, `q`, `published_from`, and `published_to` for list filtering.
- First release does not deduplicate repeated events across batches.

### Idea + route graph
- `create_idea`, `patch_idea`, `promote_idea`
- `create_route`, `patch_route`
- `create_route_node`, `patch_route_node`, `delete_route_node`
- `create_route_edge`, `delete_route_edge`
- Route edges are connector-only links between nodes. They do not carry relation, description, or log metadata.
- `append_route_node_log`

### Links + inbox
- `create_link`, `delete_link`
- `capture_inbox`

## 5) Core Payload Envelopes

### Dry-run request

```json
{
  "actions": [
    {
      "type": "create_task",
      "payload": {
        "title": "Ship docs sync",
        "status": "todo",
        "topic_id": "top_fx_other",
        "source": "chat://openclaw/thread-123/msg-8"
      }
    }
  ],
  "actor": { "type": "agent", "id": "openclaw" },
  "tool": "openclaw-skill"
}
```

Note:
- `status: "todo"` is the current API enum for a not-started task.
- Product docs may say "task" in user-facing wording, but the runtime enum remains `todo`.

### Commit request

```json
{
  "approved_by": { "type": "user", "id": "usr_local" },
  "client_request_id": "optional-idempotency-key"
}
```

### Undo request

```json
{
  "requested_by": { "type": "user", "id": "usr_local" },
  "reason": "human rollback",
  "client_request_id": "optional-idempotency-key"
}
```

## 6) MemLineage Skill Mapping (Codex + OpenClaw)

Production skill path:
- `skills/memlineage/SKILL.md`
- `skills/memlineage/index.js`
- `skills/memlineage/lib/client.js`

Action mapping:
- `list_*` and `get_*` skill actions call read APIs directly.
- `propose_*` skill actions call `POST /api/v1/changes/dry-run`.
- `commit_changes` calls commit API.
- `reject_changes` calls reject API.
- `undo_last_commit` calls undo API.

## 7) Compatibility Note

Historical docs that mention `playbook|decision|brief` knowledge typing or `/api/v1/knowledge/migration/*` are not current runtime contracts.
Current runtime contract is this document + API schemas in `backend/src/schemas.py`.
