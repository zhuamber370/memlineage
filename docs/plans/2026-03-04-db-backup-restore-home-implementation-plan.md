# Home DB Backup/Restore Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Home-page database backup download and direct local-file restore (overwrite) flow.

**Architecture:** Keep backup/restore logic on backend with a new `DbBackupService` and expose two admin endpoints (`backup` download, `restore` upload). Use a deterministic zip-based backup package (`manifest.json + payload`) to support both SQLite and PostgreSQL. Frontend adds one Home card (`Database Safety`) with explicit danger UX and no server-side backup list.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy, Python stdlib (`zipfile`, `tempfile`, `subprocess`), Next.js App Router, React client state.

---

### Task 1: Add Backend API Contract Tests (Red)

**Files:**
- Create: `backend/tests/test_db_backup_api.py`
- Reference: `backend/tests/helpers.py`
- Reference: `backend/tests/test_skills_api.py` (monkeypatch style)

**Step 1: Write failing tests for backup package and restore workflow (SQLite runtime)**

```python
# backend/tests/test_db_backup_api.py
import io
import json
import zipfile

from tests.helpers import create_test_task, make_client


def _download_backup(client):
    resp = client.get("/api/v1/admin/db/backup")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/octet-stream"
    assert "attachment;" in resp.headers.get("content-disposition", "")
    return resp.content


def test_backup_download_contains_manifest_and_payload_sqlite():
    client = make_client()
    payload = _download_backup(client)
    zf = zipfile.ZipFile(io.BytesIO(payload))
    assert set(zf.namelist()) >= {"manifest.json", "payload.sqlite3"}
    manifest = json.loads(zf.read("manifest.json"))
    assert manifest["format"] == "memlineage-db-backup"
    assert manifest["backend"] == "sqlite"


def test_restore_overwrites_data_from_uploaded_backup_sqlite():
    client = make_client()
    original_task_id = create_test_task(client, prefix="restore_baseline")
    backup_blob = _download_backup(client)

    # mutate database after backup
    create_test_task(client, prefix="restore_after_backup")

    restore = client.post(
        "/api/v1/admin/db/restore",
        content=backup_blob,
        headers={"content-type": "application/octet-stream", "x-backup-filename": "baseline.mlbk"},
    )
    assert restore.status_code == 200, restore.text

    listed = client.get("/api/v1/tasks?page=1&page_size=200")
    assert listed.status_code == 200, listed.text
    ids = {item["id"] for item in listed.json()["items"]}
    assert original_task_id in ids
    assert not any(item_id.startswith("tsk_") and item_id not in ids for item_id in [])


def test_restore_rejects_invalid_backup_blob():
    client = make_client()
    resp = client.post(
        "/api/v1/admin/db/restore",
        content=b"not-a-zip",
        headers={"content-type": "application/octet-stream", "x-backup-filename": "bad.mlbk"},
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["error"]["code"] == "DB_BACKUP_INVALID"
```

**Step 2: Run tests to verify failure**

Run: `cd backend && python3 -m pytest -q tests/test_db_backup_api.py`
Expected: FAIL with `404` (route missing) or import errors for new service/schemas.

**Step 3: Commit test skeleton (optional if you prefer red+green in one commit)**

```bash
git add backend/tests/test_db_backup_api.py
git commit -m "test(db-backup): add failing api contract tests"
```

### Task 2: Implement Backend Backup/Restore Service + Routes (Green)

**Files:**
- Create: `backend/src/services/db_backup_service.py`
- Create: `backend/src/routes/db_admin.py`
- Modify: `backend/src/schemas.py`
- Modify: `backend/src/app.py`
- Modify: `backend/src/services/__init__.py` (if service export convention is used)

**Step 1: Add minimal schemas for response contract**

```python
# backend/src/schemas.py
class DbBackupOut(BaseModel):
    filename: str
    backend: Literal["sqlite", "postgres"]
    created_at: datetime


class DbRestoreOut(BaseModel):
    status: Literal["restored"]
    backend: Literal["sqlite", "postgres"]
    restored_at: datetime
```

