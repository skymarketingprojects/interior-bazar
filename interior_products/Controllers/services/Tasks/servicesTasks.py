from asgiref.sync import sync_to_async
from interior_products.models import Service,ServiceImage,ProductSubCategory,ProductCategory
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business
import json
from interior_products.Controllers.products.Tasks.productsTasks import PRODUCTS_TASKS

class SERVICES_TASKS:
    @classmethod
    async def deleteService(self,service:Service):
        try:
            service.delete()
            return True
        except Exception as e:
            pass
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

            categories = getattr(data, 'categories', None)
            if isinstance(categories, list) and len(categories) <= 3:
                category_ids = [c.id for c in categories]
                category_objs = await sync_to_async(lambda: list(ProductCategory.objects.filter(id__in=category_ids)))()
                if len(category_objs) == len(category_ids):
                    await sync_to_async(service.category.set)(category_objs)
            
            
            subCategories = getattr(data, 'subCategories', None)
            if isinstance(subCategories, list) and len(subCategories) <= 3:
                category_ids = [c.id for c in subCategories]
                category_objs = await sync_to_async(lambda: list(ProductSubCategory.objects.filter(id__in=category_ids)))()
                if len(category_objs) == len(category_ids):
                    await sync_to_async(service.subCategory.set)(category_objs)

            service.save()
            try:
                if data.images:
                    for image in data.images:
                        _imgId = getattr(image, 'id', None)
                        _imgUrl = getattr(image, 'imageUrl', '') or getattr(image, 'image', '')
                        _imgIdx = getattr(image, 'index', 0) or 0
                        _imgLink = getattr(image, 'link', '') or ''
                        if _imgId:
                            await sync_to_async(ServiceImage.objects.filter(id=_imgId).update)(
                                image=_imgUrl, index=_imgIdx, link=_imgLink
                            )
                        else:
                            await sync_to_async(ServiceImage.objects.create)(
                                service=service, image=_imgUrl, index=_imgIdx, link=_imgLink
                            )
            except Exception as e:
                pass
                pass
            data = await self.getService(service)
            return data
        except Exception as e:
            pass
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
            
            await sync_to_async(service.category.set)(categories)
            await sync_to_async(service.subCategory.set)(subCategories)
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
                pass
                pass
            data = await self.getService(service)
            return data
        except Exception as e:
            pass
            return False
        
    @classmethod
    async def getService(self,service:Service):
        try:
            serviceImages: list[ServiceImage] = await sync_to_async(service.serviceImages.all)()
            serviceImageData = []
            for image in serviceImages:
                serviceImageData.append({
                    'id':image.id,
                    'imageUrl':image.image,
                    'index':image.index,
                    'link':image.link
                })
            _raw = service.serviceTags
            if not _raw:
                tags = []
            else:
                try:
                    tags = json.loads(str(_raw).replace("'", '"'))
                except Exception:
                    tags = [t.strip() for t in str(_raw).split(",") if t.strip()]
            prodCategory=[]
            for cat in service.category.all():
                data = await PRODUCTS_TASKS.getCategoriesDataTask(cat)
                prodCategory.append(data)

            prodSubCategory=[]

            for subCat in service.subCategory.all():
                data = await PRODUCTS_TASKS.getCategoriesDataTask(subCat)
                prodSubCategory.append(data)
            serviceData = {
                'id':service.id,
                'title':service.title,
                'originalPrice':service.orignalPrice,
                'price':service.orignalPrice,
                'discountType':service.discountType,
                'discountBy':service.discountBy,
                'description':service.description,
                'serviceTags':tags,
                'images':serviceImageData,
                'displayPrice':service.displayPrice,
                'index':service.index,
                "categories":prodCategory,
                "subCategories":prodSubCategory,
                # Owning business so the service-detail page can show the provider
                # ("By <business>") and link back to it. See ISSUE-004.
                "businessId":service.business.id,
                "businessName":service.business.businessName,
                "phone":service.business.user.user_profile.phone,
                "countryCode":service.business.user.user_profile.countryCode
            }
            return serviceData
        except Exception as e:
            pass
            return False
