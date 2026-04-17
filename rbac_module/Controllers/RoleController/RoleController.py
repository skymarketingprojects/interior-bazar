from asgiref.sync import sync_to_async
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.decorators.ViewDecorator import exceptionHandler, controllerExceptionHandler
from app_ib.models import CustomUser
from rbac_module.models import Role
from rbac_module.Controllers.RoleController.Tasks.RoleTasks import ROLE_TASKS

class ROLE_CONTROLLER:

    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_create_error,
        successMessage=RESPONSE_MESSAGES.role_create_success,
        responseFunc=LocalResponse
    )
    async def getRolesByUserController(user: CustomUser):
        roles = await sync_to_async(
            lambda: list(Role.objects.filter(users=user).select_related('owner').prefetch_related('access', 'users'))
        )()
        data = await ROLE_TASKS.BulkSerializeRoles(roles)
        return True, data

    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_list_fetch_error,
        successMessage="All roles fetched successfully",
        responseFunc=LocalResponse
    )
    async def getAllRoleController():
        roles = await sync_to_async(
            lambda: list(Role.objects.all().select_related('owner').prefetch_related('access', 'users'))
        )()
        data = await ROLE_TASKS.BulkSerializeRoles(roles)
        return True, data

    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_fetch_error,
        successMessage=RESPONSE_MESSAGES.role_fetched,
        responseFunc=LocalResponse
    )
    async def getRoleDetailController(roleId: int):
        role_qs = Role.objects.filter(id=roleId).select_related('owner').prefetch_related('access', 'users')
        role_list = await sync_to_async(list)(role_qs)
        if not role_list: raise ValueError("Role not found")
        data = await ROLE_TASKS.BulkSerializeRoles(role_list)
        return True, data[0]

    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_list_fetch_error,
        successMessage=RESPONSE_MESSAGES.role_list_fetched,
        responseFunc=LocalResponse
    )
    async def getRolesByOwnerController(user: CustomUser):
        roles = await sync_to_async(
            lambda: list(Role.objects.filter(owner=user).select_related('owner').prefetch_related('access', 'users'))
        )()
        data = await ROLE_TASKS.BulkSerializeRoles(roles)
        return True, data

    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_create_error,
        successMessage=RESPONSE_MESSAGES.role_create_success,
        responseFunc=LocalResponse
    )
    async def createRoleController(payload, owner):
        status, role_data = await ROLE_TASKS.createRoleTask(payload, owner)
        if not status: raise ValueError(role_data)
        return status, role_data

    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_update_error,
        successMessage=RESPONSE_MESSAGES.role_update_success,
        responseFunc=LocalResponse
    )
    async def updateRoleController(user, roleId, payload):
        role = await sync_to_async(Role.objects.get)(id=roleId)
        status, role_data = await ROLE_TASKS.updateRoleTask(role, payload)
        if not status: raise ValueError(role_data)
        return status, role_data

    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_update_error,
        successMessage=RESPONSE_MESSAGES.role_update_success,
        responseFunc=LocalResponse
    )
    async def removeUserFromRoleController(user, roleId, payload):
        role = await sync_to_async(Role.objects.get)(id=roleId, owner=user)
        status, data = await ROLE_TASKS.removeUserFromRoleTask(role, payload)
        if not status: raise ValueError(data)
        return status, data

    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_update_error,
        successMessage=RESPONSE_MESSAGES.role_update_success,
        responseFunc=LocalResponse
    )
    async def removeAccessFromRoleController(user, roleId, payload):
        role = await sync_to_async(Role.objects.get)(id=roleId, owner=user)
        status, data = await ROLE_TASKS.removeAccessFromRoleTask(role, payload)
        if not status: raise ValueError(data)
        return status, data

    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_delete_error,
        successMessage=RESPONSE_MESSAGES.role_delete_success,
        responseFunc=LocalResponse
    )
    async def deleteRoleController(user, roleId):
        role = await sync_to_async(Role.objects.get)(id=roleId, owner=user)
        status, data = await ROLE_TASKS.deleteRoleTask(role)
        if not status: raise ValueError(data)
        return status, data
