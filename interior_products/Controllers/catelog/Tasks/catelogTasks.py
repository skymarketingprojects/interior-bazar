from asgiref.sync import sync_to_async
from interior_products.models import Catelogue, CatelogueImage, ProductSubCategory, ProductCategory
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business, BusinessType
from interior_products.Controllers.products.Tasks.productsTasks import PRODUCTS_TASKS
from django.db.models import Prefetch
import asyncio

class CATELOG_TASKS:
    
    @classmethod
    async def BulkSerializeCatelogs(cls, catelog_list):
        """High-performance bulk serialization for catalogs."""
        def run_sync_serialization():
            results = []
            for catelog in catelog_list:
                try:
                    type_ins = catelog.catelogueType
                    bus_ins = catelog.business
                    user_ins = bus_ins.user
                    profile = getattr(user_ins, 'user_profile', None)

                    images = catelog.catelogueImages.all()
                    imageData = [{
                        "id": img.id,
                        "imageUrl": img.catelougeImage,
                        "index": img.index,
                        "link": img.link
                    } for img in images]

                    prodCategory = [PRODUCTS_TASKS.getCategoriesDataSync(cat) for cat in catelog.catalogCategory.all()]
                    prodSubCategory = [PRODUCTS_TASKS.getCategoriesDataSync(sub) for sub in catelog.subCategory.all()]

                    results.append({
                        "id": catelog.id,
                        "title": catelog.title,
                        "downloadLink": catelog.catelougePdf,
                        "images": imageData,
                        "category": catelog.category,
                        "type": {
                            "id": type_ins.id if type_ins else None,
                            "value": type_ins.value if type_ins else None,
                            "label": type_ins.lable if type_ins else None
                        },
                        "business": {
                            "id": bus_ins.id,
                            "name": bus_ins.businessName
                        },
                        "downloads": catelog.totalDownload,
                        "ytLink": catelog.ytLink,
                        "uploadedForTime": MY_METHODS.get_time_ago_sync(catelog.createdAt),
                        "categories": prodCategory,
                        "subCategories": prodSubCategory,
                        "phone": profile.phone if profile else "",
                        "countryCode": profile.countryCode if profile else ""
                    })
                except Exception as e:
                    # Log the error if needed but continue with next
                    # print(f"Error serializing catelog {catelog.id}: {e}")
                    pass
            return results

        return await sync_to_async(run_sync_serialization)()

    @classmethod
    async def getCatelog(cls, catelog: Catelogue):
        # Fetch relationship data if not pre-fetched
        queryset = Catelogue.objects.filter(pk=catelog.pk).select_related(
            'catelogueType', 'business', 'business__user', 'business__user__user_profile'
        ).prefetch_related('catelogueImages', 'catalogCategory', 'subCategory')
        
        objs = await sync_to_async(list)(queryset)
        results = await cls.BulkSerializeCatelogs(objs)
        return results[0] if results else None

    @classmethod
    async def createCatelog(cls, business: Business, data: dict):
        try:
            cat_type = await sync_to_async(BusinessType.objects.get)(id=data.type.id)
            catelog = await sync_to_async(Catelogue.objects.create)(
                business=business, title=data.title, catelougePdf=data.downloadLink,
                category=data.category, catelogueType=cat_type, ytLink=data.ytLink
            )
            
            category_ids = [cat.id for cat in getattr(data, 'categories', [])][:3]
            sub_ids = [cat.id for cat in getattr(data, 'subCategories', [])][:3]
            
            cats, subs = await asyncio.gather(
                sync_to_async(lambda: list(ProductCategory.objects.filter(id__in=category_ids)))(),
                sync_to_async(lambda: list(ProductSubCategory.objects.filter(id__in=sub_ids)))()
            )
            
            await sync_to_async(catelog.catalogCategory.set)(cats)
            await sync_to_async(catelog.subCategory.set)(subs)
            
            if hasattr(data, 'images') and data.images:
                img_objs = [CatelogueImage(catelouge=catelog, catelougeImage=img.imageUrl, index=img.index, link=img.link) for img in data.images]
                await sync_to_async(CatelogueImage.objects.bulk_create)(img_objs)
                
            return await cls.getCatelog(catelog)
        except: return False

    @classmethod
    async def updateCatelog(cls, catelog: Catelogue, data: dict):
        try:
            catelog.title = data.title
            catelog.catelougePdf = data.downloadLink
            catelog.category = data.category
            catelog.ytLink = data.ytLink
            
            # Sync categories
            cat_ids = [c.id for c in getattr(data, 'categories', [])][:3]
            sub_ids = [c.id for c in getattr(data, 'subCategories', [])][:3]
            
            cats, subs = await asyncio.gather(
                sync_to_async(lambda: list(ProductCategory.objects.filter(id__in=cat_ids)))(),
                sync_to_async(lambda: list(ProductSubCategory.objects.filter(id__in=sub_ids)))()
            )
            await sync_to_async(catelog.catalogCategory.set)(cats)
            await sync_to_async(catelog.subCategory.set)(subs)

            if hasattr(data, 'type') and data.type:
                catelog.catelogueType = await sync_to_async(BusinessType.objects.get)(id=data.type.id)
            
            await sync_to_async(catelog.save)()
            
            # Update images via Task call (can be optimized further but usually few images)
            if hasattr(data, 'images') and data.images:
                for img in data.images:
                    if img.id:
                        await sync_to_async(CatelogueImage.objects.filter(id=img.id).update)(
                            catelougeImage=img.imageUrl, index=img.index, link=img.link)
                    else:
                        await sync_to_async(CatelogueImage.objects.create)(
                            catelouge=catelog, catelougeImage=img.imageUrl, index=img.index, link=img.link)
            
            return await cls.getCatelog(catelog)
        except: return False

    @classmethod
    async def deleteCatelog(cls, catelog: Catelogue):
        try:
            await sync_to_async(catelog.delete)()
            return True
        except: return False
