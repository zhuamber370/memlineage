# 2026-03-01 Home Dashboard Changelog

## Delivered Scope
- Added the home dashboard route `/`, replacing the previous direct redirect to `/tasks`.
- Delivered four sections on the home page:
  - Global Snapshot
  - Task Board (metrics + focus tasks)
  - Changes Board (proposed count + recent proposals)
  - Knowledge Board (total/category stats + recent updates)
- Added aggregation layer: `frontend/src/lib/home-dashboard.ts`.
- Added `Home` navigation entry and completed localized copy for loading/error/empty states.
- Added deep-link filter hydration:
  - `/tasks`: `status/priority/topic_id/workspace/task_id`
  - `/knowledge`: `status/category`
  - `/changes`: `status`
- Improved resilience:
  - Independent loading and error isolation for tasks/knowledge/changes
  - A single API failure no longer blanks the entire page

## Navigation Strategy
- Global cards jump with actionable filters:
  - Task overview -> `/tasks`
  - In-progress tasks -> `/tasks?status=in_progress`
  - In-progress P0 tasks -> `/tasks?status=in_progress&priority=P0`
  - Pending changes -> `/changes?status=proposed`
  - Knowledge overview -> `/knowledge?status=active`
- Focus task action loop:
  - Open task -> `/tasks?status=in_progress&priority=P0|...&task_id=<id>`
  - Enter execution workspace -> `/tasks?status=in_progress&workspace=studio&task_id=<id>`

## Verification Commands Executed
- Task 1 failure check:
  - `cd frontend && npm run dev` + `curl -I http://127.0.0.1:3000/` (confirmed `307 Location: /tasks` before implementation)
- Task 2 failure check:
  - `cd frontend && npm run build` (before aggregation layer: `Module not found`)
- Task 1-6 verification after each task:
  - `cd frontend && npm run build` (all passed)
- Task 7 documentation baseline check:
  - `rg -n "home dashboard" docs/reports -S` (no complete entry before update)
- Task 7 documentation diff check:
  - `git diff -- docs/reports`

## 2026-03-02 Stability Fixes (Post-Acceptance)
- Fixed intermittent `Open Studio` mismatch where URL `task_id` changed but old task detail remained visible.
- Fixed stale request write-back in `TaskExecutionPanel` during task switching to prevent DAG/log data mixing.
- Fixed list group ordering for multi-status display: `in_progress -> todo -> done -> cancelled`.
- Removed temporary `test://` tasks created during debugging and restored clean runtime data.
- Validation:
  - `cd frontend && npm run build` (PASS)
  - Playwright deep-link and list-click regression: switching between different `task_id` consistently opens the correct task detail (PASS)

## 2026-03-04 Home + Changes UX Sync
- Home dashboard layout was rebalanced:
  - Global snapshot expanded as a full-width top panel
  - Task board and Knowledge board aligned into a denser two-column working area
- Removed the home `Changes Board` section to reduce duplication and visual scatter.
- Added left-sidebar `Changes` reminder badge with pending `proposed` count.
- Fixed stale sidebar reminder updates by introducing event-driven refresh from `/changes` actions:
  - `commit/reject/undo/refresh` now dispatch a refresh signal
  - sidebar count updates immediately instead of waiting for polling interval
- Validation:
  - `cd frontend && npm run build` (PASS)
  - manual/Playwright interaction check: count changes instantly after commit/reject (PASS)

## Commit History
- `6597d5f` feat(frontend): scaffold home dashboard route and nav entry
- `5fedd5f` feat(frontend): add home dashboard aggregation and focus ranking helpers
- `d4d2e69` feat(frontend): implement home dashboard sections and localized copy
- `7ff1cbe` feat(frontend): enforce deterministic focus task ordering and actions
- `bebcd80` feat(frontend): support query-driven filter hydration for dashboard deep links
- `34f1ddc` fix(frontend): harden home dashboard loading error and empty states
- `14fdcaa` fix: tasks studio selection race and stale graph state
