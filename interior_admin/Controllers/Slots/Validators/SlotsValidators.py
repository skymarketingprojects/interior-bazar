from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional
from pydantic import Field


class SlotOverrideSchema(BaseValidator):
    capacity: Optional[int] = Field(default=None)
    holderId: Optional[int] = Field(default=None)   # 0/None clears holder
    priority: Optional[int] = Field(default=None)
