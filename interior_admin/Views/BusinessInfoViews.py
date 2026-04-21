from adrf.decorators import api_view

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES,ACCESSLIST
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.decorators.ViewDecorator import exceptionHandler

from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from interior_admin.Controllers.BusinessInfo.BusinessInfoController import BUSINESS_INFO_CONTROLLER
from rest_framework.request import Request
from interior_admin.Validators.adminValidators import hasAccess
@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def GetAdminBusinessDataView(request,pageNo,pageSize):
    try:
        await hasAccess(request=request)
        # Call Auth Controller to Create User
        pass
        final_response = await BUSINESS_INFO_CONTROLLER.GetBusinessInfo( pageNo=pageNo,size=pageSize)
        pass


        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        pass
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def GetAdminBusinessDataViewV2(request:Request):
    try:
        await hasAccess(request=request)
        pageNo = request.query_params.get(NAMES.PAGE_NO, 1)
        pageSize = request.query_params.get(NAMES.PAGE_SIZE, 10)

        # Call Auth Controller to Create User
        pass
        final_response = await BUSINESS_INFO_CONTROLLER.GetBusinessInfo( pageNo=pageNo,size=pageSize)
        pass


        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        pass
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@exceptionHandler(
    errorMessage=RESPONSE_MESSAGES.business_delete_error,
    responseFunc=ServerResponse
)
async def DeleteBusinessDataView(request:Request,businessId):
    await hasAccess(request=request)
    # Call Auth Controller to Create User
    final_response = await BUSINESS_INFO_CONTROLLER.DeleteBusinessInfo(businessId=businessId)
    return final_response
