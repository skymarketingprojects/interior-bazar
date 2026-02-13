from rbac_module.Controllers.AccessController.AccessController import ACCESS_CONTROLLER
from django.core.exceptions import PermissionDenied
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.models import CustomUser

async def hasAccess(user, accessName):
    isAdmin = await IsAdmin(user)
    if not isAdmin:
        raise PermissionDenied(detail=RESPONSE_MESSAGES.unauthorized,code=RESPONSE_CODES.forbidden)

    accessResp = await ACCESS_CONTROLLER.checkUserHasAccess(user, accessName)
    if not hasAccess.data:
        raise PermissionDenied(detail=accessResp.message,code=RESPONSE_CODES.forbidden)

    return True

async def IsAdmin(self,user:CustomUser):
    if user.type == 'admin':
        return True
    return False