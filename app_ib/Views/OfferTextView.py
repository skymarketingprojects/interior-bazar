from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Controllers.OfferText.OfferTextController import OFFER_TEXT_CONTROLLER
from app_ib.decorators.ViewDecorator import exceptionHandler
from app_ib.Utils.MyMethods import MY_METHODS
from django.core.cache import cache
from asgiref.sync import sync_to_async

cache_get = sync_to_async(cache.get)
cache_set = sync_to_async(cache.set)

@api_view(['GET'])
@exceptionHandler(
    responseFunc=ServerResponse,
    errorMessage=RESPONSE_MESSAGES.OFFER_TEXT_FETCH_ERROR,
)
async def GetOfferText(request):
    
    # Global cache for OfferText (TTL: 6 hours)
    cache_key = "cache:offertext"
    cached_data = await cache_get(cache_key)

    if cached_data:
        return LocalResponse(
            response=cached_data['response'],
            code=cached_data['code'],
            message=cached_data['message'],
            data=cached_data['data']
        )

    responseData = await OFFER_TEXT_CONTROLLER.GetOfferText()

    cache_data = {
        'response': responseData.response,
        'code': responseData.code,
        'message': responseData.message,
        'data': responseData.data
    }
    await cache_set(cache_key, cache_data, timeout=21600) # 6 hours TTL

    return responseData
