# Home Dashboard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to execute this plan task by task.

## Goal
Add a home dashboard for individual users that aggregates `Tasks / Knowledge / Changes` and provides actionable entry points.

## Architecture
Implement a client page in `frontend/app/page.tsx`. Reuse existing REST APIs (`/tasks`, `/knowledge`, `/changes`) and perform lightweight aggregation in frontend code. The Task Board combines summary metrics and a focus-task list (prioritizing `P0 + in_progress`). Dashboard cards deep-link into destination pages with URL query filters.

## Tech Stack
- Next.js 14 (App Router)
- React 18
- TypeScript
- Existing REST wrappers (`apiGet`)
- Existing i18n dictionary

---

## Task 1: Home Route and Navigation Entry

**Files**
- `frontend/app/page.tsx`
- `frontend/src/components/shell.tsx`
- `frontend/src/i18n.tsx`

**Failing check (baseline)**
- Run: `cd frontend && npm run dev`
- Open `/` and confirm it currently redirects to `/tasks`.

**Implementation**
1. Replace redirect in `app/page.tsx` with a `HomeDashboardPage` client page (initial scaffold).
2. Add Home nav item in `shell.tsx`: `{ href: "/", key: "nav.home" }`.
3. Add minimal i18n keys:
   - `nav.home`
   - `home.title`
   - `home.subtitle`

**Verification**
- Run: `cd frontend && npm run build`
- Expected: PASS.

---

## Task 2: Aggregation Layer (Task/Knowledge/Changes)

**Files**
- `frontend/src/lib/home-dashboard.ts` (new)
- `frontend/app/page.tsx`

**Failing check (baseline)**
- Reference a non-existing aggregation function and run build to confirm failure.

**Implementation**
1. Add typed snapshot aggregators in `home-dashboard.ts`.
2. Add deterministic focus-task sorting helper.
3. Move data aggregation out of JSX and into shared helpers.

**Verification**
- Run: `cd frontend && npm run build`
- Expected: PASS.

---

## Task 3: Home Dashboard UI Sections

**Files**
- `frontend/app/page.tsx`
- `frontend/app/globals.css`
- `frontend/src/i18n.tsx`

**Implementation**
1. Render four sections:
   - Global Snapshot
   - Task Board (summary + focus <= 5)
   - Changes Board (proposed + latest 3)
   - Knowledge Board (counts + latest 5)
2. Add i18n keys:
   - `home.global.*`
   - `home.tasks.*`
   - `home.changes.*`
   - `home.knowledge.*`
   - `home.loading`, `home.empty`, `home.error`
3. Keep style aligned with existing visual language.

**Verification**
- Run: `cd frontend && npm run build`
- Expected: PASS.

---

## Task 4: Focus Task Ranking and Action Links

**Files**
- `frontend/src/lib/home-dashboard.ts`
- `frontend/app/page.tsx`

**Implementation**
1. Enforce deterministic ranking:
   - `priority === P0 && status === in_progress`
   - then `status === in_progress` with nearest `due`
   - then latest `updated_at`
   - then `title` as tie-break
2. Display focus task actions:
   - open task
   - enter execution workspace

**Verification**
- Run: `cd frontend && npm run build`
- Expected: PASS.

---

## Task 5: Deep-Link Filter Hydration on Destination Pages

**Files**
- `frontend/app/tasks/page.tsx`
- `frontend/app/knowledge/page.tsx`
- optional: `frontend/app/changes/page.tsx`

**Implementation**
1. On mount, parse `URLSearchParams` and hydrate filter state using a whitelist.
2. Support dashboard deep links:
   - `/tasks?status=...&priority=...&topic_id=...&workspace=...&task_id=...`
   - `/knowledge?status=...&category=...`
   - `/changes?status=...`

**Verification**
- Run: `cd frontend && npm run build`
- Manually open deep-link URLs and verify filters are applied.

---

## Task 6: Error/Empty-State Isolation and Guardrails

**Files**
- `frontend/app/page.tsx`
- `frontend/src/lib/home-dashboard.ts`

**Implementation**
1. Isolate loading/error/empty states per board.
2. Add defensive defaults for missing fields.
3. Enforce item caps on each board for predictable rendering.

**Verification**
- Run: `cd frontend && npm run build`
- Simulate one API failure and verify the page remains partially functional.

---

## Task 7: Documentation and Acceptance Record

**Files**
- `docs/reports/mvp-release-notes.md`
- `docs/reports/2026-03-01-home-dashboard-changelog.md` (new/update)

**Implementation**
1. Add delivered scope and navigation behavior.
2. Record validation commands and post-release fixes.

**Verification**
- Run: `rg -n "home dashboard" docs/reports -S`
- Ensure docs are complete and discoverable.

---

## Global Verification
1. Frontend build:
   - `cd frontend && npm run build`
2. Backend regression guard:
   - `cd backend && python3 -m pytest -q`
3. Manual UX checks:
   - `/` shows all four dashboard sections
   - focus ranking is deterministic
   - dashboard links hydrate destination filters
   - localization has no mixed-language regressions

## Engineering Constraints
1. Keep aggregation/ranking logic centralized in `src/lib/home-dashboard.ts`.
2. Reuse existing APIs (no new backend endpoint for V1).
3. Keep visible copy fully i18n-driven.
4. Verify each task before commit.

## Suggested Skills
- `verification-before-completion`
- `requesting-code-review`