**Step 2: Implement `DbBackupService` (zip package format)**

```python
# backend/src/services/db_backup_service.py
# package content:
# - manifest.json
# - payload.sqlite3 OR payload.pgdump
# manifest fields: format, version, backend, created_at, filename
```

Implementation requirements:
1. Detect backend using `settings.is_sqlite / settings.is_postgres`.
2. SQLite backup: read sqlite file bytes from resolved path.
3. PostgreSQL backup: run `pg_dump --format=custom --file <tmp>` with env password.
4. Build zip bytes in-memory (`.mlbk`), include manifest + payload.
5. Restore validates:
   - zip parse success
   - `manifest.format == "memlineage-db-backup"`
   - backend matches current runtime
6. SQLite restore:
   - `engine.dispose()` before writing file
   - atomically replace db file
7. PostgreSQL restore:
   - write payload to temp file
   - run `pg_restore --clean --if-exists --no-owner --no-privileges --dbname <dsn> <file>`
8. Raise `ValueError` codes:
   - `DB_BACKUP_INVALID`
   - `DB_BACKUP_BACKEND_MISMATCH`
   - `DB_BACKUP_TOOL_NOT_FOUND`
   - `DB_BACKUP_COMMAND_FAILED`

**Step 3: Add router and wire into app**

```python
# backend/src/routes/db_admin.py
@router.get("/admin/db/backup")
def download_backup(...):
    # return StreamingResponse with attachment filename *.mlbk

@router.post("/admin/db/restore", response_model=DbRestoreOut)
def restore_backup(request: Request, ...):
    # read raw bytes: await request.body() via async endpoint
```

Integration:
- `backend/src/app.py` include `build_db_admin_router(get_db_dep)`.

**Step 4: Map error codes to HTTP statuses**

- `DB_BACKUP_INVALID` -> 422
- `DB_BACKUP_BACKEND_MISMATCH` -> 409
- `DB_BACKUP_TOOL_NOT_FOUND` -> 500
- `DB_BACKUP_COMMAND_FAILED` -> 500

**Step 5: Run tests to verify pass**

Run: `cd backend && python3 -m pytest -q tests/test_db_backup_api.py`
Expected: PASS.

**Step 6: Commit**

```bash
git add backend/src/services/db_backup_service.py backend/src/routes/db_admin.py backend/src/schemas.py backend/src/app.py backend/tests/test_db_backup_api.py
git commit -m "feat(db): add backup download and restore overwrite apis"
```

### Task 3: Add PostgreSQL Command Path Tests (Red -> Green)

**Files:**
- Modify: `backend/tests/test_db_backup_api.py`
- Modify: `backend/src/services/db_backup_service.py`

**Step 1: Add failing tests for pg command invocation via monkeypatch**

```python
def test_postgres_backup_uses_pg_dump(monkeypatch):
    # monkeypatch Settings/env to postgres
    # monkeypatch subprocess.run and capture cmd
    # assert pg_dump called with custom format and output file


def test_postgres_restore_uses_pg_restore(monkeypatch):
    # feed valid .mlbk manifest backend=postgres + payload.pgdump
    # assert pg_restore called with --clean --if-exists
```

**Step 2: Run target tests and confirm fail first**

Run: `cd backend && python3 -m pytest -q tests/test_db_backup_api.py -k "pg_dump or pg_restore"`
Expected: FAIL until command builder is implemented.

**Step 3: Implement minimal command builder + secure env pass-through**

Requirements:
1. Isolate command construction in private helpers.
2. Do not log DB password.
3. Return non-zero command as `DB_BACKUP_COMMAND_FAILED`.

**Step 4: Re-run tests**

Run: `cd backend && python3 -m pytest -q tests/test_db_backup_api.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add backend/src/services/db_backup_service.py backend/tests/test_db_backup_api.py
git commit -m "test(db): cover postgres backup restore command paths"
```

### Task 4: Add Home `Database Safety` Card UI

