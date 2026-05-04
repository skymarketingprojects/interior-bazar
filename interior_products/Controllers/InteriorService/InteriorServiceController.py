from asgiref.sync import sync_to_async
from django.core.cache import cache

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
            cache_key = f"interior_services_{pageNo}_{pageSize}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.service_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=cached_data
                )

            related_qs = InteriorServices.objects.all().order_by('index')

            paginated = await MY_METHODS.paginate_queryset(related_qs, pageNo, pageSize)
            serviceData = []

            for c in paginated["results"]:
                status,data = await INTERIOR_SERVICE_TASKS.GetServiceData(c)
                if status:
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

