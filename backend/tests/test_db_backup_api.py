import io
import json
import re
import zipfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from src.services.db_backup_service import DbBackupService
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


class _FakeSession:
    def __init__(self, engine):
        self._engine = engine

    def get_bind(self):
        return self._engine

    def close(self):
        return None


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


def test_backup_download_exposes_timestamped_filename_for_browser_fetch(isolated_db_env):
    client = make_client()

    resp = client.get("/api/v1/admin/db/backup", headers={"origin": "http://localhost:3000"})
    assert resp.status_code == 200, resp.text

    expose_headers = resp.headers.get("access-control-expose-headers", "")
    exposed = {part.strip().lower() for part in expose_headers.split(",") if part.strip()}
    assert "content-disposition" in exposed

    disposition = resp.headers.get("content-disposition", "")
    match = re.search(r'filename="(memlineage-backup-\d{8}-\d{6}\.mlbk)"', disposition)
    assert match, disposition


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


def test_postgres_backup_uses_pg_dump(monkeypatch: pytest.MonkeyPatch):
    engine = create_engine("postgresql+psycopg://afkms:secret@127.0.0.1:5432/afkms", future=True)
    service = DbBackupService(_FakeSession(engine))
    seen: dict[str, object] = {}

    class _RunResult:
        returncode = 0
        stdout = ""
        stderr = ""

    def _fake_run(cmd, env=None, capture_output=False, text=False, check=False):
        seen["cmd"] = [str(part) for part in cmd]
        seen["env"] = dict(env or {})
        cmd_items = [str(part) for part in cmd]
        file_index = cmd_items.index("--file")
        Path(cmd_items[file_index + 1]).write_bytes(b"pg-dump-bytes")
        return _RunResult()

    monkeypatch.setattr("src.services.db_backup_service.subprocess.run", _fake_run)

    filename, package_blob, backend = service.create_backup()
    assert filename.endswith(".mlbk")
    assert backend == "postgres"
    assert seen["cmd"][0] == "pg_dump"
    assert "--format=custom" in seen["cmd"]
    assert "--schema=public" in seen["cmd"]
    assert "--dbname" in seen["cmd"]
    assert seen["env"]["PGPASSWORD"] == "secret"

    archive = zipfile.ZipFile(io.BytesIO(package_blob))
    manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
    assert manifest["backend"] == "postgres"
    assert archive.read("payload.pgdump") == b"pg-dump-bytes"


def test_postgres_restore_uses_pg_restore(monkeypatch: pytest.MonkeyPatch):
    engine = create_engine("postgresql+psycopg://afkms:secret@127.0.0.1:5432/afkms", future=True)
    service = DbBackupService(_FakeSession(engine))
    seen: dict[str, object] = {}

    class _RunResult:
        returncode = 0
        stdout = ""
        stderr = ""

    backup_blob_io = io.BytesIO()
    with zipfile.ZipFile(backup_blob_io, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "manifest.json",
            json.dumps(
                {
                    "format": "memlineage-db-backup",
                    "version": 1,
                    "backend": "postgres",
                    "created_at": "2026-03-04T00:00:00Z",
                    "payload": "payload.pgdump",
                }
            ),
        )
        archive.writestr("payload.pgdump", b"restore-target-payload")

    def _fake_run(cmd, env=None, capture_output=False, text=False, check=False):
        cmd_items = [str(part) for part in cmd]
        seen["cmd"] = cmd_items
        seen["env"] = dict(env or {})
        seen["payload"] = Path(cmd_items[-1]).read_bytes()
        return _RunResult()

    monkeypatch.setattr("src.services.db_backup_service.subprocess.run", _fake_run)

    restored = service.restore_backup(backup_blob_io.getvalue(), backup_filename="restore.mlbk")
    assert restored["status"] == "restored"
    assert restored["backend"] == "postgres"
    assert seen["cmd"][0] == "pg_restore"
    assert "--clean" in seen["cmd"]
    assert "--if-exists" in seen["cmd"]
    assert "--schema=public" in seen["cmd"]
    assert "--dbname" in seen["cmd"]
    assert seen["env"]["PGPASSWORD"] == "secret"
    assert seen["payload"] == b"restore-target-payload"


def test_pg_command_failure_logs_stderr(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
    engine = create_engine("postgresql+psycopg://afkms:secret@127.0.0.1:5432/afkms", future=True)
    service = DbBackupService(_FakeSession(engine))

    class _RunResult:
        returncode = 1
        stdout = ""
        stderr = "permission denied for table _timescaledb_catalog.hypertable"

    def _fake_run(cmd, env=None, capture_output=False, text=False, check=False):  # noqa: ARG001
        return _RunResult()

    monkeypatch.setattr("src.services.db_backup_service.subprocess.run", _fake_run)

    with caplog.at_level("ERROR"):
        with pytest.raises(ValueError, match="DB_BACKUP_COMMAND_FAILED"):
            service._run_pg_command(["pg_restore", "--dbname", "afkms"])

    assert "Postgres command failed" in caplog.text
    assert "permission denied for table _timescaledb_catalog.hypertable" in caplog.text
