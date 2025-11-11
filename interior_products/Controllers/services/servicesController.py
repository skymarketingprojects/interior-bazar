from asgiref.sync import sync_to_async
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
            
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.service_fetch_success,
                code=RESPONSE_CODES.success,
                data=serviceData
            )
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in getService: {str(e)}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.service_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )
    
    @classmethod
    async def getAllService(self,page,size,filterType=None,id=None)->LocalResponse:
        try:
            serviceData=[]
            related_qs = []
            if filterType and id:
                if filterType == "category":
                    category = await sync_to_async(ProductCategory.objects.get)(id=int(id))
                    related_qs = category.catServices.all()
                elif filterType == "subCategory":
                    subCategory = await sync_to_async(ProductSubCategory.objects.get)(id=int(id))
                    related_qs = subCategory.subcatServices.all()
            else:
                related_qs = Service.objects.all()

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
            
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.service_fetch_success,
                code=RESPONSE_CODES.success,
                data=paginated['pagination']
            )
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in getService: {str(e)}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.service_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )
    @classmethod
    async def getServicesForBusiness(self,business:Business)->LocalResponse:
        try:
            services = await sync_to_async(
            lambda: business.services.all().order_by('index')
        )()
            servicesData = []
            for service in services:
                serviceData = await SERVICES_TASKS.getService(service)
                if serviceData:
                    servicesData.append(serviceData)
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.services_fetch_success,
                code=RESPONSE_CODES.success,
                data=servicesData
            )
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in get Services: {str(e)}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.services_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )
        
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
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.service_create_success,
                code=RESPONSE_CODES.success,
                data=service
            )
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in createservice: {str(e)}")
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
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.service_update_success,
                code=RESPONSE_CODES.success,
                data=service
            )
            
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in updateservice: {str(e)}")
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
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.service_delete_success,
                code=RESPONSE_CODES.success,
                data=service
            )
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in deleteservice: {str(e)}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.service_delete_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )
        

    @classmethod
    async def GetRelatedServices(cls, serviceId: int, page: int = 1, size: int = 10):
        try:
            service = Service.objects.get(id=serviceId)
            tags = [tag.strip().lower() for tag in service.serviceTags.split(",")]
            related_qs = Service.objects.filter(
                                Q(serviceTags__iregex=r"(" + "|".join(tags) + ")")
                                | Q(title__icontains=service.title.split(" ")[0])
                                | Q(orignalPrice__range=(service.orignalPrice * 0.8, service.orignalPrice * 1.2))
                            ).exclude(id=service.id)

            paginated = await MY_METHODS.paginate_queryset(related_qs, page, size)
            serviceData = []

            for c in paginated["results"]:
                data = await SERVICES_TASKS.getService(c)
                if data:
                    serviceData.append(data)
            paginated['pagination']['data'] = serviceData

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Related catelogues fetched successfully",
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