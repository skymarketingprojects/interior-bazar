from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional
from pydantic import Field


class ReportListFilters(BaseValidator):
    pageNo: Optional[int] = Field(default=1)
    pageSize: Optional[int] = Field(default=20)
    status: Optional[str] = Field(default=None)


class ReportSubmitSchema(BaseValidator):
    reason: str
    targetType: Optional[str] = Field(default='business')
    targetId: Optional[str] = Field(default='')
    reporterEmail: Optional[str] = Field(default='')


class ReportResolveSchema(BaseValidator):
    status: str  # resolved | dismissed | open
