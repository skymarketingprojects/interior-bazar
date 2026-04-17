from asgiref.sync import sync_to_async
from interior_products.models import InteriorServices

class INTERIOR_SERVICE_TASKS:
    
    @classmethod
    async def BulkSerializeServices(cls, service_list):
        """Unified bulk serialization for interior services."""
        return [{
            'id': service.id,
            'value': service.value,
            'lable': service.lable,
            'imageSQUrl': service.imageSQUrl,
            'imageRTUrl': service.imageRTUrl,
            'link': service.link
        } for service in service_list]

    @classmethod
    async def GetServiceData(cls, service: InteriorServices):
        """Maintained for single-item compatibility."""
        data = {
            'id': service.id, 'value': service.value, 'lable': service.lable,
            'imageSQUrl': service.imageSQUrl, 'imageRTUrl': service.imageRTUrl, 'link': service.link
        }
        return True, data
