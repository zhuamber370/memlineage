# README Repositioning Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to execute this plan task by task.

**Goal:** Rewrite the top-level README so MemLineage is presented as a shared workspace for solo developers working with agents, grounded in the current codebase.

**Architecture:** Keep the existing quickstart and integration utility, but replace the top-level product story. Center the README on human Web CRUD plus agent skill access to the same data, with tasks and knowledge as the primary scope and governance/runtime tooling as supporting capabilities.

**Tech Stack:** Markdown, existing repository docs, current frontend routes, current backend API surface, bundled MemLineage skill for Codex/OpenClaw

---

### Task 1: Reconfirm Product Scope From Code

**Files:**
- Modify: `README.md`
- Reference: `backend/README.md`
- Reference: `frontend/README.md`
- Reference: `frontend/app/page.tsx`
- Reference: `frontend/app/tasks/page.tsx`
- Reference: `frontend/app/knowledge/page.tsx`
- Reference: `frontend/app/changes/page.tsx`
- Reference: `frontend/app/skills/page.tsx`

**Step 1: Re-read the current product surfaces**

Run:

```bash
rg -n "href: \"/|/api/v1/tasks|/api/v1/knowledge|/api/v1/changes|/api/v1/skills" frontend/src/components/shell.tsx frontend/app backend/src/routes
```

Expected:
- Current routes and API domains confirm what the README can safely claim.

**Step 2: Capture the stable scope**

Confirm the README will foreground:
- `tasks`
- `knowledge`

Confirm the README will keep as secondary:
- `changes`
- `skills`
- home dashboard / DB safety

### Task 2: Replace the Top-Level Product Story

**Files:**
- Modify: `README.md`

**Step 1: Rewrite the opening section**

Replace the current "agent-heavy control layer" framing with:
- solo developer audience
- shared workspace for humans and agents
- human via Web, agent via skill
- simple CRUD outside chat
- lower token usage

**Step 2: Add a focused "Why this exists" section**

Cover:
- simple edits are too expensive through chat
- chat is poor for browsing/editing operational data
- structured shared context is easier to maintain in a UI

**Step 3: Add a "What you can do today" section**

Limit the main product story to current code:
- manage tasks
- maintain knowledge
- review proposed agent writes
- manage local skill runtimes
- monitor the workspace from home

### Task 3: Rebuild the README Structure Around Current UX

**Files:**
- Modify: `README.md`

**Step 1: Keep current quickstart utility**

Retain:
- clone
- env setup
- backend run
- frontend run
- verification URLs

**Step 2: Reframe integrations**

Keep Codex/OpenClaw instructions, but move them under a collaboration model:
- connect your agent after the app is running
- mention `/skills` first
- retain install script fallbacks

**Step 3: Keep examples concise**

Add a few natural-language examples that match the current skill contract:
- read tasks
- read knowledge
- propose a task change
- propose a knowledge change

### Task 4: Align Supporting Sections

**Files:**
- Modify: `README.md`

**Step 1: Remove stale release-changelog positioning from the top-level README**

Do not use the README as the primary release note.
Prefer durable product explanation over version-specific narrative.

**Step 2: Keep doc links and repo essentials**

Retain links for:
- integration guide
- backend/frontend docs
- docs index
- contributing
- security
- license

### Task 5: Verify the Rewrite Against the Repository

**Files:**
- Modify: `README.md`

**Step 1: Read the final README**

Run:

```bash
sed -n '1,260p' README.md
```

Expected:
- Opening sections match the confirmed positioning.
- Current code-backed pages and flows are described accurately.

**Step 2: Check git diff**

Run:

```bash
git diff -- README.md docs/plans/2026-03-19-readme-reposition-design.md docs/plans/2026-03-19-readme-reposition-implementation-plan.md
```

Expected:
- Diff shows only the README rewrite plus the two plan documents.
