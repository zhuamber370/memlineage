# 2026-03-01 DAG EntityLog Unified Logging Design

## 1. Background and Goal
The task execution DAG currently stores explanatory text in `description` fields on route nodes.
That model is static and not suitable for timeline-style execution records.

This design upgrades node notes to multi-entry execution logs, unified in one table: `entity_logs`.

Goals:
1. Support appending logs to nodes.
2. Persist log timestamps automatically on the server.
3. Support editing and deletion of logs.
4. Show explicit visual indicators on DAG nodes that have logs.
5. Keep changes incremental and reversible.

## 2. Confirmed Decisions
1. Do not migrate legacy `description` content into logs.
2. Logs are editable and deletable (not append-only).
3. Log schema stays minimal: content + timestamps + actor metadata.
4. DAG uses lightweight badges for node log presence (no broad visual redesign).
5. Use a single `EntityLog` table (`entity_type + entity_id`) for route nodes.

## 3. Non-Goals
1. No comments/replies, attachments, or rich text.
2. No pagination/full-text search in this phase.
3. No immediate schema cleanup for legacy node `description` columns.
4. No route-level or task-level logs in this phase.

## 4. Data Model

### 4.1 New Table: `entity_logs`
Proposed columns:
- `id`: `VARCHAR(40)`, primary key (e.g., `elg_xxx`)
- `route_id`: `VARCHAR(40)`, not null, references `routes.id`
- `entity_type`: `VARCHAR(20)`, not null, enum: `route_node`
- `entity_id`: `VARCHAR(40)`, not null, references target entity by `entity_type`
- `actor_type`: `VARCHAR(20)`, not null, default `human`
- `actor_id`: `VARCHAR(80)`, not null, default `local`
- `content`: `TEXT`, not null
- `created_at`: `TIMESTAMPTZ`, not null, default `NOW()`
- `updated_at`: `TIMESTAMPTZ`, not null, default `NOW()`

### 4.2 Constraints and Indexes
1. Constraint on `entity_type` (`route_node` only).
2. Index: `(route_id, entity_type, entity_id, created_at DESC)`.
3. Index: `(entity_type, entity_id)`.
4. App-level validation: `content.strip()` must be non-empty.
5. App-level validation: `entity_id` must belong to `route_id` and match `entity_type`.

### 4.3 Legacy Relation
1. Keep `route_nodes.description` for compatibility.
2. Keep `node_logs` in compatibility mode (read/migration source only); new writes go to `entity_logs`.

## 5. Migration and Compatibility

### 5.1 Historical Data
1. Do not migrate `description` values.
2. Migrate legacy `node_logs` into `entity_logs` to preserve execution history.

Mapping:
- `entity_type = 'route_node'`
- `entity_id = node_logs.node_id`
- `route_id` backfilled via `route_nodes.route_id`
- Copy actor/content/timestamps with same semantics

### 5.2 Transition Strategy
1. Keep legacy node-log GET endpoint readable, backed by `entity_logs`.
2. Remove node description editing path after frontend migration stabilizes.

## 6. API Design
Use existing node-log route style only.

### 6.1 Node Logs
1. `GET /api/v1/routes/{route_id}/nodes/{node_id}/logs`
2. `POST /api/v1/routes/{route_id}/nodes/{node_id}/logs`
3. `PATCH /api/v1/routes/{route_id}/nodes/{node_id}/logs/{log_id}`
4. `DELETE /api/v1/routes/{route_id}/nodes/{node_id}/logs/{log_id}`

### 6.2 Request/Response Contract
Create request:
- `content` (required)
- `actor_type` (optional, default `human`)
- `actor_id` (optional, default `local`)

Patch request:
- `content` (required, updated value)

Response fields:
- `id`, `route_id`, `entity_type`, `entity_id`
- `content`
- `actor_type`, `actor_id`
- `created_at`, `updated_at`

### 6.3 Graph Enhancement for Badges
`GET /api/v1/routes/{route_id}/graph` adds:
- `has_logs: boolean` on nodes

Optional future field (not required now):
- `log_count: int`

## 7. Frontend Interaction Design (Task Execution Panel)

### 7.1 Inspector Area
Replace description editor with a log panel:
1. Input box for adding logs.
2. Log list sorted by `created_at desc`.
3. Per-log edit and delete actions.

Behavior:
- Node selected -> use node-log APIs

### 7.2 DAG Badge Display
1. Node badge (`LOG` or dot) when `has_logs=true`.
2. Keep existing status color semantics (`waiting/execute/done`).

### 7.3 Legacy Description Behavior
1. Remove description input UI.
2. Stop sending description patch requests for nodes.

## 8. Error Handling and Validation
1. `404`: route/node/log not found.
2. `422`: empty content after trim.
3. `409`: `entity_type + entity_id` does not belong to `route_id`.
4. Validate ownership on edit/delete to avoid cross-entity mutation.

## 9. Testing Strategy

### 9.1 Backend
1. Node log CRUD tests.
2. Error-path tests (`404/422/409`).
3. Graph `has_logs` correctness for nodes.
4. Regression checks for route graph and existing DAG behavior.

### 9.2 Frontend
1. Inspector loads correct logs for the selected node target.
2. New logs refresh list immediately.
3. Edit/delete states stay consistent with server responses.
4. DAG badges match `has_logs` values.

## 10. Rollout and Rollback

### 10.1 Staged Rollout
1. Phase A: backend table/APIs/graph fields.
2. Phase B: frontend log panel + badges.
3. Phase C: remove description-edit entry points.

### 10.2 Rollback
1. Frontend issues: revert frontend to previous panel behavior.
2. Backend issues: temporarily disable node-log entry while keeping safe read paths.

## 11. Risks and Mitigations
1. No database-level polymorphic FK for `entity_id`.
   - Mitigation: strict service-layer ownership/type validation.
2. Legacy endpoint compatibility drift.
   - Mitigation: compatibility tests against old node-log endpoints.
3. UI complexity in inspector state management.
   - Mitigation: keep a single node-target state model and isolate API adapters by entity kind.
