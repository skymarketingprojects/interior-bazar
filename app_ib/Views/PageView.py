import asyncio
from app_ib.Utils.MyMethods import MY_METHODS
from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Controllers.Pages.PagesController import PAGE_CONTROLLER
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from asgiref.sync import sync_to_async

cache_get = sync_to_async(cache.get)
cache_set = sync_to_async(cache.set)

@api_view(['GET'])
async def GetPagesView(request,page_name):
    try:
        data = MY_METHODS.json_to_object(request.data)
        pass

        # Global Cache with predictable key for Delete-on-Write invalidation
        cache_key = f"cache:page:{page_name}"
        cached_data = await cache_get(cache_key)
        
        if cached_data:
            return ServerResponse(
                response=cached_data['response'],
                message=cached_data['message'],
                code=cached_data['code'],
                data=cached_data['data']
            )

        get_page_resp = await PAGE_CONTROLLER.GetPages(page_name=page_name)
        pass

        cache_data = {
            'response': get_page_resp.response,
            'message': get_page_resp.message,
            'code': get_page_resp.code,
            'data': get_page_resp.data
        }
        await cache_set(cache_key, cache_data, timeout=43200) # 12 hours TTL

        return ServerResponse(
            response=get_page_resp.response,
            message=get_page_resp.message,
            code=get_page_resp.code,
            data=get_page_resp.data
        )

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.page_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            }
        )
    
@api_view(['GET'])
async def GetQnAView(request):
    try:

        # Global Cache for all Q&As (TTL: 24 hours)
        cache_key = "cache:qna:all"
        cached_data = await cache_get(cache_key)

        if cached_data:
            return ServerResponse(
                response=cached_data['response'],
                message=cached_data['message'],
                code=cached_data['code'],
                data=cached_data['data']
            )

        get_qna_resp = await PAGE_CONTROLLER.GetQnA()
        pass

        cache_data = {
            'response': get_qna_resp.response,
            'message': get_qna_resp.message,
            'code': get_qna_resp.code,
            'data': get_qna_resp.data
        }
        await cache_set(cache_key, cache_data, timeout=86400) # 24 hours TTL

        return ServerResponse(
            response=get_qna_resp.response,
            message=get_qna_resp.message,
            code=get_qna_resp.code,
            data=get_qna_resp.data
        )

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.qna_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            }
        )