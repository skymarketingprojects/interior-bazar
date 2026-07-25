from asgiref.sync import sync_to_async
from django.core.cache import cache
import hashlib

from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business
from interior_products.models import Service,ProductCategory,ProductSubCategory
from interior_products.Controllers.products.Tasks.productsTasks import PRODUCTS_TASKS

from .Tasks.servicesTasks import SERVICES_TASKS
from .Validators.servicesValidators import SERVICES_VALIDATORS
from django.db.models import Q



class SERVICES_CONTROLLER:

    @classmethod
    async def getService(self,serviceId:int)->LocalResponse:
        try:
            cache_key = f"service_detail_{serviceId}"
            # Cache is best-effort — a Redis outage must not fail the request. See ISSUE-001.
            try:
                cached_data = cache.get(cache_key)
            except Exception:
                cached_data = None
            if cached_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.service_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=cached_data
                )

            service = await sync_to_async(Service.objects.get)(id=serviceId)
            if not service:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.service_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={'error':RESPONSE_MESSAGES.service_fetch_error}
                )
            serviceData = await SERVICES_TASKS.getService(service)
            if not serviceData:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.service_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={'error':RESPONSE_MESSAGES.service_fetch_error}
                )
            
            try:
                cache.set(cache_key, serviceData, 3600)  # Cache for 1 hour
            except Exception:
                pass  # Redis down — skip caching, still return the ORM result
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.service_fetch_success,
                code=RESPONSE_CODES.success,
                data=serviceData
            )

        except Exception as e:
            pass
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.service_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )
    
    @classmethod
    async def getAllService(self,page,size,filterType=None,id=None,state=None,query=None)->LocalResponse:
        try:
            params = f"{page}_{size}_{filterType}_{id}_{state}_{query}"
            cache_key = f"all_services_pagi_{hashlib.md5(params.encode()).hexdigest()}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.service_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=cached_data
                )

            serviceData=[]
            related_qs = []
            filterQuery=Q()
            if state:
                filterQuery |= Q(business__business_location__locationState__value__iexact=state)
            if query:
                filterQuery |= Q(value__icontains=query)
                filterQuery |= Q(lable__icontains=query)
            
            if filterType and id:
                if filterType == "category":
                    filterQuery |= Q(category__id=int(id))
                elif filterType == "subCategory":
                    filterQuery |= Q(subCategory__id=int(id))

            if filterQuery:
                related_qs = Service.objects.filter(filterQuery).order_by('index')
            else:
                related_qs = Service.objects.all().order_by('index')

            if related_qs.count() == 0:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.service_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={'error':RESPONSE_MESSAGES.service_fetch_error}
                )
            paginated = await MY_METHODS.paginate_queryset(related_qs, page, size)
            serviceData = []

            for c in paginated["results"]:
                data = await SERVICES_TASKS.getService(c)
                if data:
                    serviceData.append(data)
            paginated['pagination']['data'] = serviceData
            
            cache.set(cache_key, paginated['pagination'], 3600)  # Cache for 1 hour
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.service_fetch_success,
                code=RESPONSE_CODES.success,
                data=paginated['pagination']
            )

        except Exception as e:
            pass
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.service_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )
    @classmethod
    async def getServicesForBusiness(self,business:Business)->LocalResponse:
        try:
            cache_key = f"services_business_{business.id}"
            # Cache is best-effort — a Redis outage must NOT fail the owner's
            # listing (see ISSUE-001 / F3). Fall through to the ORM on any error.
            try:
                cached_data = cache.get(cache_key)
            except Exception:
                cached_data = None
            if cached_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.services_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=cached_data
                )

            services:Service = await sync_to_async(
            lambda: business.services.all().order_by('index')
        )()
            servicesData = []
            for service in services:
                serviceData = await SERVICES_TASKS.getService(service)
                if serviceData:
                    servicesData.append(serviceData)

            try:
                cache.set(cache_key, servicesData, 3600)  # Cache for 1 hour
            except Exception:
                pass  # Redis down — skip caching, still return the ORM result
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.services_fetch_success,
                code=RESPONSE_CODES.success,
                data=servicesData
            )

        except Exception as e:
            pass
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.services_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )
        
    @classmethod
    def _bustBusinessCache(self, business_id, service_id=None):
        """Invalidate the service caches a write just made stale.

        Two layers cache the same data under different key schemes (controller
        `service_detail_*` / `services_business_*`, view `cache:service:*`), so
        both must go or the seller sees a stale read. The per-item detail keys
        were missing, so an edit stayed invisible on the detail endpoint for the
        full TTL. Pass service_id on update/delete."""
        keys = [
            f"services_business_{business_id}",
            f"cache:service:business:owner:{business_id}",
            f"cache:service:business:{business_id}",
        ]
        if service_id is not None:
            keys += [f"service_detail_{service_id}", f"cache:service:{service_id}"]
        try:
            cache.delete_many(keys)
        except Exception:
            pass

    @classmethod
    async def createService(self,business:Business,data:dict)->LocalResponse:
        try:
            service = await SERVICES_TASKS.createService(business,data)
            if not service:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.service_create_error,
                    code=RESPONSE_CODES.error,
                    data={'error':RESPONSE_MESSAGES.service_create_error}
                )
            self._bustBusinessCache(business.id)
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.service_create_success,
                code=RESPONSE_CODES.success,
                data=service
            )
        except Exception as e:
            pass
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.service_create_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )
    
    @classmethod
    async def updateService(self,business:Business,serviceId:int,data:dict)->LocalResponse:
        try:
            service = Service.objects.get(id=serviceId,business=business)
            if not service:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.service_update_error,
                    code=RESPONSE_CODES.error,
                    data={'error':RESPONSE_MESSAGES.service_update_error}
                )
            service = await SERVICES_TASKS.updateService(service,data)
            if not service:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.service_update_error,
                    code=RESPONSE_CODES.error,
                    data={'error':RESPONSE_MESSAGES.service_update_error}
                )
            self._bustBusinessCache(business.id, serviceId)
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.service_update_success,
                code=RESPONSE_CODES.success,
                data=service
            )
            
        except Exception as e:
            pass
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.service_update_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )
    
    @classmethod
    async def deleteService(self,business:Business,serviceId:int)->LocalResponse:
        try:
            service = Service.objects.get(id=serviceId,business=business)
            if not service:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.service_delete_error,
                    code=RESPONSE_CODES.error,
                    data={'error':RESPONSE_MESSAGES.service_delete_error}
                )
            service = await SERVICES_TASKS.deleteService(service)
            if not service:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.service_delete_error,
                    code=RESPONSE_CODES.error,
                    data={'error':RESPONSE_MESSAGES.service_delete_error}
                )
            self._bustBusinessCache(business.id, serviceId)
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.service_delete_success,
                code=RESPONSE_CODES.success,
                data=service
            )
        except Exception as e:
            pass
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.service_delete_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )
        

    @classmethod
    async def GetRelatedServices(cls, serviceId: int, page: int = 1, size: int = 10):
        try:
            cache_key = f"related_services_{serviceId}_{page}_{size}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message="Related services fetched successfully",
                    code=RESPONSE_CODES.success,
                    data=cached_data
                )

            service = Service.objects.get(id=serviceId)
            related_qs = Service.objects.filter(
                                Q(title__icontains=service.title.split(" ")[0])
                                | Q(orignalPrice__range=(service.orignalPrice * 0.8, service.orignalPrice * 1.2))
                                | Q(business=service.business)
                            ).exclude(id=service.id)

            paginated = await MY_METHODS.paginate_queryset(related_qs, page, size)
            serviceData = []

            for c in paginated["results"]:
                data = await SERVICES_TASKS.getService(c)
                if data:
                    serviceData.append(data)
            paginated['pagination']['data'] = serviceData

            cache.set(cache_key, paginated["pagination"], 3600)  # Cache for 1 hour
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Related services fetched successfully",
                code=RESPONSE_CODES.success,
                data=paginated["pagination"]
            )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Error fetching related catelogues",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )
        
    @classmethod
    async def GetServiceTab(cls):
        try:
            cache_key = "service_tab_data"
            cached_data = cache.get(cache_key)
            if cached_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.service_tab_success,
                    code=RESPONSE_CODES.success,
                    data=cached_data
                )

            categorys = ProductCategory.objects.all()
            tabData = []
            for category in categorys:
                if category.catServices.all().count():
                    categoryData = await PRODUCTS_TASKS.getCategoriesDataTask(category)
                    if categoryData:
                        categoryData['type']='category'
                        tabData.append(categoryData)
            subCategorys = ProductSubCategory.objects.all()
            for subCategory in subCategorys:
                if subCategory.subcatServices.all().count():
                    subCategoryData = await PRODUCTS_TASKS.getCategoriesDataTask(subCategory)
                    if subCategoryData:
                        subCategoryData['type']='subCategory'
                        tabData.append(subCategoryData)
            
            cache.set(cache_key, tabData, 86400)  # Cache for 24 hours
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.service_tab_success,
                code=RESPONSE_CODES.success,
                data=tabData
                )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.service_tab_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
                )