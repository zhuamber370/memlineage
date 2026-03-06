# 2026-03-01 DAG EntityLog Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to execute this plan task by task.

## Goal
Replace node `description` editing entry points with unified execution logs stored in `entity_logs`, and expose log presence on DAG nodes via badges.

## Architecture
- Backend introduces a unified `entity_logs` model keyed by `entity_type + entity_id`.
- Node log CRUD remains the only supported execution-log path.
- `/graph` returns `has_logs` for nodes.
- Frontend inspector switches from description editor to log panel.

## Task Breakdown

### Task 1: Backend Schema and Model (`EntityLog`)
**Files**
- `backend/src/models.py`
- `backend/src/db.py`
- `backend/tests/test_routes_api.py`

**Implementation**
1. Add `EntityLog` model with required fields and defaults.
2. Add runtime schema ensure for `entity_logs` and related indexes.
3. Keep legacy fields/tables for compatibility.

**Verification**
- `cd backend && python3 -m pytest -q tests/test_routes_api.py`

---

### Task 2: Pydantic Schemas and DTOs
**Files**
- `backend/src/schemas.py`
- `backend/tests/test_routes_api.py`

**Implementation**
1. Add request/response schemas for entity logs.
2. Add list wrappers and patch payload schema.
3. Keep backward-compatible structures as needed.

**Verification**
- `cd backend && python3 -m pytest -q tests/test_routes_api.py`

---

### Task 3: Unified Service Implementation
**Files**
- `backend/src/services/route_service.py`
- `backend/tests/test_routes_api.py`

**Implementation**
1. Add shared service methods:
   - create/list/patch/delete entity logs
2. Enforce validation:
   - unsupported entity type
   - cross-route ownership mismatch
   - empty content
   - missing log id / wrong ownership
3. Keep compatibility wrappers for node-log paths.

**Verification**
- `cd backend && python3 -m pytest -q tests/test_routes_api.py`

---

### Task 4: Routes API Endpoints for Node Logs
**Files**
- `backend/src/routes/routes.py`
- `backend/src/schemas.py`
- `backend/tests/test_routes_api.py`

**Implementation**
1. Add full node log CRUD endpoints.
2. Map validation exceptions to stable API error codes.

**Verification**
- `cd backend && python3 -m pytest -q tests/test_routes_api.py`

---

### Task 5: Graph `has_logs` Output
**Files**
- `backend/src/services/route_service.py`
- `backend/src/schemas.py`
- `backend/tests/test_routes_api.py`

**Implementation**
1. Extend route graph output schemas with `has_logs: bool`.
2. Batch compute log existence by route and annotate nodes.

**Verification**
- `cd backend && python3 -m pytest -q tests/test_routes_api.py`

---

### Task 6: Frontend Inspector Migration to Log Panel
**Files**
- `frontend/src/components/task-execution-panel.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/i18n.tsx`

**Implementation**
1. Remove description draft/save state and handlers.
2. Add log panel states (`entityLogs`, draft, edit mode).
3. Render create/edit/delete log interactions in inspector.

**Verification**
- `cd frontend && npm run build`
- Manual: create/edit/delete logs for nodes.

---

### Task 7: DAG Badge Rendering
**Files**
- `frontend/src/components/task-execution-panel.tsx`
- `frontend/app/globals.css`

**Implementation**
1. Render node badge when `node.has_logs` is true.
2. Keep status-color semantics intact.

**Verification**
- `cd frontend && npm run build`
- Manual: badge appears/disappears with log presence.

---

### Task 8: Compatibility and Docs
**Files**
- `backend/README.md`
- `docs/reports/mvp-release-notes.md`
- `docs/reports/2026-03-01-dag-entity-log-changelog.md`

**Implementation**
1. Document node log APIs and unified storage.
2. Keep legacy node-log read path behavior documented.
3. Add release notes and changelog updates.

**Verification**
- `rg -n "entity_logs|node logs" backend/README.md docs/reports -S`

---

### Task 9: End-to-End Validation and Closeout
**Verification checklist**
1. Node log CRUD works.
2. Timestamps are auto-generated and updated correctly.
3. Graph badges reflect true log presence.
4. Description editor entry point is removed.
5. Regression checks pass for existing route graph flows.

**Commands**
- Backend: `cd backend && python3 -m pytest -q`
- Frontend: `cd frontend && npm run build`

## Error Contract
- `404`: route/node/log not found
- `422`: invalid payload (e.g., empty content)
- `409`: cross-route or invalid ownership mapping

## Engineering Constraints
1. DRY: use shared service logic for node logs and compatibility wrappers.
2. YAGNI: no attachments/comments/search in this phase.
3. Verification-first: run checks after each task.

## Suggested Skills
- `test-driven-development`
- `verification-before-completion`
- `requesting-code-review`

## Completion Record
- [x] Task 1: Schema/model
- [x] Task 2: DTOs
- [x] Task 3: Service
- [x] Task 4: API
- [x] Task 5: `has_logs`
- [x] Task 6: Frontend inspector migration
- [x] Task 7: Badge rendering
- [x] Task 8: Compatibility/docs
- [x] Task 9: End-to-end validation
