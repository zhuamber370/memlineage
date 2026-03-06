> Documentation Status: Current
> Last synced: 2026-03-01

# 2026-03-01 DAG EntityLog Changelog

## Scope
- Implementation plan: `docs/plans/2026-03-01-dag-entity-log-implementation-plan.md`
- Goal: unify DAG execution records into `entity_logs`, and simplify execution-panel interactions in the frontend.

## Backend Delivery
- Added unified log model: `entity_logs` (`entity_type + entity_id`).
- Current contract keeps `entity_logs` for route nodes only.
- Edge log CRUD has been removed from the active API surface.
- Route graph response keeps `has_logs` on nodes only.
- Route edges are plain connectors (`from_node_id -> to_node_id`) with no relation/description metadata contract.

## Frontend Delivery
- Replaced description editor with a log panel in the execution inspector.
- Simplified add-step form to `title + status`.
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
