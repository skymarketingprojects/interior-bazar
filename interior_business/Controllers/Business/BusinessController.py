from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse
from .Tasks.BusinessTasks import BUSS_TASK
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.models import Business,BusinessType,BusinessCategory,BusinessSegment
import asyncio
from django.db.models import Count
from django.db.models import Q
from interior_notification.signals import businessSignupSignal
from django.core.cache import cache


class BUSS_CONTROLLER:

    @classmethod
    async def GetBusinessHeader(self,businessId):
        try:
            cache_key = f"business_header_{businessId}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_header_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=cached_data)

            business = await sync_to_async(Business.objects.get)(id=businessId)
            headerData,status = await BUSS_TASK.GetBusinessHeaderTask(business)
            if status:
                cache.set(cache_key, headerData, 3600)  # Cache for 1 hour
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_header_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=headerData)
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_header_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: headerData
                }
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_header_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })


    @classmethod
    async def GetBusinessContactInfo(self, business:Business):
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
                data={
                    NAMES.ERROR: str(e)
                })

    async def UpdateBusinessContactInfo(self, user, data):
        try:
            contact_info = await BUSS_TASK.UpdateBusinessContactInfoTask(user, data)
            if contact_info is not None:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_contact_update_success,
                    code=RESPONSE_CODES.success,
                    data=contact_info)
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_contact_update_error,
                code=RESPONSE_CODES.error,
                data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_contact_update_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })

    @classmethod
    async def CreateBusiness(self, user_ins, data):
        try:
            # Check if business already exist
            is_business_exist = await sync_to_async(Business.objects.filter(user=user_ins).exists)()
            if is_business_exist:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.business_already_exist,
                    code=RESPONSE_CODES.error,
                    data={})
            # Create business
            business_ins = await BUSS_TASK.CreateBusinessTask(user_ins=user_ins, data=data)
            # Guard BEFORE touching the DB: on a failed create no Business row exists,
            # so firing the signal (which does Business.objects.get) here would raise
            # "Business matching query does not exist" and mask the real failure (E4).
            if not business_ins:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.business_register_error,
                    code=RESPONSE_CODES.error,
                    data={})

            business_obj = await sync_to_async(Business.objects.get)(user=user_ins)
            asyncio.create_task(sync_to_async(businessSignupSignal.send)(sender=Business, instance=business_obj, created=True))

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
                data={
                    NAMES.ERROR: str(e)
                })

    @classmethod
    async def UpdateeBusiness(self, user_ins, data):
        try:
            # Check if business already exist
            is_business_exist = await sync_to_async(Business.objects.filter(user=user_ins).exists)()
            business_data = None

            if is_business_exist:
                business_instance = await sync_to_async(Business.objects.get)(user=user_ins)
                pass
                
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

            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_register_success,
                data=business_data)

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_register_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })
    
    @classmethod
    async def GetBusinessById(self,id):
        try:
            # Check if business already exist
            is_business_exist = await sync_to_async(Business.objects.filter(pk=id).exists)()

            if is_business_exist:
                business_data = await BUSS_TASK.GetBusinessInfo(id=id)
                pass

                if business_data is not None:
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

            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_fetch_success,
                data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })


    @classmethod
    async def GetAllBusinessTypes(self):
        try:
            cache_key = "all_business_types"
            cached_data = cache.get(cache_key)
            if cached_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_type_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=cached_data)

            type_instances = await sync_to_async(list)(BusinessType.objects.all())
            type_list = []
            for type_instance in type_instances:
                type_data = await BUSS_TASK.GetBusinessTypeData(type_instance)
                if type_data:
                    type_list.append(type_data)
            
            cache.set(cache_key, type_list, 86400)  # Cache for 24 hours
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
                data={
                    NAMES.ERROR: str(e)
                })

    
    @classmethod
    async def GetAllBusinessTab(self):
        try:
            cache_key = "all_business_tabs"
            cached_data = cache.get(cache_key)
            if cached_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_category_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=cached_data)

            categoryInstances = await sync_to_async(list)(
                BusinessCategory.objects.filter(isActive=True).annotate(num_related=Count(NAMES.BUSINESS_CATEGORY_RELATION)).filter(num_related__gt=0)
            )
            category_list = []
            for categoryInstance in categoryInstances:
                categoryData = await BUSS_TASK.GetBusinessTypeData(categoryInstance)
                if categoryData:
                    categoryData[NAMES.TYPE]=NAMES.CATEGORY
                    category_list.append(categoryData)
            segmentInstances = await sync_to_async(list)(
                BusinessSegment.objects.filter(isActive=True).annotate(num_related=Count(NAMES.BUSINESS_SEGMENT_RELATION)).filter(num_related__gt=0)
                )
            for segmentInstance in segmentInstances:
                segmentData = await BUSS_TASK.GetBusinessTypeData(segmentInstance)
                if segmentData:
                    segmentData[NAMES.TYPE]=NAMES.SEGMENT
                    category_list.append(segmentData)
            
            category_list.sort(
                key=lambda x: (x.get(NAMES.LABEL) or "").lower()
            )

            cache.set(cache_key, category_list, 86400)  # Cache for 24 hours
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_category_fetch_success,
                code=RESPONSE_CODES.success,
                data=category_list)
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_category_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })

    @classmethod
    async def GetAllBusinessCategories(self,trending=False,query=None):
        try:
            cache_key = f"all_categories_{trending}_{query}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_category_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=cached_data)

            categoryInstances = []

            if trending:
                categoryInstances = await sync_to_async(list)(BusinessCategory.objects.filter(isActive=True, trending=True).order_by('index'))
            else:
                if query:
                    categoryInstances = await sync_to_async(list)(BusinessCategory.objects.filter(isActive=True, lable__icontains=query).order_by('index'))
                else:
                    categoryInstances = await sync_to_async(list)(BusinessCategory.objects.filter(isActive=True))
            category_list = []
            for categoryInstance in categoryInstances:
                categoryData = await BUSS_TASK.GetBusinessTypeData(categoryInstance)
                if categoryData:
                    category_list.append(categoryData)
            
            cache.set(cache_key, category_list, 86400)  # Cache for 24 hours
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_category_fetch_success,
                code=RESPONSE_CODES.success,
                data=category_list)
        except Exception as e:
            pass
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_category_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })

    @classmethod
    async def GetBusinessSegmentsByType(self,typeId,query=None):
        try:
            cache_key = f"segments_by_type_{typeId}_{query}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_category_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=cached_data)

            isTypeExist = await sync_to_async(BusinessType.objects.filter(pk=typeId).exists)()
            if not isTypeExist:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.business_type_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={})
            businessType = await sync_to_async(BusinessType.objects.get)(pk=typeId)
            pass
            segmentInstances = []
            if query:
                segmentInstances = await sync_to_async(list)(businessType.business_type_segment.filter(lable__icontains=query))
            else:
                segmentInstances = await sync_to_async(list)(businessType.business_type_segment.all())
            segment_list = []
            for segmentInstance in segmentInstances:
                segmentData = await BUSS_TASK.GetBusinessSegmentData(segmentInstance)
                if segmentData:
                    segment_list.append(segmentData)
            
            cache.set(cache_key, segment_list, 86400)  # Cache for 24 hours
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_category_fetch_success,
                code=RESPONSE_CODES.success,
                data=segment_list)
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_category_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })

        
    @classmethod
    async def GetExploreSections(self):
        try:
            cache_key = "explore_sections_all"
            cached_data = cache.get(cache_key)
            if cached_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.explore_section_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=cached_data
                )

            categoryInstances = await sync_to_async(list)(BusinessCategory.objects.filter(isActive=True).exclude(trending=False).order_by('index'))
            data = []
            for categoryInstance in categoryInstances:
                categoryData = await BUSS_TASK.GetBusinessTypeData(categoryInstance)
                if not categoryData:
                    continue
                segments = categoryInstance.business_category_segment.all()[:3]
                segmentData = [await BUSS_TASK.GetBusinessSegmentData(seg) for seg in segments]
                categoryData[NAMES.SUB_CATEGORIES] = segmentData
                data.append(categoryData)
            if not data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.explore_section_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={})

            cache.set(cache_key, data, 86400)  # Cache for 24 hours
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.explore_section_fetch_success,
                code=RESPONSE_CODES.success,
                data=data
            )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.explore_section_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })

    @classmethod
    async def UpdateBusinessBanner(self, business_ins, data):
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
                data={
                    NAMES.ERROR: str(e)
                })
    
    @classmethod
    async def GetBusinessBanner(self, business_ins):
        try:
            cache_key = f"business_banner_{business_ins.id}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_banner_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=cached_data)

            taskResult = await BUSS_TASK.GetBusinessBannerTask(business=business_ins)
            if taskResult is not None:
                cache.set(cache_key, taskResult, 3600)  # Cache for 1 hour
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
                data={
                    NAMES.ERROR: str(e)
                })