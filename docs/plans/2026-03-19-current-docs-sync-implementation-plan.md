# Current Documentation Sync Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task by task.

**Goal:** Bring current outward-facing project documentation in sync with the present codebase and current product positioning, without rewriting historical plans or release records.

**Architecture:** Audit the current docs set against the current frontend routes, backend API surface, and skill contract. Update only the docs that represent current behavior, preserving historical artifacts untouched. Keep literal runtime identifiers when they are part of the public contract.

**Tech Stack:** Markdown, current repository docs, FastAPI route definitions, Next.js route files, bundled MemLineage skill docs

---

### Task 1: Confirm Scope and Audit Targets

**Files:**
- Modify: `docs/plans/2026-03-19-current-docs-sync-design.md`
- Modify: `docs/plans/2026-03-19-current-docs-sync-implementation-plan.md`
- Reference: `README.md`
- Reference: `INTEGRATION.md`
- Reference: `backend/README.md`
- Reference: `frontend/README.md`
- Reference: `docs/README.md`
- Reference: `docs/guides/agent-api-surface.md`
- Reference: `CONTRIBUTING.md`
- Reference: `skills/memlineage/SKILL.md`

**Step 1: Enumerate in-scope files**

Run:

```bash
find . -type f \( -name '*.md' -o -name '*.MD' -o -name '*.mdx' \) | sed 's#^./##' | sort
```

Expected:
- Clear split between current docs and historical or third-party docs.

**Step 2: Lock the excluded classes**

Exclude:
- `docs/plans/*` except the new sync docs
- `docs/reports/*`
- `frontend/node_modules/*`

### Task 2: Audit Current Product and Runtime Truth

**Files:**
- Reference: `frontend/src/components/shell.tsx`
- Reference: `frontend/app/page.tsx`
- Reference: `frontend/app/tasks/page.tsx`
- Reference: `frontend/app/knowledge/page.tsx`
- Reference: `frontend/app/news/page.tsx`
- Reference: `frontend/app/changes/page.tsx`
- Reference: `frontend/app/skills/page.tsx`
- Reference: `backend/README.md`
- Reference: `backend/src/routes/*.py`

**Step 1: Verify current routes and pages**

Run:

```bash
find frontend/app -maxdepth 2 -name 'page.tsx' | sort
```

Expected:
- Current frontend pages are visible and can be reflected in docs.

**Step 2: Verify current API surface**

Run:

```bash
rg -n "@router\\.(get|post|patch|delete|put)" backend/src/routes
```

Expected:
- Current API docs can be checked against real route definitions.

### Task 3: Rewrite Outdated Current Docs

**Files:**
- Modify: `INTEGRATION.md`
- Modify: `frontend/README.md`
- Modify: `docs/guides/agent-api-surface.md`
- Modify: `CONTRIBUTING.md`
- Modify: `skills/memlineage/SKILL.md`
- Modify: other in-scope docs only if the audit finds a concrete mismatch

**Step 1: Update product positioning docs**

Correct older phrases that no longer match the current README direction.

**Step 2: Update route and feature docs**

Ensure frontend and integration docs reflect:
- current main routes
- current skill-management flow
- current tasks/knowledge emphasis

**Step 3: Update terminology**

Use `task` in user-facing wording where possible.
Preserve literal names such as `status: "todo"` or `propose_record_todo` when they are actual interface names.

### Task 4: Verify Final Consistency

**Files:**
- Modify: current synced docs only

**Step 1: Re-read changed docs**

Run:

```bash
sed -n '1,260p' README.md
sed -n '1,260p' INTEGRATION.md
sed -n '1,260p' frontend/README.md
sed -n '1,260p' docs/guides/agent-api-surface.md
sed -n '1,260p' CONTRIBUTING.md
sed -n '1,320p' skills/memlineage/SKILL.md
```

Expected:
- Product story and runtime details align with the current repo.

**Step 2: Check diff scope**

Run:

```bash
git diff -- README.md INTEGRATION.md frontend/README.md docs/README.md docs/contributing/dev-setup.md docs/guides/agent-api-surface.md docs/guides/safe-to-write-checklist.md CONTRIBUTING.md SECURITY.md skill/README.md skills/memlineage/SKILL.md docs/proof/README.md docs/plans/2026-03-19-current-docs-sync-design.md docs/plans/2026-03-19-current-docs-sync-implementation-plan.md
```

Expected:
- Only current docs and the new sync docs changed.
