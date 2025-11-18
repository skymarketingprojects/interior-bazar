from asgiref.sync import sync_to_async
from interior_products.models import Product,ProductImage,Catelogue,ProductSpecification,ProductCategory,ProductSubCategory
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business
import json

class PRODUCTS_TASKS:
    
    @classmethod
    async def deleteProduct(self,product:Product):
        try:
            product.delete()
            return True
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in deleteProduct: {str(e)}")
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
                        # await MY_METHODS.printStatus(f"updateProduct: {image['id']}")
                        if image.id:
                            await sync_to_async(ProductImage.objects.filter(id=image.id).update)(
                                image=image.imageUrl,
                                index=image.index,
                                link=image.link
                            )
                        else:
                            await sync_to_async(ProductImage.objects.create)(
                                product=product,
                                image=image.imageUrl,
                                index=image.index,
                                link=image.link
                            )


            except Exception as e:
                # await MY_METHODS.printStatus(f"Error in updateProduct: {str(e)}")
                pass


            specifications = {"sizeAvailabe":data.sizeAvailabe,"userManual":data.userManual,"detail":data.detail}
            # await MY_METHODS.printStatus(f"updateProduct: {specifications}")


            for key, value in specifications.items():
                if not value:
                    continue
                await self._create_or_update_spec(product, key, value)
            data = await self.getProduct(product)


            return data
        
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in updateProduct: {str(e)}")
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
            # await MY_METHODS.printStatus(f"Error in _create_or_update_spec: {str(e)}")
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
            

            await sync_to_async(product.category.set)(categories)
            await sync_to_async(product.subCategory.set)(subCategories)

            try:
                if data.images:
                    for image in data.images:
                        await sync_to_async(ProductImage.objects.create)(
                            product=product,
                            image=image.imageUrl,
                            index=image.index,
                            link=image.link
                        )
            except Exception as e:
                # await MY_METHODS.printStatus(f"Error in createProduct: {str(e)}")
                pass
            specifications = {"sizeAvailabe":data.sizeAvailabe,"userManual":data.userManual,"detail":data.detail}
            for key,value in specifications.items():
                await sync_to_async(ProductSpecification.objects.create)(
                    product=product,
                    title=key,
                    description=value
            )
            data = await self.getProduct(product)
            return data
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in createProduct: {str(e)}")
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
            # await MY_METHODS.printStatus(f"Product tag Data: {product.productTags} of type {type(product.productTags)}")
            tags = json.loads(str(product.productTags).replace("'",'"')) if product.productTags else []

            prodCategory=[]
            for cat in product.category.all():
                data = await self.getCategoriesDataTask(cat)
                prodCategory.append(data)

            prodSubCategory=[]

            for subCat in product.subCategory.all():
                data = await self.getCategoriesDataTask(subCat)
                prodSubCategory.append(data)

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
                "subCategories":prodSubCategory
            }
            specifications:list[ProductSpecification] = await sync_to_async(product.productSpecifications.all)()
            for specification in specifications:
                productData[specification.title] = specification.description
            return productData
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in getProduct: {str(e)}")
            return False

    @classmethod
    async def getProductCategoriesTask(self):
        try:
            categories = ProductCategory.objects.all()
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
            # await MY_METHODS.printStatus(f"error in get product category {str(e)}")
            return False
    
    @classmethod
    async def getProductSubCategoriesTask(self):
        try:
            categories = ProductSubCategory.objects.all()
            data = []
            for cat in categories:
                data.append({
                    "id":cat.id,
                    "label":cat.lable,
                    "value":cat.value
                })
            return data
        except Exception as e:
            # await MY_METHODS.printStatus(f"error in get product category {str(e)}")
            return False
    
    @classmethod
    async def getCategoriesDataTask(self,catgories:ProductCategory):
        try:
            
            return {
                    "id":catgories.id,
                    "label":catgories.lable,
                    "value":catgories.value
                }
        except Exception as e:
            await MY_METHODS.printStatus(f"error in get product category {str(e)}")
            return False