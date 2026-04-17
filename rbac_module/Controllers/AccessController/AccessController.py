from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.Names import NAMES
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from rbac_module.Controllers.AccessController.Tasks.AccessTasks import ACCESS_TASKS
from rbac_module.models import Access, Role
from app_ib.models import CustomUser
from asgiref.sync import sync_to_async
import asyncio

class ACCESS_CONTROLLER:

    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.access_list_fetch_error,
        successMessage=RESPONSE_MESSAGES.access_list_fetched,
        responseFunc=LocalResponse
    )
    async def getAllAccessList():
        # Batch fetch and serialize
        access_list = await sync_to_async(list)(Access.objects.all())
        data = await ACCESS_TASKS.BulkSerializeAccess(access_list)
        return True, data

    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.access_list_fetch_error,
        successMessage=RESPONSE_MESSAGES.access_list_fetched,
        responseFunc=LocalResponse
    )
    async def getAccessListByRole(role: Role):
        # Fetch related access directly
        access_list = await sync_to_async(lambda: list(role.access.all()))()
        # Filter and map labels efficiently
        labels = [a.permissionName for a in access_list if a.permission is not None]
        return True, labels

    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.access_list_fetch_error,
        successMessage=RESPONSE_MESSAGES.access_list_fetched,
        responseFunc=LocalResponse
    )
    async def getAccessListByUser(cls, User: CustomUser):
        # Heavy optimization: Use an efficient set comprehension over pre-fetched roles
        roles = await sync_to_async(lambda: list(User.roles.all().prefetch_related('access')))()
        access_set = {
            a.permissionName 
            for r in roles 
            for a in r.access.all() 
            if a.permission is not None
        }
        return True, list(access_set)

    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.unauthorized,
        successMessage=RESPONSE_MESSAGES.authorized,
        responseFunc=LocalResponse
    )
    async def checkUserHasAccess(user: CustomUser, accessName: str):
        has_access = await Access.objects.filter(
            permissionName=accessName,
            permission=True,
            roles__users=user
        ).aexists()
        return True, has_access