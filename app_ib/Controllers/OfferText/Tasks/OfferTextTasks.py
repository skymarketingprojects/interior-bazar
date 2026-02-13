from asgiref.sync import sync_to_async
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
from app_ib.models import OfferText
from app_ib.decorators.ViewDecorator import taskExceptionHandler
class OFFER_TEXT_TASKS:
    
    @classmethod
    @taskExceptionHandler
    async def GetOfferText(cls, offerText: OfferText):
        offerData = {
            NAMES.TEXT: offerText.text.html,
            NAMES.LINK: offerText.link,
            NAMES.COLOR: offerText.color,
            NAMES.SHOW: offerText.show
        }
        return True,offerData

