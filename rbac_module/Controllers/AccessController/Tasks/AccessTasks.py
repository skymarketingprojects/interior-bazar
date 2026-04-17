from rbac_module.models import Access
from app_ib.Utils.Names import NAMES
from app_ib.decorators.ViewDecorator import taskExceptionHandler

class ACCESS_TASKS:

    @staticmethod
    def SerializeAccessSync(access: Access):
        """Unified synchronous serializer for access objects."""
        return {
            NAMES.ID: access.id,
            NAMES.NAME: access.permissionName,
            NAMES.PERMISSION: access.permission
        }

    @staticmethod
    async def getAccessDataTask(access: Access):
        """Maintained for single-item compatibility."""
        return True, ACCESS_TASKS.SerializeAccessSync(access)

    @staticmethod
    async def getAccessForCheck(access: Access):
        """Maintained for single-item compatibility."""
        if access.permission is None:
            return False, None
        return True, access.permissionName

    @staticmethod
    async def BulkSerializeAccess(access_list):
        """High-performance bulk serialization."""
        return [ACCESS_TASKS.SerializeAccessSync(a) for a in access_list]
