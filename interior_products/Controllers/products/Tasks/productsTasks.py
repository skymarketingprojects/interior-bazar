from asgiref.sync import sync_to_async
from interior_products.models import Product, ProductImage, Catelogue, ProductSpecification, ProductCategory, ProductSubCategory
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business
import json
from app_ib.Utils.Names import NAMES

class PRODUCTS_TASKS:
    
    @classmethod
    async def deleteProduct(cls, product: Product):
        try:
            await sync_to_async(product.delete)()
            return True
        except Exception as e:
            return False
    
    @classmethod
    async def updateProduct(cls, product: Product, data: dict):
        try:
            catelouge = product.catelogue
            try:
                if hasattr(data, 'catalogueId') and data.catalogueId:
                    catelouge = await sync_to_async(Catelogue.objects.get)(id=data.catalogueId)
            except: pass

            product.title = data.title
            product.orignalPrice = data.price
            product.discountType = data.discountType
            product.discountBy = data.discountBy
            product.description = data.description
            product.productTags = data.productTags
            product.catelogue = catelouge

            categories = getattr(data, 'categories', None)
            if isinstance(categories, list) and len(categories) <= 3:
                category_ids = [c.id for c in categories]
                category_objs = await sync_to_async(lambda: list(ProductCategory.objects.filter(id__in=category_ids)))()
                if len(category_objs) == len(category_ids):
                    await sync_to_async(product.category.set)(category_objs)
            
            subCategories = getattr(data, 'subCategories', None)
            if isinstance(subCategories, list) and len(subCategories) <= 3:
                sub_ids = [c.id for c in subCategories]
                sub_objs = await sync_to_async(lambda: list(ProductSubCategory.objects.filter(id__in=sub_ids)))()
                if len(sub_objs) == len(sub_ids):
                    await sync_to_async(product.subCategory.set)(sub_objs)

            await sync_to_async(product.save)()

            try:
                if hasattr(data, 'images') and data.images:
                    for image in data.images:
                        if hasattr(image, 'id') and image.id:
                            await sync_to_async(ProductImage.objects.filter(id=image.id).update)(
                                image=image.imageUrl, index=image.index, link=image.link
                            )
                        else:
                            await sync_to_async(ProductImage.objects.create)(
                                product=product, image=image.imageUrl, index=image.index, link=image.link
                            )
            except: pass

            specifications = {"sizeAvailabe": getattr(data, 'sizeAvailabe', None), 
                              "userManual": getattr(data, 'userManual', None), 
                              "detail": getattr(data, 'detail', None)}

            for key, value in specifications.items():
                if value is not None:
                    await cls._create_or_update_spec(product, key, value)
            
            return await cls.getProduct(product)
        except Exception as e:
            return False
    
    @staticmethod
    async def _create_or_update_spec(product, title, description):
        try:
            await sync_to_async(ProductSpecification.objects.update_or_create)(
                product=product, title=title, defaults={'description': description}
            )
            return True
        except: return False

    @classmethod
    async def createProduct(cls, business: Business, data: dict):
        try:
            product = await sync_to_async(Product.objects.create)(
                business=business, title=data.title, orignalPrice=data.price,
                discountType=data.discountType, discountBy=data.discountBy,
                description=data.description, productTags=data.productTags,
            )

            category_ids = [cat.id for cat in getattr(data, 'categories', [])][:3]
            if category_ids:
                categories = await sync_to_async(lambda: list(ProductCategory.objects.filter(id__in=category_ids)))()
                await sync_to_async(product.category.set)(categories)
            
            sub_ids = [cat.id for cat in getattr(data, 'subCategories', [])][:3]
            if sub_ids:
                subs = await sync_to_async(lambda: list(ProductSubCategory.objects.filter(id__in=sub_ids)))()
                await sync_to_async(product.subCategory.set)(subs)

            try:
                if hasattr(data, 'images') and data.images:
                    for image in data.images:
                        await sync_to_async(ProductImage.objects.create)(
                            product=product, image=image.imageUrl, index=image.index, link=image.link
                        )
            except: pass

            specifications = {"sizeAvailabe": getattr(data, 'sizeAvailabe', ""), 
                              "userManual": getattr(data, 'userManual', ""), 
                              "detail": getattr(data, 'detail', "")}
            for key, value in specifications.items():
                await sync_to_async(ProductSpecification.objects.create)(
                    product=product, title=key, description=value
                )
            return await cls.getProduct(product)
        except: return False

    @classmethod
    async def BulkSerializeProducts(cls, product_list):
        """High-performance bulk serialization for products."""
        def run_sync_serialization():
            results = []
            for product in product_list:
                try:
                    image_data = [{
                        'id': img.id, 'imageUrl': img.image, 'index': img.index, 'link': img.link
                    } for img in product.productImages.all()]
                    
                    tags = json.loads(str(product.productTags).replace("'", '"')) if product.productTags else []
                    
                    prod_categories = [cls.getCategoriesDataSync(cat) for cat in product.category.all()]
                    prod_sub_categories = [cls.getCategoriesDataSync(sub) for sub in product.subCategory.all()]

                    profile = None
                    try: profile = product.business.user.user_profile
                    except: pass

                    product_data = {
                        'id': product.id,
                        'title': product.title,
                        'originalPrice': product.orignalPrice,
                        'price': product.orignalPrice,
                        'discountType': product.discountType,
                        'discountBy': product.discountBy,
                        'description': product.description,
                        'productTags': tags,
                        'images': image_data,
                        'displayPrice': product.displayPrice,
                        'catalogueId': product.catelogue.id if product.catelogue else '',
                        'index': product.index,
                        "categories": prod_categories,
                        "subCategories": prod_sub_categories,
                        "phone": profile.phone if profile else "",
                        "countryCode": profile.countryCode if profile else ""
                    }

                    for spec in product.productSpecifications.all():
                        product_data[spec.title] = spec.description
                    
                    results.append(product_data)
                except Exception as e:
                    pass
            return results
            
        return await sync_to_async(run_sync_serialization)()

    @classmethod
    async def getProduct(cls, product: Product):
        """Single product fetch using optimized patterns."""
        # Ensure relationships are loaded if possible
        optimized_list = await cls.BulkSerializeProducts([product])
        return optimized_list[0] if optimized_list else None

    @staticmethod
    def getCategoriesDataSync(cat):
        return {
            NAMES.ID: cat.id,
            NAMES.LABEL: cat.lable,
            NAMES.VALUE: cat.value,
            NAMES.SHORT_VALUE: getattr(cat, 'shortValue', ''),
            NAMES.IMAGE_SQ_URL: cat.imageSQUrl,
            NAMES.IMAGE_RT_URL: cat.imageRTUrl,
            NAMES.TRENDING: getattr(cat, 'trending', False)
        }

    @classmethod
    async def getProductCategoriesTask(cls):
        try:
            queryset = await sync_to_async(lambda: list(ProductCategory.objects.all()))()
            return [cls.getCategoriesDataSync(cat) for cat in queryset]
        except: return False
    
    @classmethod
    async def getProductSubCategoriesTask(cls):
        try:
            queryset = await sync_to_async(lambda: list(ProductSubCategory.objects.all()))()
            return [cls.getCategoriesDataSync(cat) for cat in queryset]
        except: return False
    
    @classmethod
    async def getCategoriesDataTask(cls, cat):
        return cls.getCategoriesDataSync(cat)