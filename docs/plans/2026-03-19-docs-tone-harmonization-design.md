> Documentation Status: Confirmed Design
> Last synced: 2026-03-19

# Current Docs Tone Harmonization Design

Date: 2026-03-19
Status: Confirmed
Scope: current outward-facing documentation only

## 1. Goal

Unify the tone of current project documentation without changing the factual scope established in the prior sync.

The confirmed direction is:

- top-level docs feel product-facing
- runtime and contract docs stay technical
- index docs stay neutral and navigational

## 2. Tone Model

### A. Product-facing docs

Files:

- `README.md`
- `INTEGRATION.md`
- `CONTRIBUTING.md`

Tone:

- explain what the product is, who it is for, and why it matters
- use plain language before technical detail
- keep sections easy to scan
- avoid hype and avoid stale platform-centric framing

### B. Runtime / contract docs

Files:

- `backend/README.md`
- `frontend/README.md`
- `docs/contributing/dev-setup.md`
- `docs/guides/agent-api-surface.md`
- `docs/guides/safe-to-write-checklist.md`
- `skills/memlineage/SKILL.md`

Tone:

- direct, explicit, implementation-oriented
- emphasize boundaries, commands, routes, API names, and invariants
- minimize product storytelling
- preserve literal runtime identifiers where they are part of the contract

### C. Neutral index/reference docs

Files:

- `docs/README.md`
- `skill/README.md`

Tone:

- concise and navigational
- explain how to find the right source of truth
- avoid both product prose and low-level implementation detail where unnecessary

## 3. Shared Style Rules

Across the current docs set:

1. Prefer short lead paragraphs that explain purpose before detail.
2. Prefer consistent vocabulary:
   - `shared workspace`
   - `web UI`
   - `skill`
   - `agent-originated writes`
   - `task`
3. Use `todo` only when referring to literal runtime enums or action names.
4. Keep headings functional and predictable.
5. Reduce duplicated explanation when another current doc is the better source of truth.

## 4. Structural Rules

Where it fits, current docs should follow:

1. purpose
2. current scope
3. usage or command path
4. references

Not every file needs every section, but the order should feel consistent.

## 5. Non-Goals

This pass does not:

- change product scope
- change historical plan/report wording
- rewrite proof artifacts
- change API behavior or skill behavior

## 6. Success Criteria

This pass succeeds if:

1. Entry docs feel like they belong to the same product.
2. Runtime docs read like source-of-truth technical references.
3. Navigational docs are shorter and clearer.
4. No current doc drifts away from the actual codebase.
