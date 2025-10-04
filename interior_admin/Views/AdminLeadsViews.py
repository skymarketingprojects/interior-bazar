import asyncio
from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES

import asyncio
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from interior_admin.Controllers.AdminLeads.AdminLeadsController import ADMIN_LEADS_CONTROLLER
from app_ib.Utils.MyMethods import MY_METHODS


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def GetAdminQueryView(request,pageNo,pageSize):
    try:
        user = request.user
        # Call Auth Controller to Create User
        final_response = await  ADMIN_LEADS_CONTROLLER.GetQueries(user_ins=user,pageNo=pageNo,size=pageSize)

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # print(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.query_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def AssignQueryView(request):
    try:
        user = request.user
        data = request.data
        businessId = data.get('businessId',None)
        leadId = data.get('leadId',None)
        #await MY_METHODS.printStatus(status=f"businessId {businessId}--lead {leadId}")
        assignResponse = await ADMIN_LEADS_CONTROLLER.AssignLeadQuery(user_ins=user,businessId=businessId,leadId=leadId)
        return ServerResponse(
            response=assignResponse.response,
            code=assignResponse.code,
            message=assignResponse.message,
            data=assignResponse.data)

    except Exception as e:
        # print(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.query_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })