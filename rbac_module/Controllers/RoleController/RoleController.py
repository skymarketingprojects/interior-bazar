from asgiref.sync import sync_to_async

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.decorators.ViewDecorator import exceptionHandler,controllerExceptionHandler

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
            lambda: list(
                Role.objects.filter(users=user)
                .prefetch_related(NAMES.ACCESS, NAMES.USERS)
            )
        )()

        data = []

        for role in roles:
            status, role_data = await sync_to_async(
                ROLE_TASKS.getRoleDetailTask
            )(role)

            if status:
                data.append(role_data)

        return True,data

    # ---------- GET ALL ----------
    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_list_fetch_error,
        successMessage=RESPONSE_MESSAGES.role_list_fetched,
        responseFunc=LocalResponse
    )
    async def getAllRoleController():

        roles = await sync_to_async(
            lambda: list(
                Role.objects.all().prefetch_related(NAMES.ACCESS, NAMES.USERS)
            )
        )()

        data = []

        for role in roles:
            status, role_data = await sync_to_async(
                ROLE_TASKS.getRoleDetailTask
            )(role)

            if status:
                data.append(role_data)

        return True,data


    # ---------- GET ONE ----------
    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_fetch_error,
        successMessage=RESPONSE_MESSAGES.role_fetched,
        responseFunc=LocalResponse
    )
    async def getRoleDetailController(roleId: int):

        role = await sync_to_async(Role.objects.get)(id=roleId)

        status, role_data = await sync_to_async(
            ROLE_TASKS.getRoleDetailTask
        )(role)

        if not status:
            raise ValueError(role_data)

        return status,role_data


    # ---------- BY OWNER ----------
    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_list_fetch_error,
        successMessage=RESPONSE_MESSAGES.role_list_fetched,
        responseFunc=LocalResponse
    )
    async def getRolesByOwnerController(user: CustomUser):

        roles = await sync_to_async(
            lambda: list(
                Role.objects.filter(owner=user)
                .prefetch_related(NAMES.ACCESS, NAMES.USERS)
            )
        )()

        data = []

        for role in roles:
            status, role_data = await sync_to_async(
                ROLE_TASKS.getRoleDetailTask
            )(role)

            if status:
                data.append(role_data)

        return status,data


    # ---------- CREATE ----------
    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_create_error,
        successMessage=RESPONSE_MESSAGES.role_create_success,
        responseFunc=LocalResponse
    )
    async def createRoleController(payload, owner):

        status, role_data = await sync_to_async(
            ROLE_TASKS.createRoleTask
        )(payload, owner)

        if not status:
            raise ValueError(role_data)

        return status,role_data


    # ---------- UPDATE ----------
    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_update_error,
        successMessage=RESPONSE_MESSAGES.role_update_success,
        responseFunc=LocalResponse
    )
    async def updateRoleController(user, roleId, payload):

        role = await sync_to_async(Role.objects.get)(
            id=roleId,
            owner=user
        )

        status, role_data = await sync_to_async(
            ROLE_TASKS.updateRoleTask
        )(role, payload)

        if not status:
            raise ValueError(role_data)

        return status,role_data


    # ---------- REMOVE USERS ----------
    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_update_error,
        successMessage=RESPONSE_MESSAGES.role_update_success,
        responseFunc=LocalResponse
    )
    async def removeUserFromRoleController(user, roleId, payload):

        role = await sync_to_async(Role.objects.get)(
            id=roleId,
            owner=user
        )

        status, data = await sync_to_async(
            ROLE_TASKS.removeUserFromRoleTask
        )(role, payload)

        if not status:
            raise ValueError(data)

        return status,data


    # ---------- REMOVE ACCESS ----------
    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_update_error,
        successMessage=RESPONSE_MESSAGES.role_update_success,
        responseFunc=LocalResponse
    )
    async def removeAccessFromRoleController(user, roleId, payload):

        role = await sync_to_async(Role.objects.get)(
            id=roleId,
            owner=user
        )

        status, data = await sync_to_async(
            ROLE_TASKS.removeAccessFromRoleTask
        )(role, payload)

        if not status:
            raise ValueError(data)

        return status,data


    # ---------- DELETE ----------
    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_delete_error,
        successMessage=RESPONSE_MESSAGES.role_delete_success,
        responseFunc=LocalResponse
    )
    async def deleteRoleController(user, roleId):

        role = await sync_to_async(Role.objects.get)(
            id=roleId,
            owner=user
        )

        status, data = await sync_to_async(
            ROLE_TASKS.deleteRoleTask
        )(role)

        if not status:
            raise ValueError(data)

        return status,data
