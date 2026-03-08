> Documentation Status: Current
> Last synced: 2026-03-08

# MVP Release Notes (Synced 2026-03-04)

## Delivered
- Backend APIs for `topics/tasks/notes/knowledge/journals/inbox/links/ideas/routes/changes/context/audit`
- Governed write flow: `dry-run -> commit/reject -> undo-last`
- Audit events with chain metadata (`change_set_id`, `commit_id`, `action_index`)
- DAG execution graph logging upgrade:
  - unified `entity_logs` model for route-node execution logs
  - only node log CRUD remains exposed under `/api/v1/routes/{route_id}/nodes/{node_id}/logs`
  - `/api/v1/routes/{route_id}/graph` includes `has_logs` on nodes only
- Task Command Center UI (desktop-first):
  - search + filter + grouped list + detail in one screen
  - task detail above execution graph
  - route graph keeps pure edge connections without relation labels
  - DAG auto-layout migrated to `@dagrejs/dagre` layered engine for more stable branch alignment
  - selected-node `...` menu supports:
    - inline add step
    - set status (`waiting/execute/done`)
    - rename
    - delete (leaf node only)
  - task execution panel simplification:
    - add-step inline form now keeps only title + status
- Home Dashboard (`/`) for personal overview:
  - global snapshot + `Task / Knowledge / News` board layout
  - pending change proposals are surfaced as a left-sidebar `Changes` badge reminder
  - `Database Safety` card supports local backup download and local-file restore overwrite flow
  - focus task ranking rule: `P0 + in_progress` first, then due date, then latest update, then title tie-break
  - dashboard cards deep-link to target pages with query-based filter hydration
  - per-board loading/error/empty isolation to avoid single-source failure taking down the whole page
  - post-release stabilization (2026-03-02): fixed `Open Studio` task selection race and stale DAG data replay under rapid task switching/deep-link navigation
  - post-release UX sync (2026-03-04): removed duplicated home changes panel and fixed immediate sidebar count refresh after commit/reject/undo
  - db safety sync (2026-03-04): direct restore is explicit overwrite-only and requires user confirmation
  - news sync (2026-03-08): global snapshot now includes `News Total`, home main row is rebalanced into `Task / Knowledge / News`, and `/news` supports single-day published-date filtering with `Today / Previous Day / Next Day` shortcuts
- Knowledge workspace using `/api/v1/knowledge`:
  - category model: `ops_manual | mechanism_spec | decision_record`
  - status model: `active | archived`
  - create/edit/archive/delete in UI
- Changes review page for proposal commit/reject and undo-last
- OpenClaw skill support for read/write governance path
- Additional read exposure for agent retrieval:
  - `GET /api/v1/tasks/{task_id}/sources`
  - `GET /api/v1/notes/{note_id}/sources`
  - `GET /api/v1/journals/{journal_date}/items`
  - `GET /api/v1/inbox`, `GET /api/v1/inbox/{inbox_id}`
  - `GET /api/v1/links`
- Idea route-node creation now only emits `goal` type for execution DAG initialization.

## Verification snapshot
- Backend:
  - `python3 -m pytest -q backend/tests`
- Frontend:
  - `cd frontend && npm run build`
- Skill:
  - `cd skills/memlineage && node --test index.test.js`

## Known gaps
- No SaaS multi-tenant auth/billing/OAuth yet
- No MCP server yet (REST + skill is current entry)
- Policy-based auto-approval is not implemented
