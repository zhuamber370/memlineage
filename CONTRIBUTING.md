# Contributing

Thanks for contributing to **MemLineage**.

MemLineage is a shared workspace for solo developers working with agents. Humans use the web UI directly, while agents access the same backend through skills. Contributions that improve task and knowledge workflows, skill integration, write safety, and contributor experience are especially welcome.
This file is the quickest path to where contributions are most useful right now.

## Quick start for contributors

If you want to contribute but feel blocked, comment on the relevant issue — maintainers can point you to the best starting files / components.

1) Read the dev setup guide: `docs/contributing/dev-setup.md`

2) Run the stack locally:
- Backend: `backend/README.md`
- Frontend: `frontend/README.md`

3) Pick a task:
- Look for issues labeled **good first issue** / **help wanted**.
- If you're not sure where to start, open an issue with your background (backend/frontend/full-stack) and we’ll point you to a small, high-signal change.

## Where help is most valuable (early stage)

- **Tasks workspace** (`/tasks`): CRUD, batch operations, route graph, status, inspector UX
- **Knowledge workspace** (`/knowledge`): CRUD, filters, category/status lifecycle
- **Skill integration** (`/skills` + runtime bundle): install/detect/update flows for Codex and OpenClaw
- **Governed write pipeline**: dry-run → commit/reject → undo-last
- **Changes review UX** (`/changes`): diff readability, safety checks, undo clarity
- **Docs**: API surface accuracy, onboarding guides, screenshots using synthetic test data

## Before opening a PR

- For non-trivial changes: open an issue first to align on scope.
- Keep diffs small and focused.
- Do not include secrets (`.env`, tokens, private keys).
- Keep runtime docs in sync with code (README/docs).
- If tests insert data, clean test data before merge.

## Local checks

### Backend

```bash
cd backend
python3 -m pytest -q
python3 scripts/cleanup_test_data.py
```

### Frontend

```bash
cd frontend
npm run build
```

## PR expectations

Please include:
- What changed + why
- How you verified (commands + results)
- Screenshots for UI changes
- Any doc updates (if behavior changed)
