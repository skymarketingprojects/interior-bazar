from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse

from .Tasks.OfferTextTasks import OFFER_TEXT_TASKS

from django.core.exceptions import ObjectDoesNotExist
from app_ib.models import OfferText
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
class OFFER_TEXT_CONTROLLER:
    
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.OFFER_TEXT_FETCH_ERROR,
        successMessage=RESPONSE_MESSAGES.OFFER_TEXT_FETCH_SUCCESS,
        responseFunc=LocalResponse
    )
    async def GetOfferText(self):
        offerText = await sync_to_async(OfferText.objects.all)()
        status,offerText = await OFFER_TEXT_TASKS.GetOfferText(offerText[0])
        if status:
            return offerText
        else:
            raise ObjectDoesNotExist(RESPONSE_MESSAGES.OFFER_TEXT_FETCH_ERROR)
