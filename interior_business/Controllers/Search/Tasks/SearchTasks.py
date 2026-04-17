import asyncio
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from asgiref.sync import sync_to_async
from django.http import JsonResponse
import random
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from app_ib.models import Business, Location, BusinessProfile, UserProfile, State, Country, BusinessBadge

class SEARCH_TASKS:
    
    @classmethod
    async def PaginateQuery(cls, businesses_query, PageNo, pageSize=6):
        page_number = PageNo
        page_size = pageSize
        businesses = await sync_to_async(list)(businesses_query)
        paginator = Paginator(businesses, page_size)

        try:
            businesses_page = paginator.page(page_number)
        except PageNotAnInteger:
            businesses_page = paginator.page(int(page_number))
        except EmptyPage:
            businesses_page = paginator.page(paginator.num_pages)
            
        return {
            NAMES.BUSINESSES: businesses_page,
            NAMES.HAS_NEXT: businesses_page.has_next(),
            NAMES.TOTAL_PAGES: paginator.num_pages,
            NAMES.PAGE_NO: page_number
        }

    @classmethod
    async def GetQueryData(cls, businesses_query, pageNo, pageSize=10):
        try:
            # High-performance bulk serialization
            business_list = await sync_to_async(list)(businesses_query)
            serialized_data = await cls.BulkSerializeSearchData(business_list)
            return {
                NAMES.PAGE_NO: pageNo,
                NAMES.DATA: serialized_data
            }
        except: return None

    @classmethod
    async def BulkSerializeSearchData(cls, business_list):
        """Unified bulk serialization for search results."""
        results = []
        now = timezone.now()
        for business in business_list:
            try:
                location = getattr(business, "business_location", None)
                state = location.locationState if location else None
                country = location.locationCountry if location else None
                badge = business.businessBadge

                # Fast location formatting
                city_prefix = f"{location.city} ," if location and location.city else ""
                state_prefix = f"{state.name} ," if state else ""
                country_suffix = f"{country.name}" if country else ""

                results.append({
                    NAMES.ID: business.pk,
                    NAMES.BUSINESS_NAME: business.businessName,
                    NAMES.COMPANY_NAME: business.brandName or business.businessName,
                    NAMES.MEMBERSHIP_ID: business.pk,
                    NAMES.BADGE: badge.imageUrl if badge else NAMES.EMPTY,
                    NAMES.TIME_AGO: cls.get_time_ago_sync(business.timestamp, now),
                    NAMES.SINCE: business.since or NAMES.EMPTY,
                    NAMES.BUSINESS_IMAGE: business.coverImageUrl or NAMES.EMPTY,
                    NAMES.CITY: location.city if location else NAMES.EMPTY,
                    NAMES.STATE: {
                        NAMES.ID: state.pk, NAMES.NAME: state.name,
                    } if state else {},
                    NAMES.COUNTRY: {
                        NAMES.ID: country.pk, NAMES.NAME: country.code,
                    } if country else {},
                    NAMES.PINCODE: location.pinCode if location else NAMES.EMPTY,
                    NAMES.LOCATION: f"{city_prefix}{state_prefix}{country_suffix}",
                    NAMES.RATING: business.rating or '3.5',
                    NAMES.RATING_VALUE: float(business.rating or '3.5'),
                })
            except: pass
        return results

    @staticmethod
    def get_time_ago_sync(updated_at, now):
        """Synchronous version to avoid overhead in loops."""
        if not updated_at: return "No update available"
        time_diff = now - updated_at
        if time_diff < timedelta(minutes=1): return "Just now"
        elif time_diff < timedelta(hours=1):
            m = time_diff.seconds // 60
            return f"{m} minute{'s' if m > 1 else ''} ago"
        elif time_diff < timedelta(days=1):
            h = time_diff.seconds // 3600
            return f"{h} hour{'s' if h > 1 else ''} ago"
        elif time_diff < timedelta(weeks=1):
            d = time_diff.days
            return f"{d} day{'s' if d > 1 else ''} ago"
        elif time_diff < timedelta(weeks=4):
            w = time_diff.days // 7
            return f"{w} week{'s' if w > 1 else ''} ago"
        else:
            mo = time_diff.days // 30
            return f"{mo} month{'s' if mo > 1 else ''} ago"

    @classmethod
    async def FetchBusiness(cls, business: Business):
        """Maintained for single-item compatibility."""
        results = await cls.BulkSerializeSearchData([business])
        return results[0] if results else None

    @classmethod
    async def GetRelatedBusinesses(cls, business_id, pageNo=1):
        try:
            business = await sync_to_async(Business.objects.get)(id=business_id)
            segments = await sync_to_async(lambda: list(business.businessSegment.all()))()
            categories = await sync_to_async(lambda: list(business.businessCategory.all()))()

            queryset = Business.objects.filter(
                Q(businessType=business.businessType) |
                Q(businessSegment__in=segments) |
                Q(businessCategory__in=categories)
            ).select_related(
                "user", "businessBadge", "business_location", 
                "business_location__locationState", "business_location__locationCountry"
            ).prefetch_related("businessCategory", "businessSegment").exclude(id=business_id).distinct().order_by("-timestamp")

            # Apply hard slice for pagination early if needed, or use full queryset
            offset = (pageNo - 1) * 10
            sliced_results = await sync_to_async(list)(queryset[offset:offset+10])
            
            return await cls.GetQueryData(businesses_query=sliced_results, pageNo=pageNo)
        except: return None

    @classmethod
    async def GetNearbyBusinesses(cls, city: str = None, state: str = None, locationState: State = None, businessId: int = None, pageNo=1):
        try:
            query = Q()
            if city: query |= Q(business_location__city__iexact=city)
            if state: query |= Q(business_location__state__iexact=state)
            if locationState: query |= Q(business_location__locationState=locationState)
            
            if not query: return None

            queryset = Business.objects.filter(query).select_related(
                "user", "businessBadge", "business_location", 
                "business_location__locationState", "business_location__locationCountry"
            ).prefetch_related("businessCategory", "businessSegment").distinct().order_by("-timestamp")

            if businessId: queryset = queryset.exclude(id=businessId)

            offset = (pageNo - 1) * 10
            sliced_results = await sync_to_async(list)(queryset[offset:offset+10])
            
            return await cls.GetQueryData(businesses_query=sliced_results, pageNo=pageNo)
        except: return None