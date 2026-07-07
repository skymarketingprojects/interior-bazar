from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional
from pydantic import Field


class TestimonialCreateSchema(BaseValidator):
    author: str
    quote: str
    role: Optional[str] = Field(default='')
    type: Optional[str] = Field(default='text')
    featured: Optional[bool] = Field(default=False)
    status: Optional[str] = Field(default='active')
    avatarUrl: Optional[str] = Field(default='')


class TestimonialUpdateSchema(BaseValidator):
    author: Optional[str] = Field(default=None)
    quote: Optional[str] = Field(default=None)
    role: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)
    featured: Optional[bool] = Field(default=None)
    status: Optional[str] = Field(default=None)
    avatarUrl: Optional[str] = Field(default=None)
