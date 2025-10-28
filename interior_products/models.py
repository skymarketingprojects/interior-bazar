from django.db import models
from app_ib.Utils.ModelHelper import indexShifting, applyDiscount
# Create your models here.

class Catelogue(models.Model):
    catelougeImage = models.URLField()
    business = models.ForeignKey('app_ib.Business', on_delete=models.CASCADE)
    catelougePdf = models.URLField()
    title = models.CharField(max_length=500)
    totalDownload = models.IntegerField(default=0)
    category = models.CharField(max_length=500)
    catelogueType = models.ForeignKey('app_ib.BusinessType', on_delete=models.PROTECT)
    # category = models.ForeignKey('app_ib.BusinessCategory', on_delete=models.CASCADE)
    createdAt = models.DateTimeField(auto_now_add=True)
    ytLink = models.URLField(null=True, blank=True)
    index = models.IntegerField(default=1)

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
# Service model

class Service(models.Model):
    business = models.ForeignKey('app_ib.Business', on_delete=models.CASCADE,related_name='services')
    title = models.CharField(max_length=500)
    index = models.IntegerField(default=1)
    orignalPrice = models.FloatField()
    discountType = models.CharField(max_length=50)
    displayPrice = models.FloatField()
    discountBy = models.FloatField()
    description = models.TextField()
    serviceTags = models.TextField()

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
        return f"Image {self.index} for ({self.product.title or 'Untitled'})"