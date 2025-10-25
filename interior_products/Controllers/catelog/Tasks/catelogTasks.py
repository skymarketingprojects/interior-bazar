from asgiref.sync import sync_to_async
from interior_products.models import Catelogue
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business,BusinessType
class CATELOG_TASKS:
    @classmethod
    async def getCatelog(self, catelog:Catelogue):
        data = {}
        try:
            catelogType = {
                "id": catelog.catelogueType.id,
                "value": catelog.catelogueType.value,
                "label": catelog.catelogueType.lable
            }
            businessData = {
                "id": catelog.business.id,
                "name": catelog.business.business_name
            }
            time_ago = await MY_METHODS.get_time_ago(updated_at=catelog.createdAt)
            data = {
                "id": catelog.id,
                "title": catelog.title,
                "downloadLink": catelog.catelougePdf,
                "imageUrl": catelog.catelougeImage,
                "category": catelog.category,
                "type": catelogType,
                "business": businessData,
                "downloads": catelog.totalDownload,
                "uploadedForTime": time_ago
            }
            return data
        except Exception as e:
            await MY_METHODS.printStatus(f"Error in getCatelog: {str(e)}")
            return False
        
    @classmethod
    async def createCatelog(self, business:Business, data:dict):
        try:
            await MY_METHODS.printStatus(f"createCatelog: {data.type.id}")
            catelogType = await sync_to_async(BusinessType.objects.get)(id=data.type.id)
            catelog = await sync_to_async(Catelogue.objects.create)(
                business=business,
                title=data.title,
                catelougePdf=data.downloadLink,
                catelougeImage=data.imageUrl,
                category=data.category,
                catelogueType=catelogType
            )
            data = await self.getCatelog(catelog)
            return data
        except Exception as e:
            await MY_METHODS.printStatus(f"Error in createCatelog: {str(e)}")
            return False
        
    @classmethod
    async def updateCatelog(self,catelog:Catelogue,data:dict):
        try:
            catelog.title = data.title
            catelog.catelougeImage = data.imageUrl
            catelog.catelougePdf = data.downloadLink
            catelog.category = data.category
            try:
                if data.type:
                    catelogType = BusinessType.objects.get(id=data.type.id)
                    catelog.catelogueType = catelogType
            except Exception as e:
                await MY_METHODS.printStatus(f"Error in updateCatelog: {str(e)}")
                pass
            catelog.save()
            catdata = await self.getCatelog(catelog)
            return catdata
        except Exception as e:
            await MY_METHODS.printStatus(f"Error in updateCatelog: {str(e)}")
            return False
    @classmethod
    async def deleteCatelog(self,catelog:Catelogue):
        try:
            catelog.delete()
            return True
        except Exception as e:
            await MY_METHODS.printStatus(f"Error in deleteCatelog: {str(e)}")
            return False

