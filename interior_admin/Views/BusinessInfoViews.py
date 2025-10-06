from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from interior_admin.Controllers.BusinessInfo.BusinessInfoController import BUSINESS_INFO_CONTROLLER
from app_ib.Utils.MyMethods import MY_METHODS
@api_view(['GET'])
# @permission_classes([IsAuthenticated])
async def GetAdminBusinessDataView(request,pageNo,pageSize):
    try:
        # Call Auth Controller to Create User
        await MY_METHODS.printStatus(f'GetAdminBusinessDataView called with pageNo,pageSize:-{pageNo},{pageSize}')
        final_response = await BUSINESS_INFO_CONTROLLER.GetBusinessInfo( pageNo=pageNo,size=pageSize)
        await MY_METHODS.printStatus(f'GetAdminBusinessDataView final response:-{final_response}')


        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        await MY_METHODS.printStatus(f'GetAdminBusinessDataView{str(e)}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })