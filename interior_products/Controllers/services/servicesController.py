from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business
from interior_products.models import Service, ProductCategory, ProductSubCategory
from interior_products.Controllers.products.Tasks.productsTasks import PRODUCTS_TASKS
from .Tasks.servicesTasks import SERVICES_TASKS
from .Validators.servicesValidators import SERVICES_VALIDATORS
from django.db.models import Q, Count, Prefetch
import asyncio

class SERVICES_CONTROLLER:

    @classmethod
    async def getService(cls, serviceId: int) -> LocalResponse:
        try:
            queryset = Service.objects.filter(id=serviceId).select_related(
                'business', 'business__user', 'business__user__user_profile'
            ).prefetch_related('serviceImages', 'category', 'subCategory')
            
            objs = await sync_to_async(list)(queryset)
            data = await SERVICES_TASKS.BulkSerializeServices(objs)
            
            if not data:
                return LocalResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.service_fetch_error, code=RESPONSE_CODES.error, data={})
            
            return LocalResponse(response=RESPONSE_MESSAGES.success, message=RESPONSE_MESSAGES.service_fetch_success, code=RESPONSE_CODES.success, data=data[0])
        except Exception as e:
            return LocalResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.service_fetch_error, code=RESPONSE_CODES.error, data={'error': str(e)})
    
    @classmethod
    async def getAllService(cls, page, size, filterType=None, id=None, state=None, query=None) -> LocalResponse:
        try:
            filterQuery = Q()
            if state:
                filterQuery &= Q(business__business_location__locationState__value__iexact=state)
            
            if filterType and id:
                if filterType == "category":
                    filterQuery &= Q(category__id=int(id))
                elif filterType == "subCategory":
                    filterQuery &= Q(subCategory__id=int(id))

            if query:
                q_obj = Q(title__icontains=query)
                q_obj |= Q(category__lable__icontains=query)
                q_obj |= Q(subCategory__lable__icontains=query)
                filterQuery &= q_obj

            related_qs = Service.objects.filter(filterQuery).select_related(
                'business', 'business__user', 'business__user__user_profile'
            ).prefetch_related('serviceImages', 'category', 'subCategory').order_by('index')

            paginated = await MY_METHODS.paginate_queryset(related_qs, page, size)
            data = await SERVICES_TASKS.BulkSerializeServices(paginated["results"])
            paginated['pagination']['data'] = data
            
            return LocalResponse(response=RESPONSE_MESSAGES.success, message=RESPONSE_MESSAGES.service_fetch_success, code=RESPONSE_CODES.success, data=paginated['pagination'])
        except Exception as e:
            return LocalResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.service_fetch_error, code=RESPONSE_CODES.error, data={'error': str(e)})

    @classmethod
    async def getServicesForBusiness(cls, business: Business) -> LocalResponse:
        try:
            queryset = business.services.select_related(
                'business', 'business__user', 'business__user__user_profile'
            ).prefetch_related('serviceImages', 'category', 'subCategory').order_by('index')
            
            services = await sync_to_async(list)(queryset)
            data = await SERVICES_TASKS.BulkSerializeServices(services)
            return LocalResponse(response=RESPONSE_MESSAGES.success, message=RESPONSE_MESSAGES.services_fetch_success, code=RESPONSE_CODES.success, data=data)
        except Exception as e:
            return LocalResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.services_fetch_error, code=RESPONSE_CODES.error, data={'error': str(e)})

    @classmethod
    async def createService(cls, business: Business, data: dict) -> LocalResponse:
        res = await SERVICES_TASKS.createService(business, data)
        if not res: return LocalResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.service_create_error, code=RESPONSE_CODES.error, data={})
        return LocalResponse(response=RESPONSE_MESSAGES.success, message=RESPONSE_MESSAGES.service_create_success, code=RESPONSE_CODES.success, data=res)
    
    @classmethod
    async def updateService(cls, business: Business, serviceId: int, data: dict) -> LocalResponse:
        service = await sync_to_async(Service.objects.filter(id=serviceId, business=business).first)()
        if not service: return LocalResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.service_update_error, code=RESPONSE_CODES.error, data={})
        res = await SERVICES_TASKS.updateService(service, data)
        if not res: return LocalResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.service_update_error, code=RESPONSE_CODES.error, data={})
        return LocalResponse(response=RESPONSE_MESSAGES.success, message=RESPONSE_MESSAGES.service_update_success, code=RESPONSE_CODES.success, data=res)
    
    @classmethod
    async def deleteService(cls, business: Business, serviceId: int) -> LocalResponse:
        service = await sync_to_async(Service.objects.filter(id=serviceId, business=business).first)()
        if not service: return LocalResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.service_delete_error, code=RESPONSE_CODES.error, data={})
        res = await SERVICES_TASKS.deleteService(service)
        if not res: return LocalResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.service_delete_error, code=RESPONSE_CODES.error, data={})
        return LocalResponse(response=RESPONSE_MESSAGES.success, message=RESPONSE_MESSAGES.service_delete_success, code=RESPONSE_CODES.success, data=res)
        
    @classmethod
    async def GetRelatedServices(cls, serviceId: int, page: int = 1, size: int = 10):
        try:
            base_service = await sync_to_async(Service.objects.get)(id=serviceId)
            related_qs = Service.objects.filter(
                Q(title__icontains=base_service.title.split(" ")[0]) | 
                Q(orignalPrice__range=(base_service.orignalPrice * 0.8, base_service.orignalPrice * 1.2)) |
                Q(business=base_service.business)
            ).select_related(
                'business', 'business__user', 'business__user__user_profile'
            ).prefetch_related('serviceImages', 'category', 'subCategory').exclude(id=base_service.id)

            paginated = await MY_METHODS.paginate_queryset(related_qs, page, size)
            data = await SERVICES_TASKS.BulkSerializeServices(paginated["results"])
            paginated['pagination']['data'] = data
            return LocalResponse(response=RESPONSE_MESSAGES.success, message="Related services fetched successfully", code=RESPONSE_CODES.success, data=paginated["pagination"])
        except Exception as e:
            return LocalResponse(response=RESPONSE_MESSAGES.error, message="Error fetching related services", code=RESPONSE_CODES.error, data={"error": str(e)})

    @classmethod
    async def GetServiceTab(cls):
        try:
            cat_qs = ProductCategory.objects.annotate(num_entries=Count('catServices'))
            sub_qs = ProductSubCategory.objects.annotate(num_entries=Count('subcatServices'))
            
            cats, subs = await asyncio.gather(sync_to_async(list)(cat_qs), sync_to_async(list)(sub_qs))
            
            tabData = []
            for c in cats:
                data = PRODUCTS_TASKS.getCategoriesDataSync(c)
                data['type'] = 'category'
                tabData.append(data)
                
            for s in subs:
                data = PRODUCTS_TASKS.getCategoriesDataSync(s)
                data['type'] = 'subCategory'
                tabData.append(data)

            return LocalResponse(response=RESPONSE_MESSAGES.success, message=RESPONSE_MESSAGES.service_tab_success, code=RESPONSE_CODES.success, data=tabData)
        except Exception as e:
            return LocalResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.service_tab_error, code=RESPONSE_CODES.error, data={'error': str(e)})