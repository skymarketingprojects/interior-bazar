from asgiref.sync import sync_to_async
from interior_products.models import Product,ProductImage,Catelogue,ProductSpecification,ProductCategory,ProductSubCategory,ProductBulkTier
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business
import json
from app_ib.Utils.Names import NAMES

# ponytail: module-level sentinel — createProduct/updateProduct's bulkTiers block
# references `_missing` too. It used to be a local of _applyCommercialTerms only, so
# those methods raised NameError AFTER the row was saved; the bare except swallowed it
# and the controller reported "Unable to create product" on a successful create.
_missing = object()


def _applyCommercialTerms(product, data):
    """Copy the optional MOQ/unit terms off the request object onto `product`.

    Only keys the client actually SENT are touched — an absent key leaves the
    stored value alone (the seller form is the only writer, but other callers
    post partial payloads). Blank/0/garbage MOQ → None ("no minimum"), never a
    fabricated default.
    """
    moq = getattr(data, 'minOrderQty', _missing)
    if moq is not _missing:
        try:
            moq = int(moq)
            product.minOrderQty = moq if moq > 0 else None
        except (TypeError, ValueError):
            product.minOrderQty = None
    unit = getattr(data, 'unit', _missing)
    if unit is not _missing:
        product.unit = str(unit or '').strip()[:30]
    pricingModel = getattr(data, 'pricingModel', _missing)
    if pricingModel is not _missing:
        product.pricingModel = str(pricingModel or '').strip()[:30]
    stockStatus = getattr(data, 'stockStatus', _missing)
    if stockStatus is not _missing:
        product.stockStatus = str(stockStatus or '').strip()[:30]


