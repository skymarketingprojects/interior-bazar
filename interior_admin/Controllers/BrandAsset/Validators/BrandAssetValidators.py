from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional
from pydantic import Field


class BrandAssetSchema(BaseValidator):
    logoUrl: Optional[str] = Field(default=None)
    faviconUrl: Optional[str] = Field(default=None)
