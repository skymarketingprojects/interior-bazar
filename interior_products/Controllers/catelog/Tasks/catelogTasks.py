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
            pass
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

            pass
            prodSubCategory=[]

            for subCat in catelog.subCategory.all():
                tempdata = await PRODUCTS_TASKS.getCategoriesDataTask(subCat)
                prodSubCategory.append(tempdata)
            pass
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
            pass
            return data
        except Exception as e:
            pass
            return False
        
    @classmethod
    async def createCatelog(self, business:Business, data:dict):
        try:
            # catelogueType is a required (PROTECT) FK. The v3 dashboard create
            # form does not collect a catalogue "type", so fall back to the
            # seller's own business type, then to any available type. (F3: without
            # this the create raised AttributeError on `data.type.id` and 0 rows
            # were ever persisted.)
            type_id = getattr(getattr(data, 'type', None), 'id', None)
            if type_id:
                catelogType = await sync_to_async(BusinessType.objects.get)(id=type_id)
            else:
                catelogType = await sync_to_async(lambda: business.businessType)()
                if catelogType is None:
                    catelogType = await sync_to_async(BusinessType.objects.first)()
            if catelogType is None:
                return False
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
                        await sync_to_async(CatelogueImage.objects.create)(
                            catelouge=catelog,
                            catelougeImage=getattr(image, 'imageUrl', '') or getattr(image, 'catelougeImage', ''),
                            index=getattr(image, 'index', 0) or 0,
                            link=getattr(image, 'link', '') or ''
                        )
            except Exception as e:
                pass
                pass
            data = await self.getCatelog(catelog)
            return data
        except Exception as e:
            pass
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
            pass
            try:
                if data.type:
                    catelogType = BusinessType.objects.get(id=data.type.id)
                    catelog.catelogueType = catelogType
            except Exception as e:
                pass
                pass
            try:
                if data.images:
                    for image in data.images:
                        _imgId = getattr(image, 'id', None)
                        _imgUrl = getattr(image, 'imageUrl', '') or getattr(image, 'catelougeImage', '')
                        _imgIdx = getattr(image, 'index', 0) or 0
                        _imgLink = getattr(image, 'link', '') or ''
                        #update already created images
                        if _imgId:
                            await sync_to_async(CatelogueImage.objects.filter(id=_imgId).update)(
                                catelougeImage=_imgUrl, index=_imgIdx, link=_imgLink
                            )
                        #create new images
                        else:
                            await sync_to_async(CatelogueImage.objects.create)(
                                catelouge=catelog,
                                catelougeImage=_imgUrl, index=_imgIdx, link=_imgLink
                            )
            except Exception as e:
                pass
                pass
            catelog.save()
            catdata = await self.getCatelog(catelog)
            return catdata
        except Exception as e:
            pass
            return False
    @classmethod
    async def deleteCatelog(self,catelog:Catelogue):
        try:
            catelog.delete()
            return True
        except Exception as e:
            pass
            return False

