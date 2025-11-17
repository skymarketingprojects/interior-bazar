from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES

from interior_business.Controllers.Search.SearchController import SEARCH_CONTROLLER


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
        index = request.GET.get('pageNo', 1)
        pageSize = request.GET.get('pageSize', 1)
        tabId = request.GET.get('tabId', None)
        tabType= request.GET.get('type', None)
        state = request.GET.get('state', None)
        query = request.GET.get('query', None)
        
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
                'error': str(e)
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
                'error': str(e)
            })
@api_view(['GET'])
async def GetRelatedBusinessView(request, businessId):
    try:
        pageNo = request.GET.get('pageNo', 1)
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
            message="Error fetching related businesses",
            data={"error": str(e)}
        )

@api_view(['GET'])
async def GetNearbyBusinessView(request, businessId=None):
    try:
        pageNo = request.GET.get('pageNo', 1)
        if not businessId:
            city = request.GET.get('city', None)
            state = request.GET.get('state', None)
        
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
            message="Error fetching nearby businesses",
            data={"error": str(e)}
        )