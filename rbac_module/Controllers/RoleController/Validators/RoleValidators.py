from typing import Optional, List
from pydantic import Field
from app_ib.Utils.BaseValidator import BaseValidator


class RoleCreateSchema(BaseValidator):
    name: str = Field(..., description="Role name")
    userIds: Optional[List[int]] = Field(None, description="List of user id's")
    accessIds: Optional[List[int]] = Field(None, description="List of access id's")

class RoleUpdateSchema(BaseValidator):
    name: Optional[str] = Field(None, description="Role name")
    userIds: Optional[List[int]] = Field(None, description="List of user id's")
    accessIds: Optional[List[int]] = Field(None, description="List of access id's")
class RoleAssignUsersSchema(BaseValidator):
    userIds: List[int] = Field(..., description="List of user id's to assign to the role")

class RoleAccessUpdateSchema(BaseValidator):
    accessIds: List[int] = Field(..., description="List of access id's to assign to the role")