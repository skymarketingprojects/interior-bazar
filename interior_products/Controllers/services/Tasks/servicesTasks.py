from asgiref.sync import sync_to_async
from interior_products.models import Service,ServiceImage
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business
import json

class SERVICES_TASKS:
    @classmethod
    async def deleteService(self,service:Service):
        try:
            service.delete()
            return True
        except Exception as e:
            await MY_METHODS.printStatus(f"Error in deleteservice: {str(e)}")
            return False
    
    @classmethod
    async def updateService(self,service:Service,data:dict):
        try:
            service.title = data.title
            service.orignalPrice = data.price
            service.discountType = data.discountType
            service.discountBy = data.discountBy
            service.description = data.description
            service.serviceTags = data.serviceTags
            service.save()
            try:
                if data.images:
                    for image in data.images:
                        if image.id:
                            await sync_to_async(ServiceImage.objects.filter(id=image.id).update)(
                                image=image.imageUrl,
                                index=image.index,
                                link=image.link
                            )
                        else:
                            await sync_to_async(ServiceImage.objects.create)(
                                service=service,
                                image=image.imageUrl,
                                index=image.index,
                                link=image.link
                            )
            except Exception as e:
                await MY_METHODS.printStatus(f"Error in updateservice: {str(e)}")
                pass
            data = await self.getService(service)
            return data
        except Exception as e:
            await MY_METHODS.printStatus(f"Error in updateservice: {str(e)}")
            return False
    
    @classmethod
    async def createService(self,business:Business,data:dict):
        try:
            service = await sync_to_async(Service.objects.create)(
                business=business,
                title=data.title,
                orignalPrice=data.price,
                discountType=data.discountType,
                discountBy=data.discountBy,
                description=data.description,
                serviceTags=data.serviceTags
            )
            try:
                if data.images:
                    for image in data.images:
                        await sync_to_async(ServiceImage.objects.create)(
                            service=service,
                            image=image.imageUrl,
                            index=image.index,
                            link=image.link
                        )
            except Exception as e:
                await MY_METHODS.printStatus(f"Error in createService: {str(e)}")
                pass
            data = await self.getService(service)
            return data
        except Exception as e:
            await MY_METHODS.printStatus(f"Error in createService: {str(e)}")
            return False
        
    @classmethod
    async def getService(self,service:Service):
        try:
            serviceImages = await sync_to_async(service.serviceImages.all)()
            serviceImageData = []
            for image in serviceImages:
                serviceImageData.append({
                    'id':image.id,
                    'imageUrl':image.image,
                    'index':image.index,
                    'link':image.link
                })
            tags = json.loads(str(service.serviceTags).replace("'",'"')) if service.serviceTags else []
            serviceData = {
                'id':service.id,
                'title':service.title,
                'orignalPrice':service.orignalPrice,
                'price':service.orignalPrice,
                'discountType':service.discountType,
                'discountBy':service.discountBy,
                'description':service.description,
                'serviceTags':tags,
                'images':serviceImageData,
                'displayPrice':service.displayPrice,
                'index':service.index
            }
            return serviceData
        except Exception as e:
            await MY_METHODS.printStatus(f"Error in getservice: {str(e)}")
            return False
