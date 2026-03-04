import io
import json
import zipfile
from pathlib import Path

import pytest

from tests.helpers import create_test_task, make_client


@pytest.fixture
def isolated_db_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "backup_restore.sqlite3"
    monkeypatch.setenv("AFKMS_DATABASE_URL", f"sqlite:///{db_path}")
    return {"db_path": db_path}


def _list_task_ids(client) -> set[str]:
    listed = client.get("/api/v1/tasks?page=1&page_size=100")
    assert listed.status_code == 200, listed.text
    return {item["id"] for item in listed.json()["items"]}


def _download_backup(client) -> bytes:
    resp = client.get("/api/v1/admin/db/backup")
    assert resp.status_code == 200, resp.text
    assert resp.headers.get("content-type", "").startswith("application/octet-stream")
    disposition = resp.headers.get("content-disposition", "")
    assert "attachment;" in disposition
    assert ".mlbk" in disposition
    return resp.content


def test_backup_download_contains_manifest_and_payload_sqlite(isolated_db_env):
    client = make_client()

    payload = _download_backup(client)
    archive = zipfile.ZipFile(io.BytesIO(payload))
    names = set(archive.namelist())
    assert "manifest.json" in names
    assert "payload.sqlite3" in names

    manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
    assert manifest["format"] == "memlineage-db-backup"
    assert manifest["version"] == 1
    assert manifest["backend"] == "sqlite"


def test_restore_overwrites_data_from_uploaded_backup_sqlite(isolated_db_env):
    client = make_client()

    baseline_task_id = create_test_task(client, prefix="restore_baseline")
    backup_blob = _download_backup(client)

    extra_task_id = create_test_task(client, prefix="restore_after_backup")
    before_restore_ids = _list_task_ids(client)
    assert baseline_task_id in before_restore_ids
    assert extra_task_id in before_restore_ids

    restore = client.post(
        "/api/v1/admin/db/restore",
        content=backup_blob,
        headers={
            "content-type": "application/octet-stream",
            "x-backup-filename": "baseline.mlbk",
        },
    )
    assert restore.status_code == 200, restore.text
    restored = restore.json()
    assert restored["status"] == "restored"
    assert restored["backend"] == "sqlite"
    assert restored["restored_at"]

    after_restore_ids = _list_task_ids(client)
    assert baseline_task_id in after_restore_ids
    assert extra_task_id not in after_restore_ids


def test_restore_rejects_invalid_backup_blob(isolated_db_env):
    client = make_client()

    resp = client.post(
        "/api/v1/admin/db/restore",
        content=b"not-a-zip",
        headers={
            "content-type": "application/octet-stream",
            "x-backup-filename": "bad.mlbk",
        },
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["error"]["code"] == "DB_BACKUP_INVALID"
