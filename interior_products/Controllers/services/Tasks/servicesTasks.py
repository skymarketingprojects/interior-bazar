from asgiref.sync import sync_to_async
from interior_products.models import Service,ServiceImage,ServiceFAQ,ProductSubCategory,ProductCategory
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business
import json
from interior_products.Controllers.products.Tasks.productsTasks import PRODUCTS_TASKS


def _clean_turnaround(data):
    """Seller-stated turnaround in days, or None when not stated.

    The form posts a string; '' / null / junk all mean "not stated" — never a
    fabricated number (P3-26). Kept lenient rather than validated hard because
    the whole service payload is an attribute bag (json_to_object), not a schema.
    """
    value = getattr(data, 'turnaroundDays', None)
    try:
        days = int(value)
    except (TypeError, ValueError):
        return None
    return days if days >= 0 else None


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
            service.turnaroundDays = _clean_turnaround(data)

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
                serviceTags=data.serviceTags,
                turnaroundDays=_clean_turnaround(data)
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

            faqs = await sync_to_async(
                lambda: list(service.faqs.order_by('displayOrder').values('question', 'answer'))
            )()
            # Owner may not have a UserProfile (signup doesn't create one) — same
            # guard as products' getProduct (F-prof), else the reverse O2O raises
            # and the whole service is reported as failed/dropped.
            _owner = service.business.user if service.business else None
            _profile = getattr(_owner, 'user_profile', None)

            # Provider credentials for the detail chip row (task 88). Same Award model
            # the shop/architect/business detail payloads already use: kind='credential'
            # are plain chips, kind='award' render as "<title> <year>". Both are the
            # provider's, since a service has no credentials of its own.
            from app_ib.engine_models import Award
            def _cred_chips(business):
                if not business:
                    return []
                rows = Award.objects.filter(
                    business=business, isActive=True
                ).order_by('index', '-timestamp')
                out = []
                for a in rows:
                    if a.kind == 'credential':
                        out.append(a.title)
                    elif a.kind == 'award':
                        out.append(f"{a.title} {a.year}".strip())
                return out
            credentials = await sync_to_async(_cred_chips)(service.business)

            # Provider identity for the detail provider CARD (task 90) — the payload
            # carried only the name, so the card had no avatar, type, city or
            # response time to render. Mirrors _biz_full_dict's derivation.
            def _provider(business):
                if not business:
                    return {}
                bt = business.businessType
                loc = getattr(business, 'business_location', None)
                return {
                    "businessSlug": business.slug or "",
                    "businessType": bt.lable if bt else "",
                    "businessCity": loc.city if loc else "",
                    "businessLogo": business.coverImageUrl or "",
                    "businessResponseSeconds": business.avgResponseSeconds,
                    # Drives the "IB Verified" attribute chip (P8-22).
                    "businessIsVerified": business.isVerified,
                }
            provider = await sync_to_async(_provider)(service.business)
            serviceData = {
                'id':service.id,
                'title':service.title,
                'originalPrice':service.orignalPrice,
                'price':service.orignalPrice,
                'discountType':service.discountType,
                'discountBy':service.discountBy,
                'description':service.description,
                'serviceTags':tags,
                # Seller-stated turnaround; None = not stated (the form's input
                # renders empty, the card's pill hides).
                'turnaroundDays':service.turnaroundDays,
                'images':serviceImageData,
                'displayPrice':service.displayPrice,
                'index':service.index,
                "categories":prodCategory,
                "subCategories":prodSubCategory,
                "faqs":faqs,
                # Owning business so the service-detail page can show the provider
                # ("By <business>") and link back to it. See ISSUE-004.
                "businessId":service.business.id,
                "businessName":service.business.businessName,
                "phone": getattr(_profile, 'phone', '') if _profile else '',
                "countryCode": getattr(_profile, 'countryCode', '') if _profile else '',
                # Engine label ("Most booked" etc.) — drives the badge on the detail
                # hero. Empty for every seeded service today, so the badge renders
                # nothing until an admin sets one.
                "label": service.label or "",
                # Provider credential chips (task 88); [] → the row hides.
                "credentials": credentials,
                # Provider identity for the provider card (task 90).
                **provider
            }
            return serviceData
        except Exception as e:
            pass
            return False