class PRODUCTS_TASKS:

    @classmethod
    async def deleteProduct(self,product:Product):
        try:
            product.delete()
            return True
        except Exception as e:
            pass
            return False
    
    @classmethod
    async def updateProduct(self,product:Product,data:dict):
        try:
            catelouge = product.catelogue
            try:
               catelouge = await sync_to_async(Catelogue.objects.get(id=data.catalogueId))()
            except Exception as e:
                pass

            product.title = data.title
            product.orignalPrice = data.price
            product.discountType = data.discountType
            product.discountBy = data.discountBy
            product.description = data.description
            product.productTags = data.productTags
            product.catelogue = catelouge
            _applyCommercialTerms(product, data)

            categories = getattr(data, 'categories', None)
            if isinstance(categories, list) and len(categories) <= 3:
                category_ids = [c.id for c in categories]
                category_objs = await sync_to_async(lambda: list(ProductCategory.objects.filter(id__in=category_ids)))()
                if len(category_objs) == len(category_ids):
                    await sync_to_async(product.category.set)(category_objs)
            
            
            subCategories = getattr(data, 'subCategories', None)
            if isinstance(subCategories, list) and len(subCategories) <= 3:
                category_ids = [c.id for c in subCategories]
                category_objs = await sync_to_async(lambda: list(ProductSubCategory.objects.filter(id__in=category_ids)))()
                if len(category_objs) == len(category_ids):
                    await sync_to_async(product.subCategory.set)(category_objs)

            
            product.save()


            try:
                if data.images:
                    for image in data.images:
                        _imgId = getattr(image, 'id', None)
                        _imgUrl = getattr(image, 'imageUrl', '') or getattr(image, 'image', '')
                        _imgIdx = getattr(image, 'index', 0) or 0
                        _imgLink = getattr(image, 'link', '') or ''
                        if _imgId:
                            await sync_to_async(ProductImage.objects.filter(id=_imgId).update)(
                                image=_imgUrl, index=_imgIdx, link=_imgLink
                            )
                        else:
                            await sync_to_async(ProductImage.objects.create)(
                                product=product, image=_imgUrl, index=_imgIdx, link=_imgLink
                            )


            except Exception as e:
                pass
                pass


            # ── Bulk pricing tiers (additive; user-approved 2026-07-20) ──
            bulkTiers = getattr(data, 'bulkTiers', _missing)
            if bulkTiers is not _missing and isinstance(bulkTiers, list):
                await sync_to_async(product.bulkTiers.all().delete)()
                for i, tier in enumerate(bulkTiers):
                    min_qty = getattr(tier, 'minQty', None) or getattr(tier, 'min', None)
                    price = getattr(tier, 'price', None)
                    if min_qty is not None and price is not None:
                        await sync_to_async(ProductBulkTier.objects.create)(
                            product=product, minQty=int(min_qty), price=float(price), tierIndex=i
                        )

            # getattr defaults: the v3 seller edit form does not send these spec
            # fields. Direct data.sizeAvailabe access raised AttributeError AFTER the
            # row was already saved, so update reported "Unable to update product" on
            # success — same class as the create-path _missing bug.
            specifications = {
                "sizeAvailabe": getattr(data, "sizeAvailabe", None),
                "userManual": getattr(data, "userManual", None),
                "detail": getattr(data, "detail", None),
            }

            for key, value in specifications.items():
                if not value:
                    continue
                await self._create_or_update_spec(product, key, value)
            data = await self.getProduct(product)


            return data
        
        except Exception as e:
            pass
            return False
    
    @staticmethod
    async def _create_or_update_spec(product, title, description):
        try:
            await sync_to_async(ProductSpecification.objects.update_or_create)(
                product=product,
                title=title,
                description=description
            )
            return True
        except Exception as e:
            pass
            return False

    @classmethod
    async def createProduct(self,business:Business,data:dict):
        try:
            product = await sync_to_async(Product.objects.create)(
                business=business,
                title=data.title,
                orignalPrice=data.price,
                discountType=data.discountType,
                discountBy=data.discountBy,
                description=data.description,
                productTags=data.productTags,
            )
            _applyCommercialTerms(product, data)
            await sync_to_async(product.save)()

            category_ids = [cat.id for cat in getattr(data, 'categories', [])][:3]
            categories=[]
            if len(category_ids) <= 3:
                categories = await sync_to_async(lambda: list(ProductCategory.objects.filter(id__in=category_ids)))()
            

            subCategoryIds = [cat.id for cat in getattr(data, 'subCategories', [])][:3]
            subCategories=[]
            if len(subCategoryIds) <= 3:
                subCategories = await sync_to_async(lambda: list(ProductSubCategory.objects.filter(id__in=subCategoryIds)))()
            

            await sync_to_async(product.category.set)(categories)
            await sync_to_async(product.subCategory.set)(subCategories)

            try:
                if data.images:
                    for image in data.images:
                        await sync_to_async(ProductImage.objects.create)(
                            product=product,
                            image=getattr(image, 'imageUrl', '') or getattr(image, 'image', ''),
                            index=getattr(image, 'index', 0) or 0,
                            link=getattr(image, 'link', '') or ''
                        )
            except Exception as e:
                pass
                pass
            # ── Bulk pricing tiers (additive; user-approved 2026-07-20) ──
            bulkTiers = getattr(data, 'bulkTiers', _missing)
            if bulkTiers is not _missing and isinstance(bulkTiers, list):
                for i, tier in enumerate(bulkTiers):
                    min_qty = getattr(tier, 'minQty', None) or getattr(tier, 'min', None)
                    price = getattr(tier, 'price', None)
                    if min_qty is not None and price is not None:
                        await sync_to_async(ProductBulkTier.objects.create)(
                            product=product, minQty=int(min_qty), price=float(price), tierIndex=i
                        )
            # These spec fields are optional — the v3 dashboard create form does not
            # send them. Use getattr defaults so a missing key can't raise an
            # AttributeError AFTER the product is already saved (which made create
            # report "Unable to create product" on success — F3). Only persist a
            # spec row when the value is actually provided.
            specifications = {
                "sizeAvailabe": getattr(data, "sizeAvailabe", None),
                "userManual": getattr(data, "userManual", None),
                "detail": getattr(data, "detail", None),
            }
            for key,value in specifications.items():
                if not value:
                    continue
                await sync_to_async(ProductSpecification.objects.create)(
                    product=product,
                    title=key,
                    description=value
            )
            data = await self.getProduct(product)
            if not data:
                # The product IS saved; serialization just failed. Don't report a
                # false "Unable to create product" — return a minimal truthy payload
                # so the create is reported as the success it actually is (F-create).
                import traceback, sys
                print("createProduct: getProduct serialization returned falsy for product", product.id, file=sys.stderr)
                return {"id": product.id, "title": product.title}
            return data
        except Exception as e:
            import traceback, sys
            traceback.print_exc(file=sys.stderr)
            return False

    @classmethod
    async def getProduct(self,product:Product):
        try:
            productImages = await sync_to_async(product.productImages.all)()
            productImageData = []
            for image in productImages:
                productImageData.append({
                    'id':image.id,
                    'imageUrl':image.image,
                    'index':image.index,
                    'link':image.link
                })
            pass
            # productTags may be a JSON-list string (legacy) OR a plain
            # comma-separated string (what the v3 create form sends). json.loads
            # crashes on the latter and silently dropped the whole product from
            # every listing (F-tags). Parse defensively, falling back to a split.
            _raw = product.productTags
            if not _raw:
                tags = []
            else:
                try:
                    tags = json.loads(str(_raw).replace("'", '"'))
                except Exception:
                    tags = [t.strip() for t in str(_raw).split(",") if t.strip()]

            prodCategory=[]
            for cat in product.category.all():
                data = await self.getCategoriesDataTask(cat)
                prodCategory.append(data)

            prodSubCategory=[]

            for subCat in product.subCategory.all():
                data = await self.getCategoriesDataTask(subCat)
                prodSubCategory.append(data)

            # An owner may not have a UserProfile yet (signup does not create one).
            # The reverse O2O raises RelatedObjectDoesNotExist (an AttributeError
            # subclass) so getattr(...,None) safely yields None — without this guard
            # the whole product was silently dropped from every listing (F-prof).
            _owner = product.business.user if product.business else None
            _profile = getattr(_owner, 'user_profile', None)

            productData = {
                'id':product.id,
                'title':product.title,
                'originalPrice':product.orignalPrice,
                'price':product.orignalPrice,
                'discountType':product.discountType,
                'discountBy':product.discountBy,
                'description':product.description,
                'productTags':tags,
                'images':productImageData,
                'displayPrice':product.displayPrice,
                'catalogueId':product.catelogue.id if product.catelogue else '',
                'index':product.index,
                "categories":prodCategory,
                "subCategories":prodSubCategory,
                "minOrderQty":product.minOrderQty,
                "unit":product.unit or '',
                "pricingModel":product.pricingModel or '',
                "stockStatus":product.stockStatus or '',
                "phone": getattr(_profile, 'phone', '') if _profile else '',
                "countryCode": getattr(_profile, 'countryCode', '') if _profile else ''
            }
            # Bulk pricing tiers
            bulkTiers = await sync_to_async(list)(product.bulkTiers.all())
            productData["bulkTiers"] = [
                {'id': t.id, 'minQty': t.minQty, 'price': t.price, 'tierIndex': t.tierIndex}
                for t in bulkTiers
            ]
            specifications:list[ProductSpecification] = await sync_to_async(product.productSpecifications.all)()
            for specification in specifications:
                productData[specification.title] = specification.description
            return productData
        except Exception as e:
            import traceback, sys
            print("getProduct FAILED:", repr(e), file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return False

    @classmethod
    async def getProductCategoriesTask(self, kind="product"):
        try:
            # Products and services share this table but are SEPARATE taxonomies
            # (service rows are marked by the `svc-` value prefix), so a caller
            # must say which one it wants — a service must never be filed under
            # a product category like Furniture.
            categories = (ProductCategory.serviceOnes() if kind == "service"
                          else ProductCategory.productOnes())
            data = []
            for cat in categories:
                data.append({
                    "id":cat.id,
                    "label":cat.lable,
                    "value":cat.value,
                    'imageSQUrl':cat.imageSQUrl,
                    'imageRTUrl':cat.imageRTUrl
                })
            return data
        except Exception as e:
            pass
            return False
    
    @classmethod
    async def getProductSubCategoriesTask(self):
        try:
            categories = ProductSubCategory.objects.all()
            data = []
            for cat in categories:
                data.append({
                    NAMES.ID:cat.id,
                    NAMES.LABEL:cat.lable,
                    NAMES.VALUE:cat.value,
                    NAMES.SHORT_VALUE:cat.shortValue,
                    NAMES.IMAGE_SQ_URL:cat.imageSQUrl,
                    NAMES.IMAGE_RT_URL:cat.imageRTUrl,
                    NAMES.TRENDING:cat.trending
                })
            return data
        except Exception as e:
            pass
            return False
    
    @classmethod
    async def getCategoriesDataTask(self,catgories:ProductCategory):
        try:
            
            return {
                    NAMES.ID:catgories.id,
                    NAMES.LABEL:catgories.lable,
                    NAMES.VALUE:catgories.value,
                    NAMES.SHORT_VALUE:catgories.shortValue,
                    NAMES.IMAGE_SQ_URL:catgories.imageSQUrl,
                    NAMES.IMAGE_RT_URL:catgories.imageRTUrl,
                    NAMES.TRENDING:catgories.trending
                }
        except Exception as e:
            pass
            return False