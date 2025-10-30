from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db
from app.api.deps.auth import get_current_user_id, require_role_editor_or_admin
from app.services.report_service import ReportService
from app.schemas.report import (
    CreateReportRequest,
    ReportListResponse,
    ReportItem,
    ModerateReportRequest,
    ModerateReportResponse,
)


report_router = APIRouter(prefix="/reports", tags=["Reports"])


@report_router.post("", response_model=ReportItem, status_code=status.HTTP_201_CREATED)
async def create_report(
    req: CreateReportRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    return await service.create_report(user_id, req)


@report_router.get("", response_model=ReportListResponse)
async def list_reports(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(require_role_editor_or_admin),
    db: AsyncSession = Depends(get_db),
):
    # simple role check for admin/editor
    # payload is attached by middleware to request.state.user; this route uses dependency only for ID
    # For strict role checking, add a separate dependency that validates role from request.state.user
    service = ReportService(db)
    return await service.list_reports(limit, offset)


@report_router.post("/{report_id}/moderate", response_model=ModerateReportResponse)
async def moderate_report(
    report_id: str = Path(...),
    req: ModerateReportRequest = ...,
    user_id: str = Depends(require_role_editor_or_admin),
    db: AsyncSession = Depends(get_db),
):
    # role check could be enforced here using user role from request.state.user
    service = ReportService(db)
    return await service.moderate(user_id, report_id, req)


