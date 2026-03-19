> Documentation Status: Confirmed Design
> Last synced: 2026-03-19

# Current Documentation Sync Design

Date: 2026-03-19
Status: Confirmed
Scope: current outward-facing project documentation only

## 1. Context

The repository contains multiple documentation layers:

1. Current outward-facing docs used by users and contributors.
2. Historical design and planning artifacts in `docs/plans/`.
3. Historical changelogs and release records in `docs/reports/`.
4. Third-party package docs under `frontend/node_modules/`.

The user confirmed that this sync should follow option 1:
update only the current outward-facing docs so they match the current codebase and current product positioning.

## 2. In-Scope Files

Primary scope:

- `README.md`
- `INTEGRATION.md`
- `backend/README.md`
- `frontend/README.md`
- `docs/README.md`
- `docs/contributing/dev-setup.md`
- `docs/guides/agent-api-surface.md`
- `docs/guides/safe-to-write-checklist.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `skill/README.md`
- `skills/memlineage/SKILL.md`
- `docs/proof/README.md` when needed for consistency

## 3. Out-of-Scope Files

Do not rewrite these to present-day wording:

- `docs/plans/*`
- `docs/reports/*`
- raw proof artifacts such as `docs/proof/*.json`
- third-party docs under `frontend/node_modules/*`

These files may intentionally reflect historical states.

## 4. Current Product Truth To Preserve

The synced docs must reflect the current repository state:

1. MemLineage is positioned as a shared workspace for solo developers working with agents.
2. The main current product emphasis is `tasks + knowledge`.
3. Humans use the web UI directly; agents use the bundled skill against the same backend.
4. Agent-originated writes can go through `dry-run -> diff -> review -> commit -> undo`.
5. Current web surfaces include `/`, `/tasks`, `/knowledge`, `/news`, `/changes`, and `/skills`.
6. Current integration targets are Codex and OpenClaw.

## 5. Expected Corrections

Likely corrections during this sync:

1. Remove older positioning such as "governed memory layer" and "workflow command center" from current docs.
2. Update frontend route/page documentation to include current pages.
3. Update current API guidance to include current read domains such as news.
4. Replace user-facing "todo" wording with "task" where the underlying contract does not require the literal API/action name.
5. Keep literal API enums or action IDs unchanged where they are part of the real runtime contract.

## 6. Success Criteria

This sync succeeds if:

1. Current docs describe the present product accurately.
2. Historical docs remain untouched.
3. User-facing terminology is consistent with the current positioning.
4. Contract docs preserve actual runtime names where those names are part of the interface.
