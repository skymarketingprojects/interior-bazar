from asgiref.sync import sync_to_async
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from rbac_module.models import Role
from interior_admin.models import AdminModuleAccess
from interior_admin.Controllers.Audit.AuditController import append_audit
from .rbac_matrix import MODULE_KEYS
from .Validators.RolesValidators import RoleUpdateSchema, RoleCreateSchema


class RolesController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def MePermissions(cls, user) -> Tuple[bool, Dict[str, Any]]:
        """Resolve the acting user's role + module levels for the RBAC store.
        super_admin (is_full_access) → level 3 everywhere. No role → all 0."""
        if not getattr(user, "is_authenticated", False):
            return True, {"role": None, "modules": {k: 0 for k in MODULE_KEYS}}

        # Django superusers get full access even without an explicit role row
        if getattr(user, "is_superuser", False):
            return True, {"role": "super_admin", "modules": {k: 3 for k in MODULE_KEYS}}

        role = await sync_to_async(lambda: user.roles.order_by("-is_full_access", "id").first())()
        if role is None:
            return True, {"role": None, "modules": {k: 0 for k in MODULE_KEYS}}
        if role.is_full_access:
            return True, {"role": role.name, "modules": {k: 3 for k in MODULE_KEYS}}

        cells = await sync_to_async(list)(AdminModuleAccess.objects.filter(role=role).values_list("moduleKey", "level"))
        levels = {k: 0 for k in MODULE_KEYS}
        levels.update({m: l for m, l in cells})
        return True, {"role": role.name, "modules": levels}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def ListRoles(cls) -> Tuple[bool, Dict[str, Any]]:
        roles = await sync_to_async(list)(Role.objects.all().prefetch_related("module_access"))
        out = []
        for r in roles:
            if r.is_full_access:
                modules = {k: 3 for k in MODULE_KEYS}
            else:
                cells = await sync_to_async(lambda r=r: {c.moduleKey: c.level for c in r.module_access.all()})()
                modules = {k: cells.get(k, 0) for k in MODULE_KEYS}
            out.append({"name": r.name, "isFullAccess": r.is_full_access, "modules": modules})
        return True, {"roles": out, "moduleKeys": MODULE_KEYS}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def UpdateRole(cls, payload: RoleUpdateSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        role = await Role.objects.filter(name=payload.roleName).afirst()
        if role is None:
            return False, {"message": f"Role '{payload.roleName}' not found"}
        if role.is_full_access:
            return False, {"message": "super_admin is full-access and not editable"}
        for mod, level in (payload.modules or {}).items():
            if mod not in MODULE_KEYS:
                continue
            lvl = max(0, min(3, int(level)))
            await AdminModuleAccess.objects.aupdate_or_create(
                role=role, moduleKey=mod, defaults={"level": lvl})
        await append_audit(actor=actor, action='role_matrix_updated', module_key='roles',
                           detail=f"role={payload.roleName} changed={list((payload.modules or {}).keys())}")
        cells = await sync_to_async(lambda: {c.moduleKey: c.level for c in role.module_access.all()})()
        modules = {k: cells.get(k, 0) for k in MODULE_KEYS}
        return True, {"name": role.name, "isFullAccess": role.is_full_access, "modules": modules}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def CreateRole(cls, payload: RoleCreateSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        """Create a non-full-access role and seed its module-access cells from
        payload.modules (clamped 0..3, only known MODULE_KEYS). Rejects duplicate
        names. Super-admin only — the view enforces the 403 guard."""
        name = (payload.name or "").strip()
        if not name:
            return False, {"message": "Role name is required"}
        if await Role.objects.filter(name=name).aexists():
            return False, {"message": f"Role '{name}' already exists"}
        role = await Role.objects.acreate(name=name, is_full_access=False)
        for mod, level in (payload.modules or {}).items():
            if mod not in MODULE_KEYS:
                continue
            lvl = max(0, min(3, int(level)))
            await AdminModuleAccess.objects.aupdate_or_create(
                role=role, moduleKey=mod, defaults={"level": lvl})
        await append_audit(actor=actor, action='role_created', module_key='roles',
                           detail=f"role={name}")
        cells = await sync_to_async(lambda: {c.moduleKey: c.level for c in role.module_access.all()})()
        modules = {k: cells.get(k, 0) for k in MODULE_KEYS}
        return True, {"name": role.name, "isFullAccess": role.is_full_access, "modules": modules}


ROLES_CONTROLLER = RolesController()
