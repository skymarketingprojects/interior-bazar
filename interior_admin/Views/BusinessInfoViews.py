import asyncio
from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES

import asyncio
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from interior_admin.Controllers.BusinessInfo.BusinessInfoController import BUSINESS_INFO_CONTROLLER

@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def GetAdminBusinessDataView(request,pageNo,pageSize):
    try:
        # Call Auth Controller to Create User
        final_response = await BUSINESS_INFO_CONTROLLER.GetBusinessInfo( pageNo=pageNo,size=pageSize)

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # print(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })