from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.schemas import TopicListOut
from src.services.task_service import TopicService


def build_router(get_db_dep):
    router = APIRouter(prefix="/api/v1/topics", tags=["topics"])

    @router.get("", response_model=TopicListOut)
    def list_topics(db: Session = Depends(get_db_dep)):
        items = TopicService(db).list()
        return {"items": items}

    return router
