from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.MyMethods import MY_METHODS

from .Tasks.InteriorServiceTasks import INTERIOR_SERVICE_TASKS
from .Validators.InteriorServiceValidators import INTERIOR_SERVICE_VALIDATORS

from interior_products.models import InteriorServices

class INTERIOR_SERVICE_CONTROLLER:
    
    @classmethod
    async def getInteriorService(request,pageNo=1,pageSize=10):
        try:
            related_qs = InteriorServices.objects.all().order_by('index')

            paginated = await MY_METHODS.paginate_queryset(related_qs, pageNo, pageSize)
            serviceData = []

            for c in paginated["results"]:
                status,data = await INTERIOR_SERVICE_TASKS.GetServiceData(c)
                if status:
                    serviceData.append(data)
            paginated['pagination']['data'] = serviceData
            
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.service_fetch_success,
                code=RESPONSE_CODES.success,
                data=paginated['pagination']
            )
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in getService: {str(e)}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.service_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )

