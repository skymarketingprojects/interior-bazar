
import random
import asyncio
from profile import Profile
from adrf.decorators import api_view
from asgiref.sync import sync_to_async
from django.http import JsonResponse
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.models import Business, Location, BusinessProfile,BusinessCategory,BusinessSegment, UserProfile
from interior_business.Controllers.BusinessProfile.Tasks.BusinessProfileTasks import BUSS_PROF_TASK
from app_ib.Controllers.Profile.Tasks.Taskys import PROFILE_TASKS
from interior_business.Controllers.Business.Tasks.BusinessTasks import BUSS_TASK
from interior_business.Controllers.BussLocation.Tasks.BusinessLocationTasks import BUSS_LOC_TASK
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse
from interior_business.Controllers.Search.Tasks.SearchTasks import SEARCH_TASKS
from django.db.models import Q
from django.core.cache import cache
import hashlib
import json


class SEARCH_CONTROLLER:
    @classmethod
    async def GetBusinessUsingPagination(self, pageNo, pageSize=10, tabId=None, tabType=None, state=None, query=None):
        try:
            # Standardize parameters
            pageNo = int(pageNo)
            pageSize = int(pageSize)
            
            # Create a unique cache key based on parameters
            params = f"{pageNo}_{pageSize}_{tabId}_{tabType}_{state}_{query}"
            cache_key = f"search_pagination_{hashlib.md5(params.encode()).hexdigest()}"
            
            # Entropy Control: Bypass cache for search queries or deep pagination to save VPS memory
            use_cache = not query and pageNo <= 3
            
            if use_cache:
                cached_data = await cache.aget(cache_key)
                if cached_data:
                    return LocalResponse(
                        code=RESPONSE_CODES.success,
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.business_fetch_success,
                        data=cached_data)

            # filterQuery construction...
            filterQuery = Q()
            offset = (pageNo - 1) * pageSize
            limit = offset + pageSize

            if state:
                filterQuery |= Q(business_location__locationState__value__iexact=state)
            
            if tabId and tabType:
                if tabType == NAMES.CATEGORY:
                    filterQuery &= Q(businessCategory__id=tabId)
                elif tabType == NAMES.SEGMENT:
                    filterQuery &= Q(businessSegment__id=tabId)
            
            if query:
                filterQuery |= Q(businessName__icontains=query)
                filterQuery |= Q(businessSegment__lable__icontains=query)
                filterQuery |= Q(businessCategory__lable__icontains=query)

            queryset = (
                Business.objects
                .filter(filterQuery).distinct()
                .select_related(
                    "user",
                    "businessBadge",
                    "business_location",
                    "business_location__locationState",
                    "business_location__locationCountry",
                )
                .prefetch_related(
                    "businessCategory",
                    "businessSegment",
                )
                .order_by("-timestamp")[offset:limit]
            )

            businesses = await sync_to_async(list)(queryset)

            # fetch business data:
            business_data = await SEARCH_TASKS.GetQueryData(
                                businesses_query=businesses,
                                pageNo=pageNo,
                                pageSize=pageSize
                            )
            
            if use_cache:
                await cache.aset(cache_key, business_data, 900)  # Tier 1: 15m for search results

            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_fetch_success,
                data=business_data)

        except Exception as e:
            pass
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })


    @classmethod
    async def GetTopBusiness(self,index,pageSize=10,tabId=None,tabType=None,state=None,query=None):
        try:
            paginationResp = await self.GetBusinessUsingPagination(pageNo=index,pageSize=pageSize,tabId=tabId,tabType=tabType,state=state,query=query)
            business_data = paginationResp.data
            business_data[NAMES.TOP_SELLER] = business_data[NAMES.DATA][:5]
            business_data[NAMES.BUSINESSES] = business_data.pop(NAMES.DATA)

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
                    NAMES.ERROR: str(e)
                })
    @classmethod
    async def GetRelatedBusiness(self, businessId, pageNo=1):
        try:
            pageNo = int(pageNo)
            cache_key = f"related_business_{businessId}_{pageNo}"
            
            # Only cache the first few pages of discovery
            use_cache = pageNo <= 3
            
            if use_cache:
                cached_data = await cache.aget(cache_key)
                if cached_data:
                    return LocalResponse(
                        code=RESPONSE_CODES.success,
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.business_fetch_success,
                        data=cached_data
                    )

            related_businesses = await SEARCH_TASKS.GetRelatedBusinesses(business_id=businessId, pageNo=pageNo)
            if related_businesses is None:
                return LocalResponse(
                    code=RESPONSE_CODES.error,
                    response=RESPONSE_MESSAGES.error,
                    message="Business not found",
                    data=[]
                )

            if use_cache:
                await cache.aset(cache_key, related_businesses, 3600)  # Tier 2: 1h for discovery
            
            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_fetch_success,
                data=related_businesses
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=str(e),
                code=RESPONSE_CODES.error,
                data={}
            )


    @classmethod
    async def GetNearbyBusiness(self, businessId=None, city=None, state=None, pageNo=1):
        try:
            pageNo = int(pageNo)
            # Standardize strings for better cache hits
            city_std = city.lower() if city else ""
            state_std = state.lower() if state else ""
            
            params = f"{businessId}_{city_std}_{state_std}_{pageNo}"
            cache_key = f"nearby_business_{hashlib.md5(params.encode()).hexdigest()}"
            
            use_cache = pageNo <= 3
            
            if use_cache:
                cached_data = await cache.aget(cache_key)
                if cached_data:
                    return LocalResponse(
                        code=RESPONSE_CODES.success,
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.business_fetch_success,
                        data=cached_data
                    )

            business = None
            locationState = None
            if businessId:
                business = await sync_to_async(Business.objects.get)(id=businessId)
                location: Location = business.business_location
                city = location.city
                locationState = location.locationState
                
            nearby_businesses = await SEARCH_TASKS.GetNearbyBusinesses(businessId=businessId, city=city, state=state, locationState=locationState, pageNo=pageNo)
            if nearby_businesses is None:
                return LocalResponse(
                    code=RESPONSE_CODES.error,
                    response=RESPONSE_MESSAGES.error,
                    message="Business or location not found",
                    data=[]
                )

            if use_cache:
                await cache.aset(cache_key, nearby_businesses, 3600)  # Tier 2: 1h for discovery
            
            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_fetch_success,
                data=nearby_businesses
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=str(e),
                code=RESPONSE_CODES.error,
                data={}
            )