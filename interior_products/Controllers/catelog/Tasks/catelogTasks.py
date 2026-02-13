from asgiref.sync import sync_to_async
from interior_products.models import Catelogue,CatelogueImage,ProductSubCategory,ProductCategory
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business,BusinessType
from interior_products.Controllers.products.Tasks.productsTasks import PRODUCTS_TASKS
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
                "name": catelog.business.businessName
            }
            catalougeImages:list[CatelogueImage] = await sync_to_async(catelog.catelogueImages.all)()
            # await MY_METHODS.printStatus(f"getCatelog: {catalougeImages}")
            imageData = []
            for image in catalougeImages:
                imageData.append({
                    "id": image.id,
                    "imageUrl": image.catelougeImage,
                    "index": image.index,
                    "link": image.link
                })

            time_ago = await MY_METHODS.get_time_ago(updated_at=catelog.createdAt)
            
            prodCategory=[]
            for cat in catelog.catalogCategory.all():
                tempdata = await PRODUCTS_TASKS.getCategoriesDataTask(cat)
                prodCategory.append(tempdata)

            # await MY_METHODS.printStatus(f"sub category {prodCategory} ")
            prodSubCategory=[]

            for subCat in catelog.subCategory.all():
                tempdata = await PRODUCTS_TASKS.getCategoriesDataTask(subCat)
                prodSubCategory.append(tempdata)
            # await MY_METHODS.printStatus(f"sub category {prodSubCategory} ")
            data = {
                "id": catelog.id,
                "title": catelog.title,
                "downloadLink": catelog.catelougePdf,
                "images": imageData,
                "category": catelog.category,
                "type": catelogType,
                "business": businessData,
                "downloads": catelog.totalDownload,
                "ytLink": catelog.ytLink,
                "uploadedForTime": time_ago,
                "categories":prodCategory,
                "subCategories":prodSubCategory,
                "phone":catelog.business.user.user_profile.phone,
                "countryCode":catelog.business.user.user_profile.countryCode
            }
            # await MY_METHODS.printStatus(f"data {data}")
            return data
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in getCatelog: {str(e)}")
            return False
        
    @classmethod
    async def createCatelog(self, business:Business, data:dict):
        try:
            # await MY_METHODS.printStatus(f"createCatelog: {data.type.id}")
            # await MY_METHODS.printStatus(f"createCatelog: {data.ytLink}")
            catelogType = await sync_to_async(BusinessType.objects.get)(id=data.type.id)
            catelog = await sync_to_async(Catelogue.objects.create)(
                business=business,
                title=data.title,
                catelougePdf=data.downloadLink,
                category=data.category,
                catelogueType=catelogType,
                ytLink=data.ytLink
            )
            category_ids = [cat.id for cat in getattr(data, 'categories', [])]
            if len(category_ids) > 3:
                return None
            categories = await sync_to_async(lambda: list(ProductCategory.objects.filter(id__in=category_ids)))()
            if len(categories) != len(category_ids):
                return None
            

            subCategoryIds = [cat.id for cat in getattr(data, 'subCategories', [])]
            if len(subCategoryIds) > 3:
                return None
            subCategories = await sync_to_async(lambda: list(ProductSubCategory.objects.filter(id__in=subCategoryIds)))()
            if len(subCategories) != len(subCategoryIds):
                return None
            
            await sync_to_async(catelog.catalogCategory.set)(categories)
            await sync_to_async(catelog.subCategory.set)(subCategories)
            try:
                if data.images:
                    for image in data.images:
                        # await MY_METHODS.printStatus(f"createCatelog: {image}")
                        await sync_to_async(CatelogueImage.objects.create)(
                            catelouge=catelog,
                            catelougeImage=image.imageUrl,
                            index=image.index,
                            link=image.link
                        )
            except Exception as e:
                # await MY_METHODS.printStatus(f"Error in createCatelog: {str(e)}")
                pass
            data = await self.getCatelog(catelog)
            return data
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in createCatelog: {str(e)}")
            return False
        
    @classmethod
    async def updateCatelog(self,catelog:Catelogue,data:dict):
        try:
            catelog.title = data.title
            catelog.catelougePdf = data.downloadLink
            catelog.category = data.category
            catelog.ytLink = data.ytLink
            categories = getattr(data, 'categories', None)
            if isinstance(categories, list) and len(categories) <= 3:
                category_ids = [c.id for c in categories]
                category_objs = await sync_to_async(lambda: list(ProductCategory.objects.filter(id__in=category_ids)))()
                if len(category_objs) == len(category_ids):
                    await sync_to_async(catelog.catalogCategory.set)(category_objs)
            
            
            subCategories = getattr(data, 'subCategories', None)
            if isinstance(subCategories, list) and len(subCategories) <= 3:
                category_ids = [c.id for c in subCategories]
                category_objs = await sync_to_async(lambda: list(ProductSubCategory.objects.filter(id__in=category_ids)))()
                if len(category_objs) == len(category_ids):
                    await sync_to_async(catelog.subCategory.set)(category_objs)
            # await MY_METHODS.printStatus(f"update Catelog: {data.ytLink}")
            try:
                if data.type:
                    catelogType = BusinessType.objects.get(id=data.type.id)
                    catelog.catelogueType = catelogType
            except Exception as e:
                # await MY_METHODS.printStatus(f"Error in updateCatelog: {str(e)}")
                pass
            try:
                if data.images:
                    for image in data.images:
                        #update already created images
                        if image.id:
                            await sync_to_async(CatelogueImage.objects.filter(id=image.id).update)(
                                catelougeImage=image.imageUrl,
                                index=image.index,
                                link=image.link
                            )
                        #create new images
                        else:
                            await sync_to_async(CatelogueImage.objects.create)(
                                catelogue=catelog,
                                catelougeImage=image.imageUrl,
                                index=image.index,
                                link=image.link
                            )
            except Exception as e:
                # await MY_METHODS.printStatus(f"Error in createCatelog: {str(e)}")
                pass
            catelog.save()
            catdata = await self.getCatelog(catelog)
            return catdata
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in updateCatelog: {str(e)}")
            return False
    @classmethod
    async def deleteCatelog(self,catelog:Catelogue):
        try:
            catelog.delete()
            return True
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in deleteCatelog: {str(e)}")
            return False

