from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES

from interior_business.Controllers.Search.SearchController import SEARCH_CONTROLLER
from app_ib.Utils.Names import NAMES

# #########################################
# 1. Add profile data to obj: 
# 2. Add Business data obj: 
# 3. Add Business Location data obj: 
# 4. Add Business Profile data obj: 
# 5. Add additional data {reviews, join_date} 
# #########################################
@api_view(['GET'])
async def GetBusinessByPaginationView(request):
    try:
        index = request.GET.get(NAMES.PAGE_NO, 1)
        pageSize = request.GET.get(NAMES.PAGE_SIZE, 1)
        tabId = request.GET.get(NAMES.TAB_ID, None)
        tabType= request.GET.get(NAMES.TYPE, None)
        state = request.GET.get(NAMES.STATE, None)
        query = request.GET.get(NAMES.QUERY, None)
        
        final_response= await SEARCH_CONTROLLER.GetBusinessUsingPagination(pageNo=index,pageSize=pageSize,tabId=tabId,tabType=tabType,state=state,query=query)
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
        # index = request.GET.get(NAMES.PAGE_NO, 1)
        pageSize = request.GET.get(NAMES.PAGE_SIZE, 1)
        tabId = request.GET.get(NAMES.TAB_ID, None)
        tabType= request.GET.get(NAMES.TYPE, None)
        state = request.GET.get(NAMES.STATE, None)
        query = request.GET.get(NAMES.QUERY, None)

        final_response= await SEARCH_CONTROLLER.GetTopBusiness(index=index,pageSize=pageSize,tabId=tabId,tabType=tabType,state=state,query=query)
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
async def GetRelatedBusinessView(request, businessId):
    try:
        pageNo = request.GET.get(NAMES.PAGE_NO, 1)
        final_response = await SEARCH_CONTROLLER.GetRelatedBusiness(businessId=businessId, pageNo=pageNo)
        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
        )
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            code=RESPONSE_CODES.error,
            message='Error fetching related businesses',
            data={NAMES.ERROR: str(e)}
        )

@api_view(['GET'])
async def GetNearbyBusinessView(request, businessId=None):
    try:
        pageNo = request.GET.get(NAMES.PAGE_NO, 1)
        if not businessId:
            city = request.GET.get(NAMES.CITY, None)
            state = request.GET.get(NAMES.STATE, None)
        
            final_response = await SEARCH_CONTROLLER.GetNearbyBusiness(city=city,state=state, pageNo=pageNo)
        else:
            final_response = await SEARCH_CONTROLLER.GetNearbyBusiness(businessId=businessId, pageNo=pageNo)
        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
        )
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            code=RESPONSE_CODES.error,
            message='Error fetching nearby businesses',
            data={NAMES.ERROR: str(e)}
        )