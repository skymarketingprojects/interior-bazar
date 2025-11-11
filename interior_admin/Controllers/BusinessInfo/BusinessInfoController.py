from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse

from .Tasks.BusinessInfoTasks import BUSINESS_INFO_TASKS
from .Validators.BusinessInfoValidators import BUSINESS_INFO_VALIDATORS
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business
from django.core.paginator import Paginator
import asyncio

from django.conf import settings
from app_ib.Utils.AppMode import APPMODE

class BUSINESS_INFO_CONTROLLER:
    
    @classmethod
    async def GetBusinessInfo(cls,pageNo=1,size=10):
        try:
            #await MY_METHODS.printStatus(f'pageNo {pageNo}')
            businessesIns = None
            if settings.ENV == APPMODE.PROD:
                businessesIns = await sync_to_async(lambda: Business.objects.filter(selfCreated=False).select_related('business_profile').only(
                        'id',
                        'business_name',
                        'timestamp',
                        'cover_image_url',
                        'since',
                        'business_plan__services',
                        'business_plan__isActive',
                        'business_lead_query__id'
                    ).order_by('-timestamp')
                )()
            else: 
                businessesIns = await sync_to_async(lambda: Business.objects.all().select_related('business_profile').only(
                        'id',
                        'business_name',
                        'timestamp',
                        'cover_image_url',
                        'since',
                        'business_plan__services',
                        'business_plan__isActive',
                        'business_lead_query__id'
                    ).order_by('-timestamp')
                )()
            #await MY_METHODS.printStatus(f'pageNo {pageNo}')

            paginator = Paginator(businessesIns, size)
            page_obj = paginator.get_page(pageNo)

            tasks = [BUSINESS_INFO_TASKS.GetBusinessInfo(business) for business in page_obj]
            businessData = await asyncio.gather(*tasks)

            busPaginationData={
                NAMES.BUSINESSES: businessData,
                NAMES.CURRENT_PAGE: page_obj.number,
                NAMES.HAS_NEXT: page_obj.has_next(),
                NAMES.HAS_PREVIOUS: page_obj.has_previous(),
                NAMES.TOTAL_PAGES: paginator.num_pages,
                NAMES.TOTAL_COUNT: len(businessesIns),
                NAMES.PAGE_SIZE: size
            }
            
                    
            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_fetch_success,
                data=busPaginationData
            )
        except Exception as e:
            #await MY_METHODS.printStatus(f'GetBusinessInfo:{str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                }
            )
