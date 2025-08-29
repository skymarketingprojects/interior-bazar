import random
import asyncio
from profile import Profile
from adrf.decorators import api_view
from asgiref.sync import sync_to_async
from django.http import JsonResponse
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.models import Business, Location, BusinessProfile, UserProfile
from app_ib.Controllers.BusinessProfile.Tasks.BusinessProfileTasks import BUSS_PROF_TASK
from app_ib.Controllers.Profile.Tasks.Taskys import PROFILE_TASKS
from app_ib.Controllers.Business.Tasks.BusinessTasks import BUSS_TASK
from app_ib.Controllers.BussLocation.Tasks.BusinessLocationTasks import BUSS_LOC_TASK
from app_ib.Utils.MyMethods import MY_METHODS
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
        final_response= await SEARCH_CONTROLLER.GetBusinessUsingPagination()
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

