from asgiref.sync import sync_to_async
from django.core.cache import cache


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
        # Fetch all roles (uses global cache)
        status, all_roles = await ROLE_CONTROLLER.getAllRoleController()
        if not status:
            return False, all_roles

        # Filter in-memory for roles assigned to this user
        user_roles = [
            role for role in all_roles 
            if any(u[NAMES.ID] == user.id for u in role.get(NAMES.USERS, []))
        ]

        return True, user_roles


    # ---------- GET ALL ----------
    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_list_fetch_error,
        successMessage="DEBUG: All roles fetched successfully",
        responseFunc=LocalResponse
    )
    async def getAllRoleController():
        cache_key = "all_rbac_roles"
        cached_data = cache.get(cache_key)
        if cached_data:
            return True, cached_data

        roles = await sync_to_async(
            lambda: list(
                Role.objects.all().prefetch_related(NAMES.ACCESS, NAMES.USERS)
            )
        )()

        data = []

        for role in roles:
            status, role_data = await ROLE_TASKS.getRoleDetailTask(role)
            print(f"DEBUG: Role {role.name} status: {status}")

            if status:
                data.append(role_data)
        
        print(f"DEBUG: Final data length: {len(data)}")
        cache.set(cache_key, data, 86400)  # Cache for 24 hours
        return True,data


    # ---------- GET ONE ----------
    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_fetch_error,
        successMessage=RESPONSE_MESSAGES.role_fetched,
        responseFunc=LocalResponse
    )
    async def getRoleDetailController(roleId: int):
        cache_key = f"role_detail_{roleId}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return True, cached_data

        role = await sync_to_async(Role.objects.get)(id=roleId)

        status, role_data = await ROLE_TASKS.getRoleDetailTask(role)

        if not status:
            raise ValueError(role_data)

        cache.set(cache_key, role_data, 86400)  # Cache for 24 hours
        return status,role_data


    # ---------- BY OWNER ----------
    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_list_fetch_error,
        successMessage=RESPONSE_MESSAGES.role_list_fetched,
        responseFunc=LocalResponse
    )
    async def getRolesByOwnerController(user: CustomUser):
        # Fetch all roles (uses global cache)
        status, all_roles = await ROLE_CONTROLLER.getAllRoleController()
        if not status:
            return False, all_roles

        # Filter in-memory for roles owned by this user
        owner_roles = [
            role for role in all_roles 
            if role.get(NAMES.OWNER) and role[NAMES.OWNER][NAMES.ID] == user.id
        ]

        return True, owner_roles



    # ---------- CREATE ----------
    @staticmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_create_error,
        successMessage=RESPONSE_MESSAGES.role_create_success,
        responseFunc=LocalResponse
    )
    async def createRoleController(payload, owner):

        status, role_data = await ROLE_TASKS.createRoleTask(payload, owner)

        if not status:
            raise ValueError(role_data)

        cache.delete("all_rbac_roles")


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
        )

        status, role_data = await ROLE_TASKS.updateRoleTask(role, payload)

        if not status:
            raise ValueError(role_data)

        cache.delete(f"role_detail_{roleId}")
        cache.delete("all_rbac_roles")


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

        status, data = await ROLE_TASKS.removeUserFromRoleTask(role, payload)

        if not status:
            raise ValueError(data)

        cache.delete(f"role_detail_{roleId}")
        cache.delete("all_rbac_roles")

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

        status, data = await ROLE_TASKS.removeAccessFromRoleTask(role, payload)

        if not status:
            raise ValueError(data)

        cache.delete(f"role_detail_{roleId}")
        cache.delete("all_rbac_roles")

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

        status, data = await ROLE_TASKS.deleteRoleTask(role)

        if not status:
            raise ValueError(data)

        cache.delete(f"role_detail_{roleId}")
        cache.delete("all_rbac_roles")


        return status,data
