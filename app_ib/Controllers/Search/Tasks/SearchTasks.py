import asyncio
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from asgiref.sync import sync_to_async
from django.db.models import Prefetch
from app_ib.models import Business, Location, BusinessProfile, UserProfile
from app_ib.Controllers.Business.Tasks.BusinessTasks import BUSS_TASK
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
import random

class SEARCH_TASKS:
    
    @classmethod
    async def PaginateQuery(cls, businesses_query, PageNo):
        """
        Optimized pagination that operates on QuerySets without list conversion.
        """
        page_size = 6  
        
        # Ensure we have the necessary relations for the bulk fetch
        optimized_query = businesses_query.select_related(
            'business_location', 
            'business_location__locationState', 
            'business_location__locationCountry',
            'businessBadge',
            'businessType'
        ).prefetch_related(
            'businessSegment',
            'businessCategory'
        )

        total_count = await sync_to_async(optimized_query.count)()
        paginator = Paginator(optimized_query, page_size)

        try:
            businesses_page = paginator.page(PageNo)
        except (PageNotAnInteger, ValueError):
            businesses_page = paginator.page(1)
        except EmptyPage:
            businesses_page = paginator.page(paginator.num_pages)
            
        return {
            NAMES.BUSINESSES: list(businesses_page.object_list), # We only convert the PAGE to a list
            NAMES.HAS_NEXT: businesses_page.has_next(),
            NAMES.TOTAL_PAGES: paginator.num_pages,
            NAMES.PAGE_NO: businesses_page.number
        }

    @classmethod
    async def BulkSerializeBusinesses(cls, business_list):
        """
        Serializes a list of businesses in bulk with pre-fetched data.
        Maintains EXACT data structure as legacy FetchBusiness.
        """
        serialized_data = []
        
        # Prepare random ratings in bulk to avoid multiple async calls if possible
        # but let's stick to the exact logic of MY_METHODS if it's complex.
        
        for business in business_list:
            try:
                # 1. Location Logic (Replicating BUSS_LOC_TASK.GetBusinessLocTask & FetchBusiness)
                loc_ins = getattr(business, 'business_location', None)
                loc_data = {}
                if loc_ins:
                    state_name = loc_ins.locationState.name if loc_ins.locationState else None
                    country_name = loc_ins.locationCountry.name if loc_ins.locationCountry else None
                    
                    loc_data = {
                        NAMES.PINCODE: loc_ins.pinCode,
                        NAMES.CITY: loc_ins.city,
                        NAMES.STATE: {NAMES.ID: loc_ins.locationState.id, NAMES.NAME: state_name} if loc_ins.locationState else None,
                        NAMES.COUNTRY: {NAMES.ID: loc_ins.locationCountry.id, NAMES.NAME: country_name} if loc_ins.locationCountry else None,
                        NAMES.LOCATION_LINK: loc_ins.locationLink,
                        NAMES.ID: loc_ins.pk,
                    }

                # 2. Time Ago Logic
                time_ago = await MY_METHODS.get_time_ago(updated_at=business.timestamp)
                
                # 3. Rating Logic
                rating = await MY_METHODS.get_random_rating()

                # 4. Construct Final Data (EXACT structure matching legacy)
                obj = {
                    NAMES.ID: business.pk,
                    NAMES.BUSINESS_NAME: business.businessName,
                    NAMES.COMPANY_NAME: business.businessName,
                    NAMES.MEMBERSHIP_ID: business.pk,
                    NAMES.BADGE: business.businessBadge.imageUrl if business.businessBadge else NAMES.EMPTY,
                    NAMES.TIME_AGO: str(time_ago),
                    NAMES.SINCE: business.since or NAMES.EMPTY,
                    NAMES.BUSINESS_IMAGE: business.coverImageUrl or NAMES.EMPTY,
                    NAMES.CITY: loc_data.get(NAMES.CITY, NAMES.EMPTY),
                    NAMES.STATE: loc_data.get(NAMES.STATE, NAMES.EMPTY),
                    NAMES.COUNTRY: loc_data.get(NAMES.COUNTRY, NAMES.EMPTY),
                    NAMES.PINCODE: loc_data.get(NAMES.PINCODE, NAMES.EMPTY),
                    NAMES.RATING: f"{rating}",
                    NAMES.RATING_VALUE: float(rating),
                }

                # Location String Logic
                city_str = f"{loc_data.get(NAMES.CITY)} ," if loc_data.get(NAMES.CITY) else ""
                state_str = f"{loc_data.get(NAMES.STATE)[NAMES.NAME]} ," if loc_data.get(NAMES.STATE) else ""
                country_str = f"{loc_data.get(NAMES.COUNTRY)[NAMES.NAME]}" if loc_data.get(NAMES.COUNTRY) else ""
                obj[NAMES.LOCATION] = f"{city_str}{state_str}{country_str}"

                serialized_data.append(obj)
            except Exception as e:
                print(f"Error serializing business {business.pk}: {e}")
                serialized_data.append(None)
        
        return [d for d in serialized_data if d is not None]

    @classmethod
    async def GetQueryData(cls, businesses_query, pageNo):
        """
        High-performance search entry point.
        """
        try:
            # 1. Paginate QuerySet (Optimized)
            pagination_result = await cls.PaginateQuery(businesses_query, pageNo)
            
            business_list = pagination_result[NAMES.BUSINESSES]
            
            # 2. Bulk Serialize results (Preserving legacy format)
            lawyers_data = await cls.BulkSerializeBusinesses(business_list)
            
            return {
                NAMES.HAS_NEXT: pagination_result[NAMES.HAS_NEXT],
                NAMES.TOTAL_PAGES: pagination_result[NAMES.TOTAL_PAGES],
                NAMES.PAGE_NO: pagination_result[NAMES.PAGE_NO],
                NAMES.DATA: lawyers_data
            }
            
        except Exception as e:
            print(f"Error in GetQueryData: {e}")
            return None

    @classmethod
    async def FetchBusiness(cls, business: Business):
        """
        Maintains legacy individual fetch for other controllers (e.g. details page).
        Reduces redundancy by using the same logic.
        """
        results = await cls.BulkSerializeBusinesses([business])
        return results[0] if results else None