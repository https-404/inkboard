from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class CreateReportRequest(BaseModel):
    article_id: str = Field(...)
    reason: str = Field(..., min_length=3, max_length=2000)


class ReportItem(BaseModel):
    id: str
    article_id: str
    reporter_id: str
    reason: str
    status: str
    created_at: datetime
    updated_at: datetime


class ReportListResponse(BaseModel):
    reports: List[ReportItem]
    total: int


class ModerateReportRequest(BaseModel):
    action: str = Field(..., pattern=r"^(approve|reject|restore)$")
    note: Optional[str] = None


class ModerateReportResponse(BaseModel):
    id: str
    status: str
    message: str
    note: Optional[str] = None


