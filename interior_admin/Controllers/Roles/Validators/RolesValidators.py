from app_ib.Utils.BaseValidator import BaseValidator
from typing import Dict
from pydantic import Field


class RoleUpdateSchema(BaseValidator):
    roleName: str
    modules: Dict[str, int] = Field(default_factory=dict)  # {moduleKey: level 0..3}


class RoleCreateSchema(BaseValidator):
    name: str
    modules: Dict[str, int] = Field(default_factory=dict)  # {moduleKey: level 0..3}
