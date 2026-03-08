from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from src.models import NewsItem, NewsSource
from src.schemas import NewsCreate, NewsPatch
from src.services.audit_service import log_audit_event


class NewsService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: NewsCreate) -> dict:
        self._validate_sources(payload.sources)

        news = NewsItem(
            id=f"nws_{uuid.uuid4().hex[:12]}",
            title=payload.title,
            summary=payload.summary,
            opportunity=payload.opportunity,
            risk=payload.risk,
            tags_json=payload.tags,
            status="new",
            published_at=payload.published_at,
            captured_at=payload.captured_at,
            raw_payload_json=payload.raw_payload_json,
        )
        self.db.add(news)
        self.db.flush()
        self._replace_sources(news.id, payload.sources)
        self.db.commit()
        self.db.refresh(news)
        log_audit_event(
            self.db,
            actor_type="user",
            actor_id="local",
            tool="api",
            action="create_news",
            target_type="news",
            target_id=news.id,
            source_refs=[source.url for source in payload.sources],
        )
        return self.get(news.id) or {}

    def list(
        self,
        *,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        q: Optional[str] = None,
        published_from: Optional[datetime] = None,
        published_to: Optional[datetime] = None,
    ) -> tuple[list[dict], int]:
        stmt = select(NewsItem)
        count_stmt = select(func.count()).select_from(NewsItem)
        if status:
            stmt = stmt.where(NewsItem.status == status)
            count_stmt = count_stmt.where(NewsItem.status == status)
        if q:
            like = f"%{q}%"
            filter_clause = or_(
                NewsItem.title.ilike(like),
                NewsItem.summary.ilike(like),
                NewsItem.opportunity.ilike(like),
                NewsItem.risk.ilike(like),
            )
            stmt = stmt.where(filter_clause)
            count_stmt = count_stmt.where(filter_clause)
        if published_from is not None:
            stmt = stmt.where(NewsItem.published_at >= published_from)
            count_stmt = count_stmt.where(NewsItem.published_at >= published_from)
        if published_to is not None:
            stmt = stmt.where(NewsItem.published_at < published_to)
            count_stmt = count_stmt.where(NewsItem.published_at < published_to)

        stmt = (
            stmt.order_by(NewsItem.captured_at.desc(), NewsItem.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(self.db.scalars(stmt))
        total = int(self.db.scalar(count_stmt) or 0)
        return [self._to_out(item) for item in items], total

    def get(self, news_id: str) -> Optional[dict]:
        item = self.db.get(NewsItem, news_id)
        if item is None:
            return None
        return self._to_out(item)

    def patch(self, news_id: str, payload: NewsPatch) -> Optional[dict]:
        news = self.db.get(NewsItem, news_id)
        if news is None:
            return None
        patch_data = payload.model_dump(exclude_unset=True)
        if not patch_data:
            raise ValueError("NO_PATCH_FIELDS")

        sources = patch_data.pop("sources", None)
        if sources is not None:
            self._validate_sources(sources)
        tags = patch_data.pop("tags", None)

        for key, value in patch_data.items():
            setattr(news, key, value)
        if tags is not None:
            news.tags_json = tags
        self.db.add(news)
        self.db.flush()
        if sources is not None:
            self._replace_sources(news.id, sources)
        self.db.commit()
        self.db.refresh(news)
        source_refs = []
        if sources is not None:
            for source in sources:
                source_refs.append(source.url if hasattr(source, "url") else source["url"])
        log_audit_event(
            self.db,
            actor_type="user",
            actor_id="local",
            tool="api",
            action="patch_news",
            target_type="news",
            target_id=news.id,
            source_refs=source_refs,
        )
        return self._to_out(news)

    def archive(self, news_id: str) -> Optional[dict]:
        news = self.db.get(NewsItem, news_id)
        if news is None:
            return None
        if news.status != "archived":
            news.status = "archived"
            self.db.add(news)
            self.db.commit()
            self.db.refresh(news)
            log_audit_event(
                self.db,
                actor_type="user",
                actor_id="local",
                tool="api",
                action="archive_news",
                target_type="news",
                target_id=news.id,
                source_refs=[],
            )
        return self._to_out(news)

    def delete(self, news_id: str) -> bool:
        news = self.db.get(NewsItem, news_id)
        if news is None:
            return False
        source_refs = [source.url for source in self.db.scalars(select(NewsSource).where(NewsSource.news_id == news_id))]
        self.db.delete(news)
        self.db.commit()
        log_audit_event(
            self.db,
            actor_type="user",
            actor_id="local",
            tool="api",
            action="delete_news",
            target_type="news",
            target_id=news_id,
            source_refs=source_refs,
        )
        return True

    def _to_out(self, item: NewsItem) -> dict:
        sources = list(
            self.db.scalars(
                select(NewsSource)
                .where(NewsSource.news_id == item.id)
                .order_by(NewsSource.role.asc(), NewsSource.id.asc())
            )
        )
        return {
            "id": item.id,
            "title": item.title,
            "summary": item.summary,
            "opportunity": item.opportunity,
            "risk": item.risk,
            "tags": item.tags_json or [],
            "status": item.status,
            "published_at": item.published_at,
            "captured_at": item.captured_at,
            "raw_payload_json": item.raw_payload_json or {},
            "sources": [{"role": source.role, "url": source.url} for source in sources],
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }

    def _replace_sources(self, news_id: str, sources) -> None:
        self.db.execute(delete(NewsSource).where(NewsSource.news_id == news_id))
        for source in sources:
            role = source.role if hasattr(source, "role") else source["role"]
            url = source.url if hasattr(source, "url") else source["url"]
            self.db.add(
                NewsSource(
                    id=f"nwsrc_{uuid.uuid4().hex[:12]}",
                    news_id=news_id,
                    role=role,
                    url=url,
                )
            )

    def _validate_sources(self, sources) -> None:
        if not sources:
            raise ValueError("NEWS_SOURCES_REQUIRED")
        primary_count = 0
        for source in sources:
            role = source.role if hasattr(source, "role") else source["role"]
            if role == "primary":
                primary_count += 1
        if primary_count != 1:
            raise ValueError("NEWS_PRIMARY_SOURCE_REQUIRED")
