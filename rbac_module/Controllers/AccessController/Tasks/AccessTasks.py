from rbac_module.models import Access

from app_ib.Utils.Names import NAMES
from app_ib.decorators.ViewDecorator import taskExceptionHandler


class ACCESS_TASKS:

    @staticmethod
    @taskExceptionHandler
    async def getAccessDataTask(access: Access):
        data ={
            NAMES.ID: access.id,
            NAMES.NAME: access.permissionName,
            NAMES.PERMISSION: access.permission
        }
        return True, data

    @staticmethod
    @taskExceptionHandler
    async def getAccessForCheck(access: Access):
        if access.permission is None:
            return False, None

        return True, access.permissionName
