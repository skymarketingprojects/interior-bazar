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
from interior_notification.signals import businessSignupSignal

class BUSS_CONTROLLER:

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
            # await MY_METHODS.printStatus(f'business_ins {business_ins}')
            asyncio.create_task(sync_to_async(businessSignupSignal.send)(sender=Business,instance=Business.objects.get(user=user_ins),created=True))
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
                # await MY_METHODS.printStatus(f'business instance {business_instance}')
                
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
                # await MY_METHODS.printStatus(f'business data {business_data}')

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
            type_instances = await sync_to_async(list)(BusinessType.objects.all())
            type_list = []
            for type_instance in type_instances:
                type_data = await BUSS_TASK.GetBusinessTypeData(type_instance)
                if type_data:
                    type_list.append(type_data)
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
            categoryInstances = await sync_to_async(list)(
                BusinessCategory.objects.annotate(num_related=Count(NAMES.BUSINESS_CATEGORY_RELATION)).filter(num_related__gt=0)
            )
            category_list = []
            for categoryInstance in categoryInstances:
                categoryData = await BUSS_TASK.GetBusinessTypeData(categoryInstance)
                if categoryData:
                    categoryData[NAMES.TYPE]=NAMES.CATEGORY
                    category_list.append(categoryData)
            segmentInstances = await sync_to_async(list)(
                BusinessSegment.objects.annotate(num_related=Count(NAMES.BUSINESS_SEGMENT_RELATION)).filter(num_related__gt=0)
                )
            for segmentInstance in segmentInstances:
                segmentData = await BUSS_TASK.GetBusinessTypeData(segmentInstance)
                if segmentData:
                    segmentData[NAMES.TYPE]=NAMES.SEGMENT
                    category_list.append(segmentData)
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
    async def GetAllBusinessCategories(self,trending=False):
        try:
            categoryInstances = []
            if trending:
                categoryInstances = await sync_to_async(list)(BusinessCategory.objects.filter(trending=True).order_by('index'))
            else:
                categoryInstances = await sync_to_async(list)(BusinessCategory.objects.all())
            category_list = []
            for categoryInstance in categoryInstances:
                categoryData = await BUSS_TASK.GetBusinessTypeData(categoryInstance)
                if categoryData:
                    category_list.append(categoryData)
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_category_fetch_success,
                code=RESPONSE_CODES.success,
                data=category_list)
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in category GET: {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_category_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })
    @classmethod
    async def GetBusinessSegmentsByType(self,typeId):
        try:
            isTypeExist = await sync_to_async(BusinessType.objects.filter(pk=typeId).exists)()
            if not isTypeExist:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.business_type_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={})
            businessType = await sync_to_async(BusinessType.objects.get)(pk=typeId)
            segmentInstances = await sync_to_async(list)(businessType.business_type_segment.all())
            segment_list = []
            for segmentInstance in segmentInstances:
                segmentData = await BUSS_TASK.GetBusinessTypeData(segmentInstance)
                if segmentData:
                    segment_list.append(segmentData)
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
            categoryInstances = await sync_to_async(list)(BusinessCategory.objects.all())
            data = []
            for categoryInstance in categoryInstances:
                categoryData = await BUSS_TASK.GetBusinessTypeData(categoryInstance)
                if not categoryData:
                    continue
                segments = categoryInstance.business_category_segment.all()
                segmentData = [await BUSS_TASK.GetBusinessTypeData(seg) for seg in segments]
                categoryData[NAMES.SUB_CATEGORIES] = segmentData
                data.append(categoryData)
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
                data={
                    NAMES.ERROR: str(e)
                })