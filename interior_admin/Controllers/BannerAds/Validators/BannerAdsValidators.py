from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional, List
from pydantic import Field


class BannerAdListFilters(BaseValidator):
    status: Optional[str] = Field(default=None)  # tab key pending/live/rejected or a raw status code
    pageNo: Optional[int] = Field(default=1)
    pageSize: Optional[int] = Field(default=20)


class RejectAdSchema(BaseValidator):
    reason: str


class FallbackAdSchema(BaseValidator):
    placement: str  # AdPlacement code (required) — must match the slot's placement
    page: Optional[str] = Field(default=None)  # "" = show on any page
    image: Optional[str] = Field(default=None)  # image URL (from the uploader)
    eyebrow: Optional[str] = Field(default=None)
    heading: Optional[str] = Field(default=None)
    sub: Optional[str] = Field(default=None)
    features: Optional[List] = Field(default=None)
    ctaLabel: Optional[str] = Field(default=None)
    ctaLink: Optional[str] = Field(default=None)
    theme: Optional[str] = Field(default=None)
