from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Header, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from src.schemas import DbRestoreOut
from src.services.db_backup_service import DbBackupService


def build_router(get_db_dep):
    router = APIRouter(prefix="/api/v1/admin", tags=["db-admin"])

    def _raise_for_backup_error(exc: ValueError) -> None:
        code = str(exc)
        status_code = 422
        if code == "DB_BACKUP_BACKEND_MISMATCH":
            status_code = 409
        elif code in {"DB_BACKUP_TOOL_NOT_FOUND", "DB_BACKUP_COMMAND_FAILED"}:
            status_code = 500
        raise HTTPException(status_code=status_code, detail={"code": code, "message": code.lower()}) from exc

    @router.get("/db/backup")
    def download_backup(db: Session = Depends(get_db_dep)):
        service = DbBackupService(db)
        try:
            filename, package, backend = service.create_backup()
        except ValueError as exc:
            _raise_for_backup_error(exc)

        return Response(
            content=package,
            media_type="application/octet-stream",
            headers={
                "content-disposition": f'attachment; filename="{filename}"',
                "x-backup-backend": backend,
            },
        )

    @router.post("/db/restore", response_model=DbRestoreOut)
    def restore_backup(
        backup_blob: bytes = Body(..., media_type="application/octet-stream"),
        backup_filename: str = Header(default="", alias="x-backup-filename"),
        db: Session = Depends(get_db_dep),
    ):
        service = DbBackupService(db)
        try:
            result = service.restore_backup(backup_blob, backup_filename=backup_filename)
        except ValueError as exc:
            _raise_for_backup_error(exc)

        return {
            "status": result["status"],
            "backend": result["backend"],
            "restored_at": result["restored_at"],
        }

    return router
