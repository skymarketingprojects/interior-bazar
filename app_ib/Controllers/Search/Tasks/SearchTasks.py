import asyncio
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from asgiref.sync import sync_to_async
from django.http import JsonResponse
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


class SEARCH_TASKS:
    
    @classmethod
    async def PaginateQuery(self,businesses_query):
        page_number = 1
        page_size = 10

        # Fetch the user data asynchronously
        businesses = await sync_to_async(list)(businesses_query)
        paginator = Paginator(businesses, page_size)

        try:
            businesses_page = paginator.page(page_number)
        except PageNotAnInteger:
            businesses_page = paginator.page(1)
        except EmptyPage:
            businesses_page = paginator.page(paginator.num_pages)
            
        data = {
        'businesses': businesses_page,
        'has_next': businesses_page.has_next()
        } 
        return data


    @classmethod
    async def GetQueryData(self,businesses_query):
        try:
            lawyres_data = []
            business_list = []
            
            # pagination : 
            pageingate_lawers = await asyncio.gather(self.PaginateQuery(businesses_query=businesses_query))
            pageingate_lawers = pageingate_lawers[0]

            
            business_list = pageingate_lawers['businesses']
            has_next = pageingate_lawers['has_next']

            # fetch all information 
            for business in business_list:
                lawer_resp = await self.FetchBusiness( business=business)
                lawyres_data.append(lawer_resp)
            
            final_data = {
                'has_next':has_next,
                'data':lawyres_data
            }
            
            return final_data
            
        except Exception as e:
            print(f' Error runing pagination {e}')
            return None


    @classmethod
    async def FetchBusiness(self,business):
        try:
            final_data={}
            print(f'business {business}')
            print(f'user {business.user}')
            user_ins = business.user
            
            # 1. Store Business detail: 
            business_data= await BUSS_TASK.GetBusinessInfo(id=business.pk)
            print(f'business data {business_data}')
            final_data['business']=business_data

            # 2.Store Profile detail: 
            is_profile_ins_exist= await sync_to_async(UserProfile.objects.filter(user=user_ins).exists)()
            print(f'is_profile_ins_exist  {is_profile_ins_exist}')

            if(is_profile_ins_exist):
                profile_ins= await sync_to_async(UserProfile.objects.get)(user=user_ins)
                profile_data= await PROFILE_TASKS.GetProfileDataTask(user_profile_ins=profile_ins)
                print(f'profile date {profile_data}')
                final_data['profile']=profile_data
            
            # 3. Business Profile
            is_profile_ins_exist= await sync_to_async(BusinessProfile.objects.filter(business=business).exists)()
            print(f'is_profile_ins_exist {is_profile_ins_exist}')
            
            if(is_profile_ins_exist):
                business_prof_ins= await sync_to_async(BusinessProfile.objects.get)(business=business)
                business_profile_data= await BUSS_PROF_TASK.GetBusinessProfTask(business_prof_ins=business_prof_ins)
                print(f'business profile data {business_profile_data}')
                final_data['business_profile']=business_profile_data

            # 4. Business Location
            is_business_location_exist= await sync_to_async(Location.objects.filter(business=business).exists)()
            print(f'is_business_location_exist {is_business_location_exist}')
            
            if(is_business_location_exist):
                business_loc_ins= await sync_to_async(Location.objects.get)(business=business)
                business_location_data= await BUSS_LOC_TASK.GetBusinessLocTask(business_loc_ins=business_loc_ins)
                print(f'business location data {business_location_data}')
                final_data['business_location']=business_location_data
            
            # 5. Store business additionla information
            join_date = random.randint(1, 5)
            rating = await MY_METHODS.get_random_rating()

            additional_data={
                'review':f'{rating}',
                'join_year':f'{join_date}'
            }
            final_data['additional']=additional_data
            
            # Add  ID seprately:  
            final_data['id']=business.pk

            return final_data
        except Exception as e:
            print(f'error while fetcing business {e}')
            return None