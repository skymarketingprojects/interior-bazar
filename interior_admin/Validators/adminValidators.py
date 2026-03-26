from rbac_module.Controllers.AccessController.AccessController import ACCESS_CONTROLLER
from django.core.exceptions import PermissionDenied
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.BaseValidator import BaseValidator
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.models import CustomUser
from typing import Optional, List
from pydantic import Field

async def hasAccess(user, accessName):
    isAdmin = await IsAdmin(user)
    if not isAdmin:
        raise PermissionDenied(RESPONSE_MESSAGES.unauthorized)

    accessResp = await ACCESS_CONTROLLER.checkUserHasAccess(user, accessName)
    if not accessResp.data:
        raise PermissionDenied(RESPONSE_MESSAGES.unauthorized)

    return True

async def IsAdmin(user:CustomUser):
    if user.type == 'admin':
        return True
    return False

class CreateAdminUser(BaseValidator):
    username: str
    password: str
    name: str
    email: str
    phone: str
    roles: List[int]

class UpdateAdminUser(BaseValidator):
    username: Optional[str]
    password: Optional[str]
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    roles: Optional[List[int]]