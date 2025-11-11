from django.db import models
from app_ib.Utils.ModelHelper import indexShifting, applyDiscount
from django_quill.fields import QuillField 
# Create your models here.
# Category
class ProductCategory(models.Model):
    value = models.CharField(max_length=250)
    lable = models.CharField(max_length=250)
    def __str__(self):
        return f'product category - {self.lable}'

class ProductSubCategory(models.Model):
    category = models.ForeignKey(ProductCategory,on_delete=models.CASCADE,related_name="prodsubcat")
    value = models.CharField(max_length=250)
    lable = models.CharField(max_length=250)
    def __str__(self):
        return f'product sub category - {self.lable}'

#catelog
class Catelogue(models.Model):
    catelougeImage = models.URLField()
    business = models.ForeignKey('app_ib.Business', on_delete=models.CASCADE,related_name='catelogues')
    catelougePdf = models.URLField()
    title = models.CharField(max_length=500)
    totalDownload = models.IntegerField(default=0)
    category = models.CharField(max_length=500,null=True,blank=True)
    catelogueType = models.ForeignKey('app_ib.BusinessType', on_delete=models.PROTECT)
    # category = models.ForeignKey('app_ib.BusinessCategory', on_delete=models.CASCADE)
    createdAt = models.DateTimeField(auto_now_add=True)
    ytLink = models.URLField(null=True, blank=True)
    index = models.IntegerField(default=1)

    catalogCategory = models.ManyToManyField(ProductCategory,related_name='catCatelogues')
    subCategory = models.ManyToManyField(ProductSubCategory,related_name='catSubCatelogues')

    def save(self, *args, **kwargs):
        indexShifting(instance=self,filter_attr='business')
        super(Catelogue, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

class CatelogueImage(models.Model):
    catelougeImage = models.URLField()
    catelouge = models.ForeignKey(Catelogue, on_delete=models.CASCADE,related_name='catelogueImages')
    index = models.IntegerField(default=1)
    link = models.URLField(null=True, blank=True)

    def save(self, *args, **kwargs):
        indexShifting(instance=self,filter_attr='catelouge')
        super(CatelogueImage, self).save(*args, **kwargs)

    def __str__(self):
        return f"Image {self.index} for ({self.catelouge.title or 'Untitled'})"




# Product model
class Product(models.Model):
    business = models.ForeignKey('app_ib.Business', on_delete=models.CASCADE,related_name='products')
    title = models.CharField(max_length=500)
    index = models.IntegerField(default=1)

    orignalPrice = models.FloatField()
    discountType = models.CharField(max_length=50)
    displayPrice = models.FloatField()
    discountBy = models.FloatField()
    
    description = models.TextField()
    productTags = models.TextField()
    catelogue = models.OneToOneField(Catelogue, on_delete=models.SET_NULL, null=True, blank=True, related_name='product')

    category = models.ManyToManyField(ProductCategory,related_name='catProducts')
    subCategory = models.ManyToManyField(ProductSubCategory,related_name='subcatProducts')

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        self.displayPrice = applyDiscount(self)
        indexShifting(instance=self,filter_attr='business')
        super(Product, self).save(*args, **kwargs)
    
class ProductImage(models.Model):
    image = models.URLField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE,related_name='productImages')
    index = models.IntegerField(default=1)
    link = models.URLField(null=True, blank=True)

    def save(self, *args, **kwargs):
        indexShifting(instance=self,filter_attr='product')
        super(ProductImage, self).save(*args, **kwargs)

    def __str__(self):
        return f"Image {self.index} for ({self.product.title or 'Untitled'})"
class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,related_name='productSpecifications')
    title = models.CharField(max_length=500)
    description = models.TextField(null=True, blank=True)


    def __str__(self):
        return self.title

# Service model

class Service(models.Model):
    business = models.ForeignKey('app_ib.Business', on_delete=models.CASCADE,related_name='services')
    title = models.CharField(max_length=500)
    
    orignalPrice = models.FloatField()
    discountType = models.CharField(max_length=50)
    displayPrice = models.FloatField()
    discountBy = models.FloatField()

    description = models.TextField()
    serviceTags = models.TextField()

    category = models.ManyToManyField(ProductCategory,related_name='catServices')
    subCategory = models.ManyToManyField(ProductSubCategory,related_name='subcatServices')
    
    index = models.IntegerField(default=1)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        self.displayPrice = applyDiscount(self)
        indexShifting(instance=self,filter_attr='business')
        super(Service, self).save(*args, **kwargs)
    
class ServiceImage(models.Model):
    image = models.URLField()
    service = models.ForeignKey(Service, on_delete=models.CASCADE,related_name='serviceImages')
    index = models.IntegerField(default=1)
    link = models.URLField(null=True, blank=True)

    def save(self, *args, **kwargs):
        indexShifting(instance=self,filter_attr='service')
        super(ServiceImage, self).save(*args, **kwargs)

    def __str__(self):
        return f"Image {self.index} for ({self.service.title or 'Untitled'})"