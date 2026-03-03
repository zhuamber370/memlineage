from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.schemas import (
    SkillAgent,
    SkillHealthOut,
    SkillInstallIn,
    SkillOperationOut,
    SkillPathConfigIn,
    SkillStatusListOut,
    SkillStatusOut,
    SkillVersionOut,
)
from src.services.skill_service import SkillService


def build_router(get_db_dep):
    router = APIRouter(prefix="/api/v1/skills", tags=["skills"])

    def _raise_for_skill_error(exc: ValueError) -> None:
        code = str(exc)
        status_code = 422
        if code in {"SKILL_NOT_INSTALLED"}:
            status_code = 404
        if code in {"SKILL_PATH_NOT_FOUND"}:
            status_code = 400
        raise HTTPException(
            status_code=status_code,
            detail={"code": code, "message": code.lower()},
        ) from exc

    @router.get("", response_model=SkillStatusListOut)
    def list_skills(db: Session = Depends(get_db_dep)):
        service = SkillService(db)
        return {"items": service.list_status()}

    @router.get("/{agent}", response_model=SkillStatusOut)
    def get_skill(agent: SkillAgent, db: Session = Depends(get_db_dep)):
        service = SkillService(db)
        return service.get_status(agent)

    @router.put("/{agent}/config", response_model=SkillStatusOut)
    def configure_skill_path(agent: SkillAgent, payload: SkillPathConfigIn, db: Session = Depends(get_db_dep)):
        service = SkillService(db)
        try:
            return service.configure_path(agent, payload.configured_path)
        except ValueError as exc:
            _raise_for_skill_error(exc)

    @router.post("/{agent}/detect", response_model=SkillStatusOut)
    def detect_skill(agent: SkillAgent, db: Session = Depends(get_db_dep)):
        service = SkillService(db)
        try:
            return service.detect(agent)
        except ValueError as exc:
            _raise_for_skill_error(exc)

    @router.post("/{agent}/install", response_model=SkillOperationOut)
    def install_skill(
        agent: SkillAgent, payload: Optional[SkillInstallIn] = None, db: Session = Depends(get_db_dep)
    ):
        service = SkillService(db)
        try:
            status = service.install(agent, force=bool(payload.force) if payload else False)
        except ValueError as exc:
            _raise_for_skill_error(exc)
        return {"action": "install", "status": status}

    @router.delete("/{agent}", response_model=SkillOperationOut)
    def uninstall_skill(agent: SkillAgent, db: Session = Depends(get_db_dep)):
        service = SkillService(db)
        try:
            status = service.uninstall(agent)
        except ValueError as exc:
            _raise_for_skill_error(exc)
        return {"action": "uninstall", "status": status}

    @router.post("/{agent}/disable", response_model=SkillOperationOut)
    def disable_skill(agent: SkillAgent, db: Session = Depends(get_db_dep)):
        service = SkillService(db)
        try:
            status = service.disable(agent)
        except ValueError as exc:
            _raise_for_skill_error(exc)
        return {"action": "disable", "status": status}

    @router.post("/{agent}/enable", response_model=SkillOperationOut)
    def enable_skill(agent: SkillAgent, db: Session = Depends(get_db_dep)):
        service = SkillService(db)
        try:
            status = service.enable(agent)
        except ValueError as exc:
            _raise_for_skill_error(exc)
        return {"action": "enable", "status": status}

    @router.get("/{agent}/health", response_model=SkillHealthOut)
    def health_skill(agent: SkillAgent, db: Session = Depends(get_db_dep)):
        service = SkillService(db)
        try:
            return service.health(agent)
        except ValueError as exc:
            _raise_for_skill_error(exc)

    @router.get("/{agent}/version", response_model=SkillVersionOut)
    def version_skill(agent: SkillAgent, db: Session = Depends(get_db_dep)):
        service = SkillService(db)
        try:
            return service.version(agent)
        except ValueError as exc:
            _raise_for_skill_error(exc)

    @router.post("/{agent}/update", response_model=SkillVersionOut)
    def update_skill(
        agent: SkillAgent, payload: Optional[SkillInstallIn] = None, db: Session = Depends(get_db_dep)
    ):
        service = SkillService(db)
        try:
            return service.update(agent, force=bool(payload.force) if payload else False)
        except ValueError as exc:
            _raise_for_skill_error(exc)

    return router
