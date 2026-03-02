> Documentation Status: Current
> Last synced: 2026-03-01

# 2026-03-01 DAG EntityLog Changelog

## Scope
- Implementation plan: `docs/plans/2026-03-01-dag-entity-log-implementation-plan.md`
- Goal: unify DAG execution records into `entity_logs`, and simplify execution-panel interactions in the frontend.

## Backend Delivery
- Added unified log model: `entity_logs` (`entity_type + entity_id`).
- Delivered node and edge log CRUD APIs (including patch/delete).
- Added `has_logs` to route graph response for both nodes and edges.
- Kept legacy `description` fields for compatibility, but no longer use them as the primary execution log entry.

## Frontend Delivery
- Replaced description editor with a log panel in the execution inspector.
- Simplified add-step form to `title + status`.
- Simplified DAG edge interactions:
  - Removed edge-type checks and relation-label rendering.
  - Removed edge-log entry and edge selection interactions.
  - Kept pure node-to-node connection lines only.
- Fixed idea-to-route flow so created execution nodes use `goal` type.
- Upgraded DAG layout engine:
  - Migrated from custom layering to `@dagrejs/dagre`.
  - Adopted layered LR layout with crossing minimization.
  - Updated node coordinates and canvas bounds handling for more stable auto-fit behavior.

## Final Sync (2026-03-01)
- Synced `docs/reports/mvp-release-notes.md` with latest delivery status.
- Added this changelog as the final record for this implementation.
- Added execution-complete updates in the plan document.
- Added GitHub commit summary (below).

## GitHub Changes (This Push)
- `feat(frontend): optimize DAG layout to reduce edge crossings`
- `chore(frontend): adopt @dagrejs/dagre for production DAG auto-layout`
- Main files:
  - `frontend/src/components/task-execution-panel.tsx`
  - `frontend/package.json`
  - `frontend/package-lock.json`
  - `docs/reports/mvp-release-notes.md`
  - `docs/reports/2026-03-01-dag-entity-log-changelog.md`

## Verification
- Frontend build: `cd frontend && npm run build`
- Backend targeted regression: `cd backend && pytest tests/test_routes_api.py -q`

## Notes
- Local validation used database host `192.168.50.245` as requested.
- Local PostgreSQL environment artifacts were intentionally excluded from remote commits.
