from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional
from pydantic import Field


class BrandAssetSchema(BaseValidator):
    logoUrl: Optional[str] = Field(default=None)
    faviconUrl: Optional[str] = Field(default=None)
    tagline: Optional[str] = Field(default=None)


class BrandLogoCreateSchema(BaseValidator):
    imageUrl: str
    label: Optional[str] = Field(default='')
    tagline: Optional[str] = Field(default='')
    activeFrom: Optional[str] = Field(default=None)  # 'YYYY-MM-DD' or '' — parsed in controller
    activeTo: Optional[str] = Field(default=None)


class BrandLogoUpdateSchema(BaseValidator):
    imageUrl: Optional[str] = Field(default=None)
    label: Optional[str] = Field(default=None)
    tagline: Optional[str] = Field(default=None)
    activeFrom: Optional[str] = Field(default=None)
    activeTo: Optional[str] = Field(default=None)
