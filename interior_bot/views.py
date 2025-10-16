from django.shortcuts import render
from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from .Controllers.MessageBot.MessageBotController import MESSAGE_BOT_CONTROLLER
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
# Create your views here.

@api_view(["GET"])
# @permission_classes(IsAuthenticated)
async def GetMessagesView(request):
    try:
        messageResponse = await MESSAGE_BOT_CONTROLLER.GetMessages()

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
                data={"error":str(e)},
                message="messages found Error"
            )