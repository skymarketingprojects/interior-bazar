from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.Names import NAMES
from app_ib.decorators.ViewDecorator import controllerExceptionHandler

from rbac_module.Controllers.AccessController.Tasks.AccessTasks import ACCESS_TASKS
from rbac_module.models import Access, Role
from app_ib.models import CustomUser


class ACCESS_CONTROLLER:

    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.access_list_fetch_error,
        successMessage=RESPONSE_MESSAGES.access_list_fetched,
        responseFunc=LocalResponse
    )
    async def getAllAccessList():
        """
        Gets all access models
        Loops through access list and fetches each access detail
        """
        AccessDataList = []

        async for access in Access.objects.all().aiterator():
            status, data = await ACCESS_TASKS.getAccessDataTask(access)
            if status:
                AccessDataList.append(data)

        return True, AccessDataList

    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.access_list_fetch_error,
        successMessage=RESPONSE_MESSAGES.access_list_fetched,
        responseFunc=LocalResponse
    )
    async def getAccessListByRole(role: Role):
        """
        Args:
            Role model
        Gets access list from role
        Fetches detailed access data
        """
        AccessDataList = []

        async for access in role.access.all().aiterator():
            status, data = await ACCESS_TASKS.getAccessForCheck(access)
            if status:
                AccessDataList.append(data)

        return True, AccessDataList

    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.access_list_fetch_error,
        successMessage=RESPONSE_MESSAGES.access_list_fetched,
        responseFunc=LocalResponse
    )
    async def getAccessListByUser(cls,User: CustomUser):
        """
        Args:
            User model
        Uses user roles to fetch access list per role
        Combines all access lists into one unique list
        """
        access_set = set()

        async for role in User.roles.all().aiterator():
            response = await cls.getAccessListByRole(role)

            if response.response == RESPONSE_MESSAGES.success:
                access_set.update(response.data)

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