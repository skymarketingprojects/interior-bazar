from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Controllers.OfferText.OfferTextController import OFFER_TEXT_CONTROLLER
from app_ib.decorators.ViewDecorator import exceptionHandler
from app_ib.Utils.MyMethods import MY_METHODS

@api_view(['GET'])
@exceptionHandler(
    responseFunc=ServerResponse,
    errorMessage=RESPONSE_MESSAGES.OFFER_TEXT_FETCH_ERROR,
)
async def GetOfferText(request):
    # --- NORMAL LOGIC (won't be reached in this test) ---
    responseData = await OFFER_TEXT_CONTROLLER.GetOfferText()
    return responseData
