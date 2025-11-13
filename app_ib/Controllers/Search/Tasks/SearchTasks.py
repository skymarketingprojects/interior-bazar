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
from django.utils import timezone
from datetime import timedelta
from app_ib.Utils.Names import NAMES
class SEARCH_TASKS:
    
    @classmethod
    async def PaginateQuery(self,businesses_query,PageNo):
        page_number = PageNo
        page_size = 6 # for production 3 for testing

        # Fetch the user data asynchronously
        businesses = await sync_to_async(list)(businesses_query)
        paginator = Paginator(businesses, page_size)

        try:
            businesses_page = paginator.page(page_number)
        except PageNotAnInteger:
            businesses_page = paginator.page(int(page_number))
        except EmptyPage:
            businesses_page = paginator.page(paginator.num_pages)
            
        data = {
        NAMES.BUSINESSES: businesses_page,
        NAMES.HAS_NEXT: businesses_page.has_next(),
        NAMES.TOTAL_PAGES: paginator.num_pages,
        NAMES.PAGE_NO: page_number
        } 
        return data


    @classmethod
    async def GetQueryData(self,businesses_query,pageNo):
        try:
            lawyres_data = []
            business_list = []
            
            # pagination : 
            pageingate_lawers = await asyncio.gather(self.PaginateQuery(businesses_query=businesses_query,PageNo=pageNo))
            pageingate_lawers = pageingate_lawers[0]

            
            business_list = pageingate_lawers[NAMES.BUSINESSES]
            has_next = pageingate_lawers[NAMES.HAS_NEXT]
            totalPage = pageingate_lawers[NAMES.TOTAL_PAGES]
            pageNo = pageingate_lawers[NAMES.PAGE_NO]

            # fetch all information 
            for business in business_list:
                lawer_resp = await self.FetchBusiness( business=business)
                lawyres_data.append(lawer_resp)
            
            final_data = {
                NAMES.HAS_NEXT:has_next,
                NAMES.TOTAL_PAGES:totalPage,
                NAMES.PAGE_NO:pageNo,
                NAMES.DATA:lawyres_data
            }
            
            return final_data
            
        except Exception as e:
            await MY_METHODS.printStatus(f' Error runing pagination {e}')
            return None


    @classmethod
    async def FetchBusiness(self, business):
        try:
            final_data = {}
            await MY_METHODS.printStatus(f'business {business}')
            user_ins = business.user

            # Use asyncio.gather to fetch data in parallel for faster performance
            business_data, business_location_data = await asyncio.gather(
                BUSS_TASK.GetBusinessInfo(id=business.pk),
                BUSS_LOC_TASK.GetBusinessLocTask(business_loc_ins=await sync_to_async(Location.objects.get)(business=business) if await sync_to_async(Location.objects.filter(business=business).exists)() else None)
            )
            await MY_METHODS.printStatus(f'\nbusiness_data {business_data}\n')

            # Handle time ago logic
            timestamp = business_data.get(NAMES.TIMESTAMP, None)
            time_ago = await MY_METHODS.get_time_ago(updated_at=timestamp)
            
            await MY_METHODS.printStatus(f"time_ago {time_ago}, timestamp {timestamp}")

            # Assign the required fields to final_data in camelCase format
            final_data[NAMES.ID] = business.pk
            final_data[NAMES.BUSINESS_NAME] = business_data.get(NAMES.BUSINESS_NAME, NAMES.EMPTY)
            final_data[NAMES.COMPANY_NAME] = business_data.get(NAMES.BUSINESS_NAME, NAMES.EMPTY)
            final_data[NAMES.MEMBERSHIP_ID] = business.pk
            final_data[NAMES.BADGE] = business_data.get(NAMES.BADGE, NAMES.EMPTY)
            final_data[NAMES.TIME_AGO] = str(time_ago)  # Add the timeAgo field
            final_data[NAMES.SINCE] = business_data.get(NAMES.SINCE, NAMES.EMPTY)
            # final_data['category'] = business_data.get('category', NAMES.EMPTY)
            final_data[NAMES.BUSINESS_IMAGE] = business_data.get(NAMES.COVER_IMAGE_URL, NAMES.EMPTY)
            final_data[NAMES.CITY] = business_location_data.get(NAMES.CITY, NAMES.EMPTY)
            final_data[NAMES.STATE] = business_location_data.get(NAMES.STATE, NAMES.EMPTY)
            final_data[NAMES.COUNTRY] = business_location_data.get(NAMES.COUNTRY, NAMES.EMPTY)
            final_data[NAMES.PINCODE] = business_location_data.get(NAMES.PINCODE, NAMES.EMPTY)
            # final_data['category'] = business_data.get('categories', [])



            # Handle location
            location_data = business_location_data if business_location_data else {}
            city = f"{location_data.get(NAMES.CITY, None)} ," if location_data.get(NAMES.CITY) else None 
            state = f"{location_data.get(NAMES.STATE, None)[NAMES.NAME]} ," if location_data.get(NAMES.STATE) else None
            country = f"{location_data.get(NAMES.COUNTRY, None)[NAMES.NAME]}" if location_data.get(NAMES.COUNTRY) else None
            await MY_METHODS.printStatus(f'state {state} country {country}')
            final_data[NAMES.LOCATION] = f"{city if city else NAMES.EMPTY}{state if state else NAMES.EMPTY}{country if country else NAMES.EMPTY}"
            # Handle rating - assuming you still want a random rating for the example
            rating = await MY_METHODS.get_random_rating()
            final_data[NAMES.RATING] = f"{rating}"
            final_data[NAMES.RATING_VALUE] = float(rating)
            await MY_METHODS.printStatus(f'final_data {final_data}')

            return final_data
        except Exception as e:
            await MY_METHODS.printStatus(f'Error while fetching business {e}')
            return None