# Current Docs Tone Harmonization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Harmonize the tone and structure of current outward-facing documentation so top-level docs are more product-facing, runtime docs remain technical, and index docs stay neutral.

**Architecture:** Keep the current factual sync intact. Apply a layered writing model: product voice at the entry points, technical voice in runtime and contract docs, and concise navigation voice in indexes. Avoid touching historical reports or plans.

**Tech Stack:** Markdown, current repository docs, existing product positioning, current route and API references

---

### Task 1: Reconfirm Current Doc Groups

**Files:**
- Modify: `docs/plans/2026-03-19-docs-tone-harmonization-design.md`
- Modify: `docs/plans/2026-03-19-docs-tone-harmonization-implementation-plan.md`
- Reference: `README.md`
- Reference: `INTEGRATION.md`
- Reference: `backend/README.md`
- Reference: `frontend/README.md`
- Reference: `docs/README.md`
- Reference: `CONTRIBUTING.md`
- Reference: `skills/memlineage/SKILL.md`

**Step 1: Read representative docs**

Run:

```bash
sed -n '1,220p' README.md
sed -n '1,220p' INTEGRATION.md
sed -n '1,220p' backend/README.md
sed -n '1,220p' frontend/README.md
sed -n '1,220p' docs/README.md
sed -n '1,220p' CONTRIBUTING.md
```

Expected:
- Tone differences are visible and can be normalized by document type.

### Task 2: Improve Product-Facing Docs

**Files:**
- Modify: `README.md`
- Modify: `INTEGRATION.md`
- Modify: `CONTRIBUTING.md`

**Step 1: Tighten lead paragraphs**

Make the first paragraphs answer:
- what this is
- who it is for
- why it exists

**Step 2: Keep sections practical**

Preserve current factual content, but make section flow feel more product-oriented and readable.

### Task 3: Improve Runtime / Contract Docs

**Files:**
- Modify: `backend/README.md`
- Modify: `frontend/README.md`
- Modify: `docs/contributing/dev-setup.md`
- Modify: `docs/guides/agent-api-surface.md`
- Modify: `docs/guides/safe-to-write-checklist.md`
- Modify: `skills/memlineage/SKILL.md`

**Step 1: Add explicit purpose statements**

Each file should make it obvious whether it is:
- runtime reference
- setup guide
- contract document
- operational checklist

**Step 2: Keep contract names literal**

Do not rename enums or action IDs that are real runtime interfaces.

### Task 4: Improve Neutral Index Docs

**Files:**
- Modify: `docs/README.md`
- Modify: `skill/README.md`

**Step 1: Shorten and clarify**

Make it easy to understand:
- what this doc is for
- which other file is the source of truth

### Task 5: Verify Tone and Scope

**Files:**
- Modify: current outward-facing docs only

**Step 1: Read changed docs**

Run:

```bash
sed -n '1,220p' README.md
sed -n '1,220p' INTEGRATION.md
sed -n '1,220p' backend/README.md
sed -n '1,220p' frontend/README.md
sed -n '1,220p' docs/README.md
sed -n '1,220p' CONTRIBUTING.md
sed -n '1,260p' docs/guides/agent-api-surface.md
sed -n '1,320p' skills/memlineage/SKILL.md
```

Expected:
- Entry docs sound product-facing.
- Runtime docs sound technical.
- Index docs sound neutral.

**Step 2: Check diff scope**

Run:

```bash
git diff -- README.md INTEGRATION.md backend/README.md frontend/README.md docs/README.md docs/contributing/dev-setup.md docs/guides/agent-api-surface.md docs/guides/safe-to-write-checklist.md CONTRIBUTING.md skill/README.md skills/memlineage/SKILL.md docs/plans/2026-03-19-docs-tone-harmonization-design.md docs/plans/2026-03-19-docs-tone-harmonization-implementation-plan.md
```

Expected:
- Only current docs and the new tone-plan docs changed.
