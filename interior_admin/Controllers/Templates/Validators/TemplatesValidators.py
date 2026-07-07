from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional, List
from pydantic import Field


class TemplateCreateSchema(BaseValidator):
    key: str
    channel: Optional[str] = Field(default='email')
    subject: Optional[str] = Field(default='')
    body: Optional[str] = Field(default='')
    variables: Optional[List[str]] = Field(default_factory=list)
    active: Optional[bool] = Field(default=True)


class TemplateUpdateSchema(BaseValidator):
    channel: Optional[str] = Field(default=None)
    subject: Optional[str] = Field(default=None)
    body: Optional[str] = Field(default=None)
    variables: Optional[List[str]] = Field(default=None)
    active: Optional[bool] = Field(default=None)
