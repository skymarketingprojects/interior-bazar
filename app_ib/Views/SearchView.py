from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES

from app_ib.Controllers.Search.SearchController import SEARCH_CONTROLLER


# #########################################
# 1. Add profile data to obj: 
# 2. Add Business data obj: 
# 3. Add Business Location data obj: 
# 4. Add Business Profile data obj: 
# 5. Add additional data {reviews, join_date} 
# #########################################
@api_view(['GET'])
async def GetBusinessByPaginationView(request,index):
    try:
        final_response= await SEARCH_CONTROLLER.GetBusinessUsingPagination(pageNo=index)
        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.default_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

@api_view(['GET'])
async def GetTopBusinessView(request,index):
    try:
        final_response= await SEARCH_CONTROLLER.GetTopBusiness(index=index)
        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.default_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })