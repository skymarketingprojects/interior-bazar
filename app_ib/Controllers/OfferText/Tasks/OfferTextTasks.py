from asgiref.sync import sync_to_async
from app_ib.Utils.MyMethods import MY_METHODS

class OFFER_TEXT_TASKS:
    
    @classmethod
    async def GetOfferText(cls, offerText):
        try:
            offerData = {
                "text": offerText.text.html,
                "link": offerText.link,
                "show": offerText.show
            }
            return offerData
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in GetOfferText {e}')
            return None

