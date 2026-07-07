from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.Roles.RolesController import ROLES_CONTROLLER
from interior_admin.Controllers.Roles.Validators.RolesValidators import RoleUpdateSchema
from interior_admin.Validators.adminValidators import hasAccess


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def RolesView(request: Request):
    """GET /api/v1/admin/roles/ — role→module→level matrix for the editor grid.
    PUT /api/v1/admin/roles/ — update one role's module levels (super-admin,
    level-3 audited). Body: {roleName, modules:{key:level}}."""
    await hasAccess(request=request)
    if request.method == 'PUT':
        return await ROLES_CONTROLLER.UpdateRole(payload=RoleUpdateSchema(**request.data), actor=request.user)
    return await ROLES_CONTROLLER.ListRoles()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def MePermissionsView(request: Request):
    """GET /api/v1/admin/me/permissions/ — {role, modules:{key:level}} for the
    JWT user. The v3 admin app hydrates its RBAC store from this."""
    return await ROLES_CONTROLLER.MePermissions(user=request.user)
