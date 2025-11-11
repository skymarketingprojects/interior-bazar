import asyncio
from adrf.decorators import api_view
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Controllers.OfferText.OfferTextController import OFFER_TEXT_CONTROLLER

@api_view(['GET'])
async def GetOfferText(request):
    try:
        responseData = await OFFER_TEXT_CONTROLLER.GetOfferText()
        return ServerResponse(
            response=responseData.response,
            message=responseData.message,
            code=responseData.code,
            data=responseData.data
        )
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.OFFER_TEXT_FETCH_ERROR,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })