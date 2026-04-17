from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse
from .Tasks.BusinessTasks import BUSS_TASK
from app_ib.models import Business, BusinessType, BusinessCategory, BusinessSegment
import asyncio
from django.db.models import Count, Q, Prefetch
from interior_notification.signals import businessSignupSignal

class BUSS_CONTROLLER:

    @classmethod
    async def GetBusinessHeader(cls, businessId):
        try:
            # Optimized header retrieval via direct TASK call (no extra get)
            headerData, status = await BUSS_TASK.GetBusinessHeaderTask(Business(id=businessId))
            if status:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_header_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=headerData)
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_header_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: headerData})
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_header_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)})

    @classmethod
    async def GetBusinessContactInfo(cls, business: Business):
        try:
            contact_info = await BUSS_TASK.GetBusinessContactInfoTask(business)
            if contact_info is not None:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_contact_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=contact_info)
            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_contact_fetch_error,
                data={})
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_contact_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)})

    @classmethod
    async def CreateBusiness(cls, user_ins, data):
        try:
            is_business_exist = await sync_to_async(Business.objects.filter(user=user_ins).exists)()
            if is_business_exist:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.business_already_exist,
                    code=RESPONSE_CODES.error,
                    data={})
            business_ins = await BUSS_TASK.CreateBusinessTask(user_ins=user_ins, data=data)
            asyncio.create_task(sync_to_async(businessSignupSignal.send)(sender=Business, instance=Business.objects.get(user=user_ins), created=True))
            if not business_ins:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.business_register_error,
                    code=RESPONSE_CODES.error,
                    data={})
            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_register_success,
                data={})
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_register_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)})

    @classmethod
    async def UpdateeBusiness(cls, user_ins, data):
        try:
            business_instance = await sync_to_async(Business.objects.filter(user=user_ins).first)()
            if not business_instance:
                return LocalResponse(
                    code=RESPONSE_CODES.success,
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_register_success,
                    data={})
                
            business_ins = await BUSS_TASK.UpdateBusinessTask(business_ins=business_instance, data=data)
            if business_ins is None:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.business_update_error,
                    code=RESPONSE_CODES.error,
                    data={})
            
            business_data = await BUSS_TASK.GetBusinessInfo(id=business_instance.id)
            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_update_success,
                data=business_data)
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_register_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)})

    @classmethod
    async def GetBusinessById(cls, id):
        try:
            business_data = await BUSS_TASK.GetBusinessInfo(id=id)
            if business_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=business_data)
            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_fetch_error,
                data={})
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)})

    @classmethod
    async def GetAllBusinessTypes(cls):
        try:
            # Bulk fetch business types
            type_instances = await sync_to_async(list)(BusinessType.objects.all())
            type_list = [BUSS_TASK.GetBusinessTypeDataSync(ins) for ins in type_instances]
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_type_fetch_success,
                code=RESPONSE_CODES.success,
                data=type_list)
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_type_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)})

    @classmethod
    async def GetAllBusinessTab(cls):
        try:
            # High-speed parallel annotation and bulk serialization
            category_qs = BusinessCategory.objects.annotate(num_related=Count(NAMES.BUSINESS_CATEGORY_RELATION))
            segment_qs = BusinessSegment.objects.annotate(num_related=Count(NAMES.BUSINESS_SEGMENT_RELATION))
            
            categories, segments = await asyncio.gather(
                sync_to_async(list)(category_qs),
                sync_to_async(list)(segment_qs)
            )

            result_list = []
            for cat in categories:
                data = BUSS_TASK.GetBusinessTypeDataSync(cat)
                data[NAMES.TYPE] = NAMES.CATEGORY
                result_list.append(data)
                
            for seg in segments:
                data = BUSS_TASK.GetBusinessTypeDataSync(seg)
                data[NAMES.TYPE] = NAMES.SEGMENT
                result_list.append(data)

            result_list.sort(key=lambda x: (x.get(NAMES.LABEL) or "").lower())
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_category_fetch_success,
                code=RESPONSE_CODES.success,
                data=result_list)
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_category_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)})

    @classmethod
    async def GetAllBusinessCategories(cls, trending=False, query=None):
        try:
            queryset = BusinessCategory.objects.all()
            if trending: queryset = queryset.filter(trending=True)
            elif query: queryset = queryset.filter(lable__icontains=query)
            
            instances = await sync_to_async(list)(queryset.order_by('index'))
            data_list = [BUSS_TASK.GetBusinessTypeDataSync(ins) for ins in instances]
            
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_category_fetch_success,
                code=RESPONSE_CODES.success,
                data=data_list)
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_category_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)})

    @classmethod
    async def GetBusinessSegmentsByType(cls, typeId, query=None):
        try:
            businessType = await sync_to_async(lambda: BusinessType.objects.filter(pk=typeId).prefetch_related(
                Prefetch('business_type_segment', queryset=BusinessSegment.objects.filter(lable__icontains=query) if query else BusinessSegment.objects.all())
            ).first())()
            
            if not businessType:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.business_type_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={})
            
            segments = businessType.business_type_segment.all()
            data_list = [BUSS_TASK.GetBusinessTypeDataSync(seg) for seg in segments]
            
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_category_fetch_success,
                code=RESPONSE_CODES.success,
                data=data_list)
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_category_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)})

    @classmethod
    async def GetExploreSections(cls):
        try:
            # Massive N+1 optimization for explore section
            category_qs = BusinessCategory.objects.exclude(trending=False).prefetch_related(
                Prefetch('business_category_segment', queryset=BusinessSegment.objects.all()[:3], to_attr='top_segments')
            ).order_by('index')
            
            instances = await sync_to_async(list)(category_qs)
            data = []
            for cat in instances:
                cat_data = BUSS_TASK.GetBusinessTypeDataSync(cat)
                cat_data[NAMES.SUB_CATEGORIES] = [BUSS_TASK.GetBusinessTypeDataSync(seg) for seg in getattr(cat, 'top_segments', [])]
                data.append(cat_data)
            
            if not data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.explore_section_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={})

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.explore_section_fetch_success,
                code=RESPONSE_CODES.success,
                data=data)
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.explore_section_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)})

    @classmethod
    async def UpdateBusinessBanner(cls, business_ins, data):
        try:
            taskResult = await BUSS_TASK.UpdateBusinessBannerTask(business=business_ins, data=data)
            if taskResult is not None:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_banner_update_success,
                    code=RESPONSE_CODES.success,
                    data=taskResult)
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_banner_update_error,
                code=RESPONSE_CODES.error,
                data={})
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_banner_update_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)})

    @classmethod
    async def GetBusinessBanner(cls, business_ins):
        try:
            taskResult = await BUSS_TASK.GetBusinessBannerTask(business=business_ins)
            if taskResult is not None:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_banner_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=taskResult)
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_banner_fetch_error,
                code=RESPONSE_CODES.error,
                data={})
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_banner_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)})