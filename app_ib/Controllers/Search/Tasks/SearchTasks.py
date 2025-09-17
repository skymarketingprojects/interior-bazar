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

class SEARCH_TASKS:
    
    @classmethod
    async def PaginateQuery(self,businesses_query,PageNo):
        page_number = PageNo
        page_size = 10

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
        'businesses': businesses_page,
        'has_next': businesses_page.has_next()
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

            # Handle time ago logic
            updated_at = business_data.get('updated_at', None)
            time_ago = await sync_to_async(self.get_time_ago)(updated_at)  # Wrap with sync_to_async

            # Assign the required fields to final_data in camelCase format
            final_data['id'] = business.pk
            final_data['businessName'] = business_data.get('business_name', '')
            final_data['companyName'] = business_data.get('business_name', '')
            final_data['membershipId'] = business.pk
            final_data['badge'] = business_data.get('badge', '')
            final_data['timeAgo'] = time_ago  # Add the timeAgo field
            final_data['since'] = business_data.get('since', '')
            final_data['category'] = business_data.get('category', '')
            final_data['businessImage'] = business_data.get('cover_image_url', '')

            # Handle location
            location_data = business_location_data if business_location_data else {}
            city = f"{location_data.get('city', None)} ," if location_data.get('city') else None 
            state = f"{location_data.get('state', None)} ," if location_data.get('state') else None
            country = f"{location_data.get('country', None)}" if location_data.get('country') else None
            final_data['location'] = f"{city}{state}{country}"
            # Handle rating - assuming you still want a random rating for the example
            rating = await MY_METHODS.get_random_rating()
            final_data['rating'] = f"{rating}"
            final_data['ratingValue'] = float(rating)  # ratingValue as number

            return final_data
        except Exception as e:
            await MY_METHODS.printStatus(f'Error while fetching business {e}')
            return None

    @staticmethod
    def get_time_ago(updated_at):
        if updated_at:
            # Calculate the time difference between now and updated_at
            time_diff = timezone.now() - updated_at

            # Determine the number of seconds, minutes, hours, and days
            if time_diff < timedelta(minutes=1):
                return "Just now"
            elif time_diff < timedelta(hours=1):
                minutes = time_diff.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            elif time_diff < timedelta(days=1):
                hours = time_diff.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif time_diff < timedelta(weeks=1):
                days = time_diff.days
                return f"{days} day{'s' if days > 1 else ''} ago"
            elif time_diff < timedelta(weeks=4):
                weeks = time_diff.days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            else:
                months = time_diff.days // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
        return "No update available"