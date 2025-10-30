from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business
from interior_products.models import Service

from .Tasks.servicesTasks import SERVICES_TASKS
from .Validators.servicesValidators import SERVICES_VALIDATORS




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