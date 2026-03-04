from __future__ import annotations

import io
import json
import os
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

BACKUP_FORMAT = "memlineage-db-backup"
BACKUP_VERSION = 1


class DbBackupService:
    def __init__(self, db: Session):
        self.db = db

    def create_backup(self) -> tuple[str, bytes, Literal["sqlite", "postgres"]]:
        created_at = datetime.now(timezone.utc)
        backend = self._runtime_backend()

        if backend == "sqlite":
            payload_name = "payload.sqlite3"
            payload = self._export_sqlite()
        else:
            payload_name = "payload.pgdump"
            payload = self._export_postgres()

        manifest = {
            "format": BACKUP_FORMAT,
            "version": BACKUP_VERSION,
            "backend": backend,
            "created_at": created_at.isoformat(),
            "payload": payload_name,
        }

        package = io.BytesIO()
        with zipfile.ZipFile(package, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=True))
            archive.writestr(payload_name, payload)

        filename = f"memlineage-backup-{created_at.strftime('%Y%m%d-%H%M%S')}.mlbk"
        return filename, package.getvalue(), backend

    def restore_backup(self, backup_blob: bytes, *, backup_filename: str | None = None) -> dict:
        parsed = self._parse_backup_package(backup_blob)
        backend = self._runtime_backend()
        manifest_backend = parsed["manifest_backend"]
        payload = parsed["payload"]

        if manifest_backend != backend:
            raise ValueError("DB_BACKUP_BACKEND_MISMATCH")

        if backend == "sqlite":
            self._restore_sqlite(payload)
        else:
            self._restore_postgres(payload)

        restored_at = datetime.now(timezone.utc)
        return {
            "status": "restored",
            "backend": backend,
            "restored_at": restored_at,
            "filename": backup_filename or "",
        }

    def _runtime_backend(self) -> Literal["sqlite", "postgres"]:
        bind = self._engine()
        if bind.dialect.name == "sqlite":
            return "sqlite"
        if bind.dialect.name == "postgresql":
            return "postgres"
        raise ValueError("DB_BACKUP_INVALID")

    def _sqlite_db_path(self) -> Path:
        bind = self._engine()
        if bind.dialect.name != "sqlite" or not bind.url.database:
            raise ValueError("DB_BACKUP_INVALID")
        return Path(bind.url.database)

    def _export_sqlite(self) -> bytes:
        db_path = self._sqlite_db_path()
        if not db_path.exists() or not db_path.is_file():
            raise ValueError("DB_BACKUP_INVALID")
        return db_path.read_bytes()

    def _restore_sqlite(self, payload: bytes) -> None:
        db_path = self._sqlite_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)

        temp_file = tempfile.NamedTemporaryFile(prefix="afkms-restore-", suffix=".sqlite3", delete=False)
        temp_path = Path(temp_file.name)
        try:
            temp_file.write(payload)
            temp_file.flush()
            temp_file.close()

            bind = self.db.get_bind()
            self.db.close()
            if isinstance(bind, Engine):
                bind.dispose()

            temp_path.replace(db_path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def _postgres_env(self) -> dict[str, str]:
        env = os.environ.copy()
        bind = self._engine()
        password = bind.url.password
        if password:
            env["PGPASSWORD"] = password
        return env

    def _run_pg_command(self, cmd: list[str]) -> None:
        try:
            proc = subprocess.run(cmd, env=self._postgres_env(), capture_output=True, text=True, check=False)
        except FileNotFoundError as exc:
            raise ValueError("DB_BACKUP_TOOL_NOT_FOUND") from exc

        if proc.returncode != 0:
            raise ValueError("DB_BACKUP_COMMAND_FAILED")

    def _export_postgres(self) -> bytes:
        bind = self._engine()
        host = bind.url.host
        port = bind.url.port
        username = bind.url.username
        database = bind.url.database
        if not host or not port or not username or not database:
            raise ValueError("DB_BACKUP_INVALID")

        temp_file = tempfile.NamedTemporaryFile(prefix="afkms-backup-", suffix=".pgdump", delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()

        try:
            cmd = [
                "pg_dump",
                "--format=custom",
                "--host",
                host,
                "--port",
                str(port),
                "--username",
                username,
                "--dbname",
                database,
                "--file",
                str(temp_path),
            ]
            self._run_pg_command(cmd)
            return temp_path.read_bytes()
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def _restore_postgres(self, payload: bytes) -> None:
        bind = self._engine()
        host = bind.url.host
        port = bind.url.port
        username = bind.url.username
        database = bind.url.database
        if not host or not port or not username or not database:
            raise ValueError("DB_BACKUP_INVALID")

        temp_file = tempfile.NamedTemporaryFile(prefix="afkms-restore-", suffix=".pgdump", delete=False)
        temp_path = Path(temp_file.name)

        try:
            temp_file.write(payload)
            temp_file.flush()
            temp_file.close()

            cmd = [
                "pg_restore",
                "--clean",
                "--if-exists",
                "--no-owner",
                "--no-privileges",
                "--host",
                host,
                "--port",
                str(port),
                "--username",
                username,
                "--dbname",
                database,
                str(temp_path),
            ]
            self._run_pg_command(cmd)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def _parse_backup_package(self, backup_blob: bytes) -> dict[str, object]:
        try:
            archive = zipfile.ZipFile(io.BytesIO(backup_blob))
        except zipfile.BadZipFile as exc:
            raise ValueError("DB_BACKUP_INVALID") from exc

        try:
            manifest_raw = archive.read("manifest.json")
            manifest = json.loads(manifest_raw.decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            raise ValueError("DB_BACKUP_INVALID") from exc

        if not isinstance(manifest, dict):
            raise ValueError("DB_BACKUP_INVALID")
        if manifest.get("format") != BACKUP_FORMAT:
            raise ValueError("DB_BACKUP_INVALID")
        if manifest.get("version") != BACKUP_VERSION:
            raise ValueError("DB_BACKUP_INVALID")

        backend = manifest.get("backend")
        payload_name = manifest.get("payload")
        if backend not in {"sqlite", "postgres"}:
            raise ValueError("DB_BACKUP_INVALID")
        if payload_name not in {"payload.sqlite3", "payload.pgdump"}:
            raise ValueError("DB_BACKUP_INVALID")

        try:
            payload = archive.read(str(payload_name))
        except Exception as exc:  # noqa: BLE001
            raise ValueError("DB_BACKUP_INVALID") from exc

        if not payload:
            raise ValueError("DB_BACKUP_INVALID")

        return {"manifest_backend": backend, "payload": payload}

    def _engine(self) -> Engine:
        bind = self.db.get_bind()
        if not isinstance(bind, Engine):
            raise ValueError("DB_BACKUP_INVALID")
        return bind
