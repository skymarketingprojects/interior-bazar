from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional
from pydantic import Field


class BannerCreateSchema(BaseValidator):
    title: str
    supportText: Optional[str] = Field(default='')
    bannerUrl: Optional[str] = Field(default='')
    isActive: Optional[bool] = Field(default=False)


class BannerUpdateSchema(BaseValidator):
    title: Optional[str] = Field(default=None)
    supportText: Optional[str] = Field(default=None)
    bannerUrl: Optional[str] = Field(default=None)
    isActive: Optional[bool] = Field(default=None)


class BannerMoveSchema(BaseValidator):
    direction: str  # up | down
