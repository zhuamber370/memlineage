---
name: memlineage
version: 1.0.0
description: Use proactively and MUST BE USED for tasks/journals/notes/knowledge/routes/changes/audit requests; prioritize MemLineage read actions, keep write operations explicit-confirmation only.
metadata:
  openclaw:
    emoji: "🗂️"
    requires:
      env:
        - KMS_BASE_URL
        - KMS_API_KEY
---

# MemLineage Skill

Use this skill when you need to read or write MemLineage data.

## Activation Priority (MUST)

1. Proactive activation
- This skill MUST BE USED for requests related to:
  - tasks
  - journals
  - notes
  - knowledge
  - routes / DAG execution
  - changes / commits / undo
  - audit events
- Do not wait for users to mention API names or action names.

2. Highest-priority routing
- When a request falls into the domains above, route to `memlineage` read actions first.
- Only use other generic tools when MemLineage has no matching read capability.

3. Integration contract
- Runtime pattern remains: REST + tool calling (JSON Schema).
- Tools return standard structured JSON for stability and testing.
- Conversation output should be natural language by default (see Response Policy).

## Governance Rules

1. Single source of truth
- Tasks, journals, notes, knowledge, and route execution data are read/written in MemLineage only.

2. Explicit write trigger
- Write only when the user gives an explicit write command.

3. Dry-run first
- All `propose_*` actions go through `POST /api/v1/changes/dry-run`.
- Return proposal summary + `change_set_id` before any commit.

4. Commit only after confirmation
- Call `commit_changes` only after user confirmation.

5. Reject stale proposals
- If user rejects a proposal, call `reject_changes`.

6. Undo support
- Use `undo_last_commit` when user requests rollback.

7. Source traceability
- Include `source`/`source_ref` whenever the target action supports it.

8. Task topic safety
- For `propose_record_todo`, ensure `topic_id` is present (explicit or inferred/fallback).

## Natural-Language Routing (MUST)

1. User should not need API names
- Interpret intent from natural language and choose actions automatically.
- Do not ask user to specify endpoint/action unless disambiguation is strictly required.

2. Task execution / DAG questions (highest priority)
- If user asks about "current node / DAG / node status / branch relations / dependencies / execution progress", use:
  1) `get_task_execution_snapshot` first
  2) then `get_route_graph` / `list_route_node_logs` only when extra detail is needed
- Do not use `get_context_bundle` as the primary source for DAG answers.

3. Resolve task target automatically
- If user does not provide `task_id`, resolve via natural-language task query/title.
- If multiple tasks match and cannot be safely resolved, return candidates and ask for disambiguation.

4. Action priority
- Prefer dedicated read actions over generic `api_get`.
- `api_get` is last-resort fallback for uncovered read paths only.

5. Read-first safety
- For information requests, perform read actions only.
- Never trigger `propose_*` / commit / reject / undo unless user explicitly asks to write.

## Natural-Language Routing Examples

Use these mappings as default behavior:

1. "Which todos should I prioritize today?"
- Use `list_tasks` + optional `list_task_views_summary`, then answer in natural language.

2. "Which node is this task currently on?"
- Use `get_task_execution_snapshot` first, then `get_route_graph` if needed.

3. "Append yesterday's meeting notes to the journal."
- This is explicit write intent: use `propose_append_journal`, then wait for confirmation before `commit_changes`.

4. "Show recent knowledge updates by topic."
- Use `list_note_topic_summary` + `list_knowledge` and summarize by topic.

5. "Find notes related to onboarding."
- Use `search_notes` with query/topic filters; return top matches + ask whether to continue paging.

6. "I want to see details and impact of this change."
- Use `get_change`; explain impact in user language.

7. "Rollback the last commit."
- Explicit write intent: use `undo_last_commit`.

8. "Who changed task statuses recently?"
- Use `list_audit_events` with filters, then summarize actor/action timeline.

## Response Style (MUST)

