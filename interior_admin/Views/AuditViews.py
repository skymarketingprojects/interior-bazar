from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.Audit.AuditController import AUDIT_CONTROLLER
from interior_admin.Controllers.Audit.Validators.AuditValidators import AuditQueryFilters
from interior_admin.Validators.adminValidators import hasAccess


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(
    errorMessage=RESPONSE_MESSAGES.default_error,
    responseFunc=ServerResponse
)
async def GetAuditLogView(request: Request):
    """GET /api/v1/admin/audit/ — paginated admin audit trail, filterable by
    module / role / date range. Admin-gated."""
    await hasAccess(request=request)
    queryParams = AuditQueryFilters(**request.query_params.dict())
    return await AUDIT_CONTROLLER.GetAuditLog(queryParams=queryParams)
