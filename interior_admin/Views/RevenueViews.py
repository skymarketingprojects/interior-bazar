from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.Revenue.RevenueController import REVENUE_CONTROLLER
from interior_admin.Controllers.Revenue.Validators.RevenueValidators import ExpenseSchema, AssumptionsSchema
from interior_admin.Validators.adminValidators import hasAccess


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def RevenueOverviewView(request: Request):
    """GET /api/v1/admin/revenue/ — revenue & unit-economics aggregates
    (gross/net revenue, MRR proxy, CAC, expenses). Optional ?start=&end= range
    (gross/family/expenses); MRR/ARPU and the 6-month trend stay point-in-time."""
    await hasAccess(request=request)
    q = request.query_params
    return await REVENUE_CONTROLLER.Overview(start=q.get('start') or None, end=q.get('end') or None)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def AddExpenseView(request: Request):
    """POST /api/v1/admin/revenue/expense/ — add an operating expense line."""
    await hasAccess(request=request)
    return await REVENUE_CONTROLLER.AddExpense(payload=ExpenseSchema(**request.data), actor=request.user)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def RevenueAssumptionsView(request: Request):
    """PUT /api/v1/admin/revenue/assumptions/ — edit the unit-economics
    assumptions singleton (avgLifetimeMonths/grossMargin/revenueTarget/newCustomers)."""
    await hasAccess(request=request)
    return await REVENUE_CONTROLLER.SetAssumptions(payload=AssumptionsSchema(**request.data), actor=request.user)
