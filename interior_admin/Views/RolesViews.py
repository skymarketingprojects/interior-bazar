from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from django.core.exceptions import PermissionDenied

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.Roles.RolesController import ROLES_CONTROLLER
from interior_admin.Controllers.Roles.Validators.RolesValidators import RoleUpdateSchema, RoleCreateSchema
from interior_admin.Validators.adminValidators import hasAccess


async def _require_super_admin(user):
    """RBAC editing is super-admin only (real security, not just nav gating).
    Resolve the acting user's top role and 403 unless it's full-access."""
    role = await sync_to_async(lambda: user.roles.order_by("-is_full_access", "id").first())()
    if role is None or not role.is_full_access:
        raise PermissionDenied(RESPONSE_MESSAGES.unauthorized)


@api_view(['GET', 'PUT', 'POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def RolesView(request: Request):
    """GET /api/v1/admin/roles/ — role→module→level matrix for the editor grid.
    PUT /api/v1/admin/roles/ — update one role's module levels (super-admin only,
    level-3 audited). Body: {roleName, modules:{key:level}}.
    POST /api/v1/admin/roles/ — create a role (super-admin only). Body: {name, modules}."""
    await hasAccess(request=request)
    if request.method == 'PUT':
        await _require_super_admin(request.user)
        return await ROLES_CONTROLLER.UpdateRole(payload=RoleUpdateSchema(**request.data), actor=request.user)
    if request.method == 'POST':
        await _require_super_admin(request.user)
        return await ROLES_CONTROLLER.CreateRole(payload=RoleCreateSchema(**request.data), actor=request.user)
    return await ROLES_CONTROLLER.ListRoles()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def MePermissionsView(request: Request):
    """GET /api/v1/admin/me/permissions/ — {role, modules:{key:level}} for the
    JWT user. The v3 admin app hydrates its RBAC store from this."""
    return await ROLES_CONTROLLER.MePermissions(user=request.user)
