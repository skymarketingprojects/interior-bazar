from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional, List
from pydantic import Field


class CategoryCreateSchema(BaseValidator):
    value: str
    label: str
    trending: Optional[bool] = Field(default=False)


class CategoryUpdateSchema(BaseValidator):
    label: Optional[str] = Field(default=None)
    value: Optional[str] = Field(default=None)
    trending: Optional[bool] = Field(default=None)
    index: Optional[int] = Field(default=None)
    isActive: Optional[bool] = Field(default=None)


class SegmentCreateSchema(BaseValidator):
    value: str
    label: str
    trending: Optional[bool] = Field(default=False)
    categoryIds: Optional[List[int]] = Field(default=None)


class SegmentUpdateSchema(BaseValidator):
    value: Optional[str] = Field(default=None)
    label: Optional[str] = Field(default=None)
    trending: Optional[bool] = Field(default=None)
    isActive: Optional[bool] = Field(default=None)
    categoryIds: Optional[List[int]] = Field(default=None)


class StateCreateSchema(BaseValidator):
    name: str
    value: Optional[str] = Field(default=None)
    countryId: Optional[int] = Field(default=None)


class StateUpdateSchema(BaseValidator):
    name: Optional[str] = Field(default=None)
    value: Optional[str] = Field(default=None)
    countryId: Optional[int] = Field(default=None)