1. Natural-language first
- Explain findings in business/task language, not database language.
- Lead with the direct answer, then give key evidence.
- Default answer structure:
  1) Conclusion
  2) Key points
  3) Suggested next step

2. Hide technical internals by default
- Do not mention API paths, action names, table/field names, or SQL-like wording unless user explicitly asks.
- Do not dump raw JSON unless user explicitly asks for raw output / debug output.

3. Translate system terms into user language
- Convert status/enums to natural phrasing (e.g. `execute` -> "in progress", `waiting` -> "waiting", `done` -> "completed").
- Prefer "what is happening now / what comes next / what is blocked" over raw identifiers.

4. Structured but human
- For task execution answers, use this order:
  1) Current progress (current node + status)
  2) Critical path (dependency relations)
  3) Risks or suggestions (if any)
- Keep IDs and low-level metadata in a separate "I can expand technical details on request" section.

5. Ambiguity handling
- If task/route target is ambiguous, ask one concise disambiguation question with top candidates.
- Once clarified, continue with a natural-language summary.

## Error Message Mapping (MUST)

When backend returns machine error codes, convert to user-friendly wording:

- `TOPIC_NOT_FOUND` -> "Topic not found. Please choose an existing topic first."
- `TASK_NOT_FOUND` -> "Task not found. Please confirm the task name or ID."
- `CHANGE_SET_NOT_FOUND` -> "Change set not found. It may already be committed or removed."
- `TASK_CANCEL_REASON_REQUIRED` -> "A cancel reason is required when setting status to cancelled."
- `TASK_INVALID_STATUS_TRANSITION` -> "This status transition is not allowed directly. Please follow the status flow."
- `NO_COMMIT_TO_UNDO` -> "There is no commit available to undo."

If code is unknown:
- Explain what failed in plain language.
- Provide one concrete next step.

## Large Result Handling (MUST)

1. Summary first
- For large lists, provide a compact summary first (count + top highlights).

2. Page by default
- Use page/page_size based read actions.
- Return first page highlights, then ask whether user wants the next page.

3. No raw dump
- Do not output full raw JSON for large payloads unless explicitly requested for debugging.

## Read Actions

- `get_context_bundle`
- `list_tasks`
- `list_topics`
- `list_ideas`
- `list_changes`
- `get_change`
- `list_audit_events`
- `list_task_views_summary`
- `list_note_topic_summary`
- `list_routes`
- `list_task_routes`
- `get_route_graph`
- `list_route_node_logs`
- `get_task_execution_snapshot` (includes current node + previous step)
- `search_notes`
- `list_journals`
- `get_journal`
- `list_journal_items`
- `list_task_sources`
- `list_note_sources`
- `list_links`
- `list_inbox`
- `get_inbox`
- `list_knowledge`
- `get_knowledge`
- `api_get` (fallback generic GET for uncovered `/api/v1/*` paths only)

## Write Actions

- `propose_record_todo`
- `propose_append_journal`
- `propose_upsert_knowledge`
- `propose_capture_inbox`
- `propose_create_idea`
- `propose_patch_idea`
- `propose_promote_idea`
- `propose_create_route`
- `propose_patch_route`
- `propose_create_route_node`
- `propose_patch_route_node`
- `propose_delete_route_node`
- `propose_create_route_edge`
- `propose_patch_route_edge`
- `propose_delete_route_edge`
- `propose_append_route_node_log`
- `propose_create_knowledge`
- `propose_patch_knowledge`
- `propose_archive_knowledge`
- `propose_delete_knowledge`
- `propose_create_link`
- `propose_delete_link`
- `commit_changes`
- `reject_changes`
- `undo_last_commit`

## Environment

Set before starting OpenClaw:

```bash
export KMS_BASE_URL="http://127.0.0.1:8000"
export KMS_API_KEY="your_api_key"
```

Optional:

```bash
export KMS_ACTOR_ID="openclaw"
```
