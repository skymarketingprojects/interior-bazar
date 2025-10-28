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
from django.db.models import Q

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
        'businesses': businesses_page,
        'hasNext': businesses_page.has_next(),
        'totalPage': paginator.num_pages,
        'pageNo': page_number
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
            has_next = pageingate_lawers['hasNext']
            totalPage = pageingate_lawers['totalPage']
            pageNo = pageingate_lawers['pageNo']

            # fetch all information 
            for business in business_list:
                lawer_resp = await self.FetchBusiness( business=business)
                lawyres_data.append(lawer_resp)
            
            final_data = {
                'hasNext':has_next,
                'totalPage':totalPage,
                'pageNo':pageNo,
                'data':lawyres_data
            }
            
            return final_data
            
        except Exception as e:
            #await MY_METHODS.printStatus(f' Error runing pagination {e}')
            return None


    @classmethod
    async def FetchBusiness(self, business):
        try:
            final_data = {}
            #await MY_METHODS.printStatus(f'business {business}')
            user_ins = business.user

            # Use asyncio.gather to fetch data in parallel for faster performance
            business_data, business_location_data = await asyncio.gather(
                BUSS_TASK.GetBusinessInfo(id=business.pk),
                BUSS_LOC_TASK.GetBusinessLocTask(business_loc_ins=await sync_to_async(Location.objects.get)(business=business) if await sync_to_async(Location.objects.filter(business=business).exists)() else None)
            )
            #await MY_METHODS.printStatus(f'\nbusiness_data {business_data}\n')

            # Handle time ago logic
            timestamp = business_data.get('timestamp', None)
            time_ago = await self.get_time_ago(updated_at=timestamp)
            
            #await MY_METHODS.printStatus(f"time_ago {time_ago}, timestamp {timestamp}")

            # Assign the required fields to final_data in camelCase format
            final_data['id'] = business.pk
            final_data['businessName'] = business_data.get('businessName', '')
            final_data['companyName'] = business_data.get('businessName', '')
            final_data['membershipId'] = business.pk
            final_data['badge'] = business_data.get('badge', '')
            final_data['timeAgo'] = str(time_ago)  # Add the timeAgo field
            final_data['since'] = business_data.get('since', '')
            # final_data['category'] = business_data.get('category', '')
            final_data['businessImage'] = business_data.get('coverImageUrl', '')
            final_data['city'] = business_location_data.get('city', '')
            final_data['state'] = business_location_data.get('state', '')
            final_data['country'] = business_location_data.get('country', '')
            final_data['pincode'] = business_location_data.get('pin_code', '')
            # final_data['category'] = business_data.get('categories', [])



            # Handle location
            location_data = business_location_data if business_location_data else {}
            city = f"{location_data.get('city', None)} ," if location_data.get('city') else None 
            state = f"{location_data.get('state', None)['name']} ," if location_data.get('state') else None
            country = f"{location_data.get('country', None)['name']}" if location_data.get('country') else None
            #await MY_METHODS.printStatus(f'state {state} country {country}')
            final_data['location'] = f"{city if city else ''}{state if state else ''}{country if country else ''}"
            # Handle rating - assuming you still want a random rating for the example
            rating = await MY_METHODS.get_random_rating()
            final_data['rating'] = f"{rating}"
            final_data['ratingValue'] = float(rating)
            #await MY_METHODS.printStatus(f'final_data {final_data}')

            return final_data
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error while fetching business {e}')
            return None

    @staticmethod
    async def get_time_ago(updated_at):
        if updated_at:
            # Calculate the time difference between now and updated_at
            time_diff = timezone.now() - updated_at
            #await MY_METHODS.printStatus(f'time_diff {time_diff}')

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
    @classmethod
    async def GetRelatedBusinesses(self, business_id, pageNo=1):
        try:
            business = await sync_to_async(Business.objects.get)(id=business_id)

            # Build a single Q object combining all filters
            q_filter = Q(business_type=business.business_type) | \
                       Q(businessSegment__in=business.businessSegment.all()) | \
                       Q(businessCategory__in=business.businessCategory.all())

            # Fetch related businesses in one query, excluding the current business
            related_query = Business.objects.filter(q_filter).exclude(id=business_id).distinct()

            # Paginate and fetch full business data
            return await self.GetQueryData(businesses_query=related_query, pageNo=pageNo)
        
        except Exception as e:
            await MY_METHODS.printStatus(f'Error while fetching business {e}')
            return None
    @classmethod
    async def GetNearbyBusinesses(self, business_id, pageNo=1):
        try:
            business_location = await sync_to_async(Location.objects.get)(business__id=business_id)

            # Use Q to check city OR state
            nearby_query = Business.objects.filter(
                Q(business_location__city=business_location.city) |
                Q(business_location__state=business_location.locationState)
            ).exclude(id=business_id)

            return await self.GetQueryData(businesses_query=nearby_query, pageNo=pageNo)
        except Exception as e:
            await MY_METHODS.printStatus(f'Error while fetching business {e}')
            return None