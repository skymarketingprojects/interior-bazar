from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES

from app_ib.Controllers.StockMediaController.StockMediaController import StockMediaController
from django.core.cache import cache
from asgiref.sync import sync_to_async


@api_view(['GET'])
async def GetStockMedia(request,page,section):
    try:
        cache_key = f"cache:stockmedia:{page}:{section}"
        cached_data = await cache.aget(cache_key)

        if cached_data:
            response = ServerResponse(
                response=cached_data['response'],
                code=cached_data['code'],
                message=cached_data['message'],
                data=cached_data['data']
            )
            # Edge/CDN/Browser Caching (1 Year)
            response['Cache-Control'] = 'public, max-age=31536000, immutable'
            return response

        final_response = await StockMediaController.getStockMedia(pagename=page,sectionname=section)
        
        cache_data = {
            'response': final_response.response,
            'code': final_response.code,
            'message': final_response.message,
            'data': final_response.data
        }
        # Backend Redis Cache (1 Year)
        await cache.aset(cache_key, cache_data, timeout=31536000)

        response = ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
        )
        response['Cache-Control'] = 'public, max-age=31536000, immutable'
        return response
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.default_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })
