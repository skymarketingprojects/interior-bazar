import asyncio
from asgiref.sync import sync_to_async
from django.db import transaction
from rbac_module.models import Role, Access
from rbac_module.Controllers.AccessController.AccessController import ACCESS_CONTROLLER
from rbac_module.Controllers.RoleController.Validators.RoleValidators import (
    RoleAccessUpdateSchema,
    RoleCreateSchema,
    RoleAssignUsersSchema
)
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.models import CustomUser as User
from app_ib.decorators.ViewDecorator import taskExceptionHandler

class ROLE_TASKS:

    @classmethod
    async def BulkSerializeRoles(cls, role_list):
        """Unified bulk serialization for roles (requires pre-fetched access and users)."""
        results = []
        for role in role_list:
            try:
                access_list = [a.permissionName for a in role.access.all() if a.permission is not None]
                user_list = [{NAMES.ID: u.id, NAMES.NAME: u.username} for u in role.users.all()]
                owner = role.owner
                
                results.append({
                    NAMES.ID: role.id,
                    NAMES.NAME: role.name,
                    NAMES.ACCESS_LIST: access_list,
                    NAMES.OWNER: ({NAMES.ID: owner.id, NAMES.NAME: owner.username} if owner else None),
                    NAMES.USERS: user_list,
                    NAMES.CREATED_AT: role.createdAt,
                    NAMES.UPDATED_AT: role.updatedAt
                })
            except: pass
        return results

    @classmethod
    @taskExceptionHandler
    async def getRoleDetailTask(cls, role: Role):
        # Fetch with pre-fetching for bulk compatibility
        role_qs = Role.objects.filter(pk=role.pk).select_related('owner').prefetch_related('access', 'users')
        objs = await sync_to_async(list)(role_qs)
        results = await cls.BulkSerializeRoles(objs)
        return True, results[0] if results else None

    @classmethod
    @taskExceptionHandler
    async def createRoleTask(cls, data: RoleCreateSchema, owner=None):
        @sync_to_async
        def _create():
            with transaction.atomic():
                role = Role.objects.create(name=data.name, owner=owner)
                if data.accessIds:
                    accesses = Access.objects.filter(id__in=data.accessIds)
                    role.access.set(accesses)
                if data.userIds:
                    users = User.objects.filter(id__in=data.userIds)
                    role.users.set(users)
                return role
        role = await _create()
        return await cls.getRoleDetailTask(role)

    @classmethod
    @taskExceptionHandler
    async def updateRoleTask(cls, role: Role, data: RoleCreateSchema):
        @sync_to_async
        def _update():
            with transaction.atomic():
                if data.name is not None: role.name = data.name
                if data.accessIds is not None:
                    accesses = Access.objects.filter(id__in=data.accessIds)
                    role.access.set(accesses)
                if data.userIds is not None:
                    users = User.objects.filter(id__in=data.userIds)
                    role.users.set(users)
                role.save()
                return role
        role = await _update()
        return await cls.getRoleDetailTask(role)

    @classmethod
    @taskExceptionHandler
    async def removeUserFromRoleTask(cls, role: Role, data: RoleAssignUsersSchema):
        @sync_to_async
        def _remove():
            users = User.objects.filter(id__in=data.userIds)
            role.users.remove(*users)
        await _remove()
        return True, "Users removed from role"

    @classmethod
    @taskExceptionHandler
    async def removeAccessFromRoleTask(cls, role: Role, data: RoleAccessUpdateSchema):
        @sync_to_async
        def _remove():
            accesses = Access.objects.filter(id__in=data.accessIds)
            role.access.remove(*accesses)
        await _remove()
        return True, "Access removed from role"

    @classmethod
    @taskExceptionHandler
    async def deleteRoleTask(cls, role: Role):
        can_delete = await sync_to_async(role.can_delete)()
        if not can_delete:
            return False, "Role has users assigned and cannot be deleted"
        await sync_to_async(role.delete)()
        return True, "Role deleted successfully"
