from adrf.decorators import api_view

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.Names import ACCESSLIST
from app_ib.decorators.ViewDecorator import exceptionHandler

import asyncio
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from interior_admin.Controllers.Finance.FinanceController import FINANCE_CONTROLLER
from interior_admin.Validators.adminValidators import hasAccess

from rest_framework.request import Request

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(
    errorMessage=RESPONSE_MESSAGES.finance_fetch_error,
    responseFunc=ServerResponse
)
async def getFinanceDataView(request: Request):
    await hasAccess(request=request)
    
    final_response = await FINANCE_CONTROLLER.GetFinanceData()
    return final_response
