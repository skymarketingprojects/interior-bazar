from asgiref.sync import sync_to_async
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES

class OFFER_TEXT_TASKS:
    
    @classmethod
    async def GetOfferText(cls, offerText):
        try:
            offerData = {
                NAMES.TEXT: offerText.text.html,
                NAMES.LINK: offerText.link,
                NAMES.SHOW: offerText.show
            }
            return offerData
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in GetOfferText {e}')
            return None

