from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from src.schemas import NewsCreate, NewsListOut, NewsOut, NewsPatch
from src.services.news_service import NewsService


def build_router(get_db_dep):
    router = APIRouter(prefix="/api/v1/news", tags=["news"])

    def _raise_news_error(exc: ValueError) -> None:
        code = str(exc)
        status_code = 422
        raise HTTPException(status_code=status_code, detail={"code": code, "message": code.lower()}) from exc

    @router.post("", response_model=NewsOut, status_code=201)
    def create_news(payload: NewsCreate, db: Session = Depends(get_db_dep)):
        try:
            return NewsService(db).create(payload)
        except ValueError as exc:
            _raise_news_error(exc)

    @router.get("", response_model=NewsListOut)
    def list_news(
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        status: Optional[str] = None,
        q: Optional[str] = None,
        published_from: Optional[datetime] = None,
        published_to: Optional[datetime] = None,
        db: Session = Depends(get_db_dep),
    ):
        items, total = NewsService(db).list(
            page=page,
            page_size=page_size,
            status=status,
            q=q,
            published_from=published_from,
            published_to=published_to,
        )
        return {"items": items, "page": page, "page_size": page_size, "total": total}

    @router.get("/{news_id}", response_model=NewsOut)
    def get_news(news_id: str, db: Session = Depends(get_db_dep)):
        item = NewsService(db).get(news_id)
        if not item:
            raise HTTPException(status_code=404, detail={"code": "NEWS_NOT_FOUND", "message": "not found"})
        return item

    @router.patch("/{news_id}", response_model=NewsOut)
    def patch_news(news_id: str, payload: NewsPatch, db: Session = Depends(get_db_dep)):
        try:
            item = NewsService(db).patch(news_id, payload)
        except ValueError as exc:
            _raise_news_error(exc)
        if not item:
            raise HTTPException(status_code=404, detail={"code": "NEWS_NOT_FOUND", "message": "not found"})
        return item

    @router.post("/{news_id}/archive", response_model=NewsOut)
    def archive_news(news_id: str, db: Session = Depends(get_db_dep)):
        item = NewsService(db).archive(news_id)
        if not item:
            raise HTTPException(status_code=404, detail={"code": "NEWS_NOT_FOUND", "message": "not found"})
        return item

    @router.delete("/{news_id}", status_code=204)
    def delete_news(news_id: str, db: Session = Depends(get_db_dep)):
        deleted = NewsService(db).delete(news_id)
        if not deleted:
            raise HTTPException(status_code=404, detail={"code": "NEWS_NOT_FOUND", "message": "not found"})
        return Response(status_code=204)

    return router
