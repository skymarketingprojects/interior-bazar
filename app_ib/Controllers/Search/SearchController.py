
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
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Controllers.Search.Tasks.SearchTasks import SEARCH_TASKS

class SEARCH_CONTROLLER:
    @classmethod
    async def GetBusinessUsingPagination(self,pageNo):
        try:
            # Getting all business instance: 
            businesses_query = await sync_to_async(list)(Business.objects.all())

            # fetch business data:
            business_data= await SEARCH_TASKS.GetQueryData(businesses_query=businesses_query,pageNo=pageNo)

            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_fetch_success,
                data=business_data)

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })

    @classmethod
    async def GetTopBusiness(self,index):
        try:
            # Getting all business instance: 
            businesses_query = await sync_to_async(list)(Business.objects.all())

            # fetch business data:
            business_data= await SEARCH_TASKS.GetQueryData(businesses_query=businesses_query,pageNo=index)

            business_data['topSeller'] = business_data['data'][:5]
            business_data['businesses'] = business_data.pop('data')

            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_fetch_success,
                data=business_data)

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })