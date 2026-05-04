from django.shortcuts import render
from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from .Controllers.MessageBot.MessageBotController import MESSAGE_BOT_CONTROLLER
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from django.core.cache import cache
from asgiref.sync import sync_to_async

cache_get = sync_to_async(cache.get)
cache_set = sync_to_async(cache.set)
# Create your views here.

@api_view(["GET"])
async def GetMessagesView(request):
    try:
        # Global Cache for bot messages (TTL: 48 hours)
        cache_key = "cache:bot:messages"
        cached_data = await cache_get(cache_key)

        if cached_data:
            return ServerResponse(
                response=cached_data['response'],
                code=cached_data['code'],
                data=cached_data['data'],
                message=cached_data['message']
            )

        messageResponse = await MESSAGE_BOT_CONTROLLER.GetMessages()

        await cache_set(cache_key, {
            'response': messageResponse.response,
            'code': messageResponse.code,
            'data': messageResponse.data,
            'message': messageResponse.message
        }, timeout=172800) # 48 hours TTL

        return ServerResponse(
            response=messageResponse.response,
            code=messageResponse.code,
            data=messageResponse.data,
            message=messageResponse.message
        )
    except Exception as e:
        return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR:str(e)},
                message="messages found Error"
            )