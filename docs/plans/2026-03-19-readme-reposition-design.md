> Documentation Status: Confirmed Design
> Last synced: 2026-03-19

# Top-Level README Repositioning Design

Date: 2026-03-19
Status: Confirmed
Scope: top-level `README.md` only

## 1. Context

The current top-level README frames MemLineage primarily as an agent-heavy control layer with write governance.
That story is not wrong, but it undersells what the current code already provides:

1. A human-facing web UI with direct CRUD for tasks and knowledge.
2. A skill-based entry point for agents to read and write the same backend.
3. A local-first workflow that is especially relevant to solo developers.

The confirmed product story for this rewrite is not "more control over agents."
It is "a shared workspace where humans and agents maintain the same operational data, without forcing every simple change through chat."

## 2. Confirmed Positioning

MemLineage should be presented as:

- a shared workspace for solo developers working with agents
- a web UI for humans to manage tasks and knowledge directly
- a skill-backed interface for agents to access the same data
- a way to remove simple CRUD from chat and reduce unnecessary token usage

Current scope to emphasize:

- `tasks`
- `knowledge`

Supporting capabilities that should remain visible but secondary:

- proposed-write review on `/changes`
- local skill runtime management on `/skills`
- home dashboard and database backup/restore on `/`

## 3. Messaging Boundaries

The README should explicitly avoid these traps:

1. Do not lead with "agent control layer" or "governed memory layer."
2. Do not position the product as a team collaboration platform.
3. Do not spend the first screen on future roadmap items.
4. Do not explain "rules as skill content" in this version of the README.

The README may mention current knowledge categories when useful, but the primary story should stay on present-day task and knowledge workflows.

## 4. Product Story to Land

The reader should leave the README with this understanding:

1. MemLineage is for solo developers who work with agents regularly.
2. Humans use the web UI for fast, direct CRUD.
3. Agents use skills to access the same workspace data.
4. This lowers token waste because simple edits no longer need a full chat loop.
5. The system still provides review and rollback for agent-originated writes when needed.

## 5. README Information Architecture

Recommended section order:

1. Title, badges, and one-paragraph positioning
2. Why this exists
3. What you can do today
4. UI preview
5. How human + agent collaboration works
6. What is in the code today
7. Quickstart
8. Connect your agent
9. Example prompts
10. Docs / contributing / security / license

## 6. Source-of-Truth Constraints

The rewrite must stay aligned with the current repository:

- Web routes currently include `/`, `/tasks`, `/knowledge`, `/news`, `/changes`, and `/skills`.
- Task CRUD and task execution studio are already present in the frontend.
- Knowledge CRUD is already present and backed by `/api/v1/knowledge`.
- Agent integration exists through the bundled skill at `skills/memlineage`.
- Codex and OpenClaw install paths are supported via scripts and the `/skills` UI.
- Database backup/restore actions exist on the home dashboard.

## 7. Success Criteria

The rewrite succeeds if:

1. The first screen clearly targets solo developers.
2. The README explains the dual entry model: human via web, agent via skill.
3. Token savings from removing simple CRUD from chat is stated as a primary benefit.
4. The text reflects the current codebase without promising unbuilt scope.
