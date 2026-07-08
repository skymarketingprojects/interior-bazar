from app_ib.Utils.BaseValidator import BaseValidator
from typing import List, Optional
from pydantic import Field, validator


class BannerButtonSchema(BaseValidator):
    label: str
    link: Optional[str] = Field(default='')
    isPrimary: Optional[bool] = Field(default=False)


class BannerMetricSchema(BaseValidator):
    metric: str
    description: Optional[str] = Field(default='')
    index: Optional[int] = Field(default=0)


class BannerCreateSchema(BaseValidator):
    # Real HomeHeroBanner fields (interior_advertisement.models.HomeHeroBanner).
    tag: Optional[str] = Field(default='')
    title: str
    description: Optional[str] = Field(default='')
    page: Optional[str] = Field(default='home')
    displayOrder: Optional[int] = Field(default=0)
    isActive: Optional[bool] = Field(default=True)
    audience: Optional[str] = Field(default='all')
    backgroundGradient: Optional[str] = Field(default='')
    backgroundImageUrl: Optional[str] = Field(default='')
    startsAt: Optional[str] = Field(default=None)   # ISO string or null (evergreen)
    endsAt: Optional[str] = Field(default=None)
    buttons: Optional[List[BannerButtonSchema]] = Field(default_factory=list)
    metrics: Optional[List[BannerMetricSchema]] = Field(default_factory=list)
    businessIds: Optional[List[int]] = Field(default_factory=list)  # max 2 rendered

    @validator('businessIds')
    def _cap_businesses(cls, v):
        if v and len(v) > 2:
            raise ValueError('At most 2 businesses can be assigned to a slide.')
        return v

    @validator('audience')
    def _valid_audience(cls, v):
        if v not in ('all', 'buyers', 'sellers'):
            raise ValueError("audience must be one of all/buyers/sellers")
        return v


class BannerUpdateSchema(BannerCreateSchema):
    # Same shape; title optional on update (partial edits allowed).
    title: Optional[str] = Field(default=None)


class BannerMoveSchema(BaseValidator):
    direction: str  # up | down