**Files:**
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/i18n.tsx`
- Modify: `frontend/app/globals.css`

**Step 1: Add frontend API helpers**

```ts
// frontend/src/lib/api.ts
export async function downloadDbBackup(): Promise<{ blob: Blob; filename: string }> { ... }
export async function restoreDbBackup(file: File): Promise<{ status: "restored"; backend: "sqlite" | "postgres"; restored_at: string }> { ... }
```

Rules:
1. `downloadDbBackup` uses `GET /api/v1/admin/db/backup`.
2. Parse `content-disposition` for filename fallback `memlineage-backup.mlbk`.
3. `restoreDbBackup` posts raw bytes (`application/octet-stream`) with `x-backup-filename` header.

**Step 2: Extend Home page state + UI section**

Add local states:
- backup: `idle | running | success | error`
- restore: `file`, `ack`, `running`, `notice`, `error`

Add section below current boards:
- left block: backup action
- right block: restore picker + ack + danger action

Behavior constraints:
1. Restore button disabled until file selected and ack true.
2. `window.confirm(...)` required before calling restore API.
3. Show per-block inline status and error messages.

**Step 3: Add i18n keys (EN/ZH)**

Add all keys from design doc section 7 in both dictionaries.

**Step 4: Add card styles**

- New classes: `.homeDbSafety`, `.homeDbSafetyGrid`, `.homeDbBlock`, `.homeDbWarn`, `.homeDbFileMeta`, `.homeDbDangerButton`
- Responsive: collapse to single column at existing mobile breakpoint.

**Step 5: Validate frontend build**

Run: `cd frontend && npm run build`
Expected: PASS.

**Step 6: Commit**

```bash
git add frontend/app/page.tsx frontend/src/lib/api.ts frontend/src/i18n.tsx frontend/app/globals.css
git commit -m "feat(frontend): add home database backup restore safety card"
```

### Task 5: Docs + Final Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/reports/mvp-release-notes.md`
- Modify: `docs/reports/2026-03-01-home-dashboard-changelog.md`

**Step 1: Sync docs for new Home capability**

Required doc updates:
1. Mention Home `Database Safety` card.
2. Clarify backup is download-only and restore is local upload overwrite.
3. Add operator warning copy in release notes.

**Step 2: Run full verification set**

Run:
```bash
cd backend && python3 -m pytest -q tests/test_db_backup_api.py
cd frontend && npm run build
```

Expected:
- backend tests PASS
- frontend build PASS

**Step 3: Commit docs + verification-ready state**

```bash
git add README.md docs/reports/mvp-release-notes.md docs/reports/2026-03-01-home-dashboard-changelog.md
git commit -m "docs: sync home db backup restore feature notes"
```

### Task 6: Final Integration Commit (Optional Squash by Team Policy)

**Files:**
- No additional file changes required if prior commits are clean.

**Step 1: Inspect history and working tree**

Run:
```bash
git status --short
git log --oneline -n 8
```

Expected:
- clean working tree
- task-scoped commits present

**Step 2: Push branch**

Run:
```bash
git push -u origin <feature-branch>
```

**Step 3: Manual sanity checks (UI)**

1. Open `/` Home page.
2. Click `Create Backup & Download` and confirm `.mlbk` download.
3. Select that file in restore block.
4. Check ack checkbox and confirm restore.
5. Confirm success notice appears and app remains usable.

---

## Implementation Notes

- Keep API local-host only semantics consistent with existing skill-management wording.
- Do not add remote upload/telemetry for backup payloads.
- Preserve existing Home dashboard layout hierarchy; add `Database Safety` as one additional card section.
- Prefer explicit error codes over generic messages for operational actions.

## Risk Controls

1. Destructive restore: protected by checkbox + confirm dialog + danger styling.
2. Tooling dependency for PostgreSQL (`pg_dump`/`pg_restore`): surfaced with actionable backend error code.
3. Invalid file upload: reject with clear `DB_BACKUP_INVALID` contract.

## Ready-to-Execute Command

```bash
使用 superpowers:executing-plans 技能，严格按计划逐任务执行：
/Users/celastin/Desktop/projects/memlineage/docs/plans/2026-03-04-db-backup-restore-home-implementation-plan.md
```
