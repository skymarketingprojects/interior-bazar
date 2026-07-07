from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.Reports.ReportsController import REPORTS_CONTROLLER
from interior_admin.Controllers.Reports.Validators.ReportsValidators import (
    ReportListFilters, ReportSubmitSchema, ReportResolveSchema)
from interior_admin.Validators.adminValidators import hasAccess


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def ReportsListView(request: Request):
    """GET /api/v1/admin/reports/ — paginated report list, filter by status."""
    await hasAccess(request=request)
    return await REPORTS_CONTROLLER.List(queryParams=ReportListFilters(**request.query_params.dict()))


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def ReportResolveView(request: Request, reportId: int):
    """PUT /api/v1/admin/reports/<id>/ — set report status (resolve/dismiss)."""
    await hasAccess(request=request)
    return await REPORTS_CONTROLLER.Resolve(reportId=reportId, payload=ReportResolveSchema(**request.data), actor=request.user)


@api_view(['POST'])
@permission_classes([AllowAny])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def ReportSubmitView(request: Request):
    """POST /api/v1/admin/reports/submit/ — public 'report this listing' submit."""
    reporter = request.user if getattr(request.user, "is_authenticated", False) else None
    return await REPORTS_CONTROLLER.Submit(payload=ReportSubmitSchema(**request.data), reporter=reporter)
