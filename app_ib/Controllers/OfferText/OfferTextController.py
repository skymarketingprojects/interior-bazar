from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse

from .Tasks.OfferTextTasks import OFFER_TEXT_TASKS
from .Validators.OfferTextValidators import OFFER_TEXT_VALIDATORS

from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import OfferText

class OFFER_TEXT_CONTROLLER:
    
    @classmethod
    async def GetOfferText(self):
        try:
            offerText = await sync_to_async(OfferText.objects.all)()
            offerText = await OFFER_TEXT_TASKS.GetOfferText(offerText[0])
            if offerText:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.OFFER_TEXT_FETCH_SUCCESS,
                    code=RESPONSE_CODES.success,
                    data=offerText)
            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.OFFER_TEXT_FETCH_ERROR,
                    code=RESPONSE_CODES.error,
                    data={})
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.OFFER_TEXT_FETCH_ERROR,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })
