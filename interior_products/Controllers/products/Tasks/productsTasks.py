from asgiref.sync import sync_to_async
from interior_products.models import Product,ProductImage
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
            #await MY_METHODS.printStatus(f"Error in deleteProduct: {str(e)}")
            return False
    
    @classmethod
    async def updateProduct(self,product:Product,data:dict):
        try:
            product.title = data.title
            product.orignalPrice = data.price
            product.discountType = data.discountType
            product.discountBy = data.discountBy
            product.description = data.description
            product.productTags = data.productTags
            product.save()
            try:
                if data.images:
                    for image in data.images:
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
                #await MY_METHODS.printStatus(f"Error in updateProduct: {str(e)}")
                pass
            data = await self.getProduct(product)
            return data
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in updateProduct: {str(e)}")
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
                productTags=data.productTags
            )
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
                #await MY_METHODS.printStatus(f"Error in createProduct: {str(e)}")
                pass
            data = await self.getProduct(product)
            return data
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in createProduct: {str(e)}")
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
            #await MY_METHODS.printStatus(f"Product tag Data: {product.productTags} of type {type(product.productTags)}")
            tags = json.loads(str(product.productTags).replace("'",'"')) if product.productTags else []
            productData = {
                'id':product.id,
                'title':product.title,
                'orignalPrice':product.orignalPrice,
                'price':product.orignalPrice,
                'discountType':product.discountType,
                'discountBy':product.discountBy,
                'description':product.description,
                'productTags':tags,
                'images':productImageData,
                'displayPrice':product.displayPrice,
                'index':product.index
            }
            return productData
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in getProduct: {str(e)}")
            return False
