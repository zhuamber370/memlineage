# Frontend

Next.js frontend for MemLineage.
Use this file as the source of truth for local frontend setup and the current web routes.

## Environment

Frontend reads from `frontend/.env.local`:
- `NEXT_PUBLIC_API_BASE` (e.g. `http://127.0.0.1:8000`)
- `NEXT_PUBLIC_API_KEY`

Recommended sync from root:

```bash
cd frontend
cp ../.env .env.local
```

## Run

```bash
cd frontend
npm install
npm run dev
```

Build check:

```bash
npm run build
```

## Current Routes (Synced 2026-03-19)

- `/`
  - Home dashboard
  - Task / knowledge / news / changes snapshot cards
  - Database Safety panel for local backup download and direct restore

- `/tasks`
  - Task workspace with `manage` and `studio` modes
  - Search / filter / list / detail in one layout
  - Bulk update, reopen, delete, and archive flows
  - Route canvas with node `...` operations:
    - `+ Add Step`
    - `Set Status` (`waiting / execute / done`)
    - `Rename`
    - `Delete` (leaf node only)
  - Node logs and execution inspector in the studio panel

- `/knowledge`
  - Knowledge CRUD workspace backed by `/api/v1/knowledge`
  - List + detail split view
  - Filters:
    - status (`active | archived`)
    - category (`ops_manual | mechanism_spec | decision_record`)
    - keyword search (`q`)
  - Create supports category `auto` inference or explicit category
  - Detail supports edit/archive/delete

- `/changes`
  - Proposal review (diff + summary)
  - Commit / reject and undo-last operations
  - Applied-event timeline for committed changes

- `/news`
  - Structured news workspace
  - Search / filter by status and published day
  - Detail editing, archive, and delete flows

- `/skills`
  - Local runtime management for MemLineage skills
  - Supports `openclaw` and `codex`
  - Detect, configure path, install, uninstall, enable, disable, update, and health-check flows

## Task-scoped helper pages

- `/ideas?task_id=<task_id>`

This page requires task context and is not default top-level navigation.

Legacy route note:
- `/audit` currently redirects to `/tasks`
