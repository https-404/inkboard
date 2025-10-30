import uuid
from typing import List
from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.db.models.report import Report
from app.db.models.article import Article
from app.schemas.report import (
    CreateReportRequest,
    ReportListResponse,
    ReportItem,
    ModerateReportRequest,
    ModerateReportResponse,
)


import re
from app.core.config import settings


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _contains_bad_words(self, text: str) -> bool:
        # word-boundary regex match using config list
        if not settings.BAD_WORDS:
            return False
        pattern = r"\\b(" + "|".join(re.escape(w.lower()) for w in settings.BAD_WORDS) + r")\\b"
        return re.search(pattern, text.lower()) is not None

    async def create_report(self, reporter_id: str, req: CreateReportRequest) -> ReportItem:
        # ensure article exists
        stmt = select(Article.id).where(Article.id == uuid.UUID(req.article_id))
        if not (await self.db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

        # prevent duplicate per (article_id, reporter_id)
        existing_stmt = select(Report).where(
            Report.article_id == uuid.UUID(req.article_id),
            Report.reporter_id == uuid.UUID(reporter_id),
        )
        existing = (await self.db.execute(existing_stmt)).scalar_one_or_none()
        if existing:
            return ReportItem(
                id=str(existing.id),
                article_id=str(existing.article_id),
                reporter_id=str(existing.reporter_id),
                reason=existing.reason,
                status=existing.status,
                created_at=existing.created_at,
                updated_at=existing.updated_at,
            )

        # simple throttle: max N per minute per reporter
        min_ago = func.now() - func.make_interval(mins=settings.REPORT_THROTTLE_PER_MIN)
        throttle_stmt = select(func.count()).where(
            Report.reporter_id == uuid.UUID(reporter_id),
            Report.created_at >= min_ago,
        )
        count_recent = (await self.db.execute(throttle_stmt)).scalar_one()
        if count_recent and int(count_recent) >= settings.REPORT_THROTTLE_PER_MIN:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many reports, slow down")

        report = Report(
            article_id=uuid.UUID(req.article_id),
            reporter_id=uuid.UUID(reporter_id),
            reason=req.reason,
        )
        self.db.add(report)
        await self.db.flush()
        await self.db.refresh(report)

        # heuristic: auto-flag articles with bad words by archiving
        if self._contains_bad_words(req.reason):
            await self.db.execute(
                update(Article).where(Article.id == report.article_id).values(status="archived")
            )

        return ReportItem(
            id=str(report.id),
            article_id=str(report.article_id),
            reporter_id=str(report.reporter_id),
            reason=report.reason,
            status=report.status,
            created_at=report.created_at,
            updated_at=report.updated_at,
        )

    async def list_reports(self, limit: int = 50, offset: int = 0) -> ReportListResponse:
        stmt = select(Report).order_by(Report.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        rows: List[Report] = result.scalars().all()
        items = [
            ReportItem(
                id=str(r.id),
                article_id=str(r.article_id),
                reporter_id=str(r.reporter_id),
                reason=r.reason,
                status=r.status,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in rows
        ]
        return ReportListResponse(reports=items, total=len(items))

    async def moderate(self, admin_id: str, report_id: str, req: ModerateReportRequest) -> ModerateReportResponse:
        # role enforcement is expected in route layer; service assumes authorized
        stmt = select(Report).where(Report.id == uuid.UUID(report_id))
        result = await self.db.execute(stmt)
        report = result.scalar_one_or_none()
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

        if req.action == "approve":
            await self.db.execute(update(Article).where(Article.id == report.article_id).values(status="archived"))
            new_status = "approved"
        elif req.action == "restore":
            # unarchive to draft
            await self.db.execute(update(Article).where(Article.id == report.article_id).values(status="draft"))
            new_status = "approved"  # keep report approved but article restored
        else:
            new_status = "rejected"

        # audit log placeholder
        # In real system, persist moderation note and moderator id
        await self.db.execute(
            update(Report).where(Report.id == report.id).values(status=new_status)
        )

        return ModerateReportResponse(id=str(report.id), status=new_status, message=f"Report {new_status}", note=req.note)


