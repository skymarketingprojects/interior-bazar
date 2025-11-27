from asgiref.sync import sync_to_async
from interior_products.models import InteriorServices

class INTERIOR_SERVICE_TASKS:
    
    @classmethod
    async def GetServiceData(cls,service:InteriorServices):
        try:
            data = {
                'id':service.id,
                'value':service.value,
                'lable':service.lable,
                'imageSQUrl':service.imageSQUrl,
                'imageRTUrl':service.imageRTUrl,
                'link':service.link
            }
            return True,data
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetServiceData: {e}')
            return False

