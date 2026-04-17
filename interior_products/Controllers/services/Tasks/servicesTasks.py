from asgiref.sync import sync_to_async
from interior_products.models import Service, ServiceImage, ProductSubCategory, ProductCategory
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business
import json
from interior_products.Controllers.products.Tasks.productsTasks import PRODUCTS_TASKS
from django.db.models import Prefetch
import asyncio

class SERVICES_TASKS:
    
    @classmethod
    async def BulkSerializeServices(cls, service_list):
        """High-performance bulk serialization for services."""
        results = []
        for service in service_list:
            try:
                # Optimized images (pre-fetched via to_attr if needed)
                images = getattr(service, 'preloaded_images', service.serviceImages.all())
                imageData = [{
                    'id': img.id, 'imageUrl': img.image, 'index': img.index, 'link': img.link
                } for img in images]

                # Fast tags parsing
                tags = []
                if service.serviceTags:
                    try: tags = json.loads(str(service.serviceTags).replace("'", '"'))
                    except: pass

                # Fast categories mapping (synchronous task layer)
                cats = [PRODUCTS_TASKS.SerializeCategorySync(cat) for cat in service.category.all()]
                subs = [PRODUCTS_TASKS.SerializeCategorySync(sub) for sub in service.subCategory.all()]

                results.append({
                    'id': service.id,
                    'title': service.title,
                    'originalPrice': service.orignalPrice,
                    'price': service.orignalPrice,
                    'discountType': service.discountType,
                    'discountBy': service.discountBy,
                    'description': service.description,
                    'serviceTags': tags,
                    'images': imageData,
                    'displayPrice': service.displayPrice,
                    'index': service.index,
                    "categories": cats,
                    "subCategories": subs,
                    "phone": service.business.user.user_profile.phone if hasattr(service.business.user, 'user_profile') else "",
                    "countryCode": service.business.user.user_profile.countryCode if hasattr(service.business.user, 'user_profile') else ""
                })
            except: pass
        return results

    @classmethod
    async def getService(cls, service: Service):
        # Full relationship fetch for single item
        queryset = Service.objects.filter(pk=service.pk).select_related(
            'business', 'business__user', 'business__user__user_profile'
        ).prefetch_related('serviceImages', 'category', 'subCategory')
        
        objs = await sync_to_async(list)(queryset)
        results = await cls.BulkSerializeServices(objs)
        return results[0] if results else None

    @classmethod
    async def createService(cls, business: Business, data: dict):
        try:
            service = await sync_to_async(Service.objects.create)(
                business=business, title=data.title, orignalPrice=data.price,
                discountType=data.discountType, discountBy=data.discountBy,
                description=data.description, serviceTags=data.serviceTags
            )
            
            cat_ids = [cat.id for cat in getattr(data, 'categories', [])][:3]
            sub_ids = [cat.id for cat in getattr(data, 'subCategories', [])][:3]
            
            cats, subs = await asyncio.gather(
                sync_to_async(lambda: list(ProductCategory.objects.filter(id__in=cat_ids)))(),
                sync_to_async(lambda: list(ProductSubCategory.objects.filter(id__in=sub_ids)))()
            )
            await sync_to_async(service.category.set)(cats)
            await sync_to_async(service.subCategory.set)(subs)

            if hasattr(data, 'images') and data.images:
                img_objs = [ServiceImage(service=service, image=img.imageUrl, index=img.index, link=img.link) for img in data.images]
                await sync_to_async(ServiceImage.objects.bulk_create)(img_objs)
                
            return await cls.getService(service)
        except: return False

    @classmethod
    async def updateService(cls, service: Service, data: dict):
        try:
            service.title = data.title
            service.orignalPrice = data.price
            service.discountType = data.discountType
            service.discountBy = data.discountBy
            service.description = data.description
            service.serviceTags = data.serviceTags
            
            cat_ids = [c.id for c in getattr(data, 'categories', [])][:3]
            sub_ids = [c.id for c in getattr(data, 'subCategories', [])][:3]
            
            cats, subs = await asyncio.gather(
                sync_to_async(lambda: list(ProductCategory.objects.filter(id__in=cat_ids)))(),
                sync_to_async(lambda: list(ProductSubCategory.objects.filter(id__in=sub_ids)))()
            )
            await sync_to_async(service.category.set)(cats)
            await sync_to_async(service.subCategory.set)(subs)
            await sync_to_async(service.save)()

            if hasattr(data, 'images') and data.images:
                for img in data.images:
                    if img.id:
                        await sync_to_async(ServiceImage.objects.filter(id=img.id).update)(
                            image=img.imageUrl, index=img.index, link=img.link)
                    else:
                        await sync_to_async(ServiceImage.objects.create)(
                            service=service, image=img.imageUrl, index=img.index, link=img.link)
            
            return await cls.getService(service)
        except: return False

    @classmethod
    async def deleteService(cls, service: Service):
        try:
            await sync_to_async(service.delete)()
            return True
        except: return False
