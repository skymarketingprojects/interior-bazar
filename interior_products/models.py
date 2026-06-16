from django.db import models
from app_ib.Utils.ModelHelper import indexShifting, applyDiscount
from django_quill.fields import QuillField
from django.utils.text import slugify


def _unique_slug(model_class, text, pk):
    """Generate a collision-free slug for an engine entity."""
    base = slugify(text or '') or model_class.__name__.lower()
    candidate, n = base, 1
    while model_class.objects.filter(slug=candidate).exclude(pk=pk).exists():
        n += 1
        candidate = f'{base}-{n}'
    return candidate
# Create your models here.
# Category
class ProductCategory(models.Model):
    value = models.CharField(max_length=250)
    lable = models.CharField(max_length=250)
    shortValue = models.CharField(max_length=250,null=True,blank=True)
    imageSQUrl = models.CharField(max_length=2250,null=True,blank=True)
    imageRTUrl = models.CharField(max_length=2250,null=True,blank=True)
    trending = models.BooleanField(default=False)
    index = models.IntegerField(default=0)
   
    def __str__(self):
        return f'product category - {self.lable}'
    
    def save(self, *args, **kwargs):
        if not self.index:
            self.index = self.__class__.objects.all().count()+1
        indexShifting(instance=self,filter_attr='index')
        super().save(*args, **kwargs)

class ProductSubCategory(models.Model):
    category = models.ForeignKey(ProductCategory,on_delete=models.CASCADE,related_name="prodsubcat")
    value = models.CharField(max_length=250)
    lable = models.CharField(max_length=250)
    shortValue = models.CharField(max_length=250,null=True,blank=True)
    imageSQUrl = models.CharField(max_length=2250,null=True,blank=True)
    imageRTUrl = models.CharField(max_length=2250,null=True,blank=True)
    trending = models.BooleanField(default=False)
    index = models.IntegerField(default=0)
   
    def __str__(self):
        return f'product sub category - {self.lable}'
    
    def save(self, *args, **kwargs):
        if not self.index:
            self.index = self.__class__.objects.all().count()+1
        indexShifting(instance=self,filter_attr='index')
        super().save(*args, **kwargs)

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
    updatedAt = models.DateTimeField(auto_now=True)

    # --- v2.1.0.0 engine fields (additive; totalDownload already exists above) ---
    slug = models.SlugField(max_length=255, null=True, blank=True, unique=True)
    viewCount = models.PositiveIntegerField(default=0)
    trendingScore = models.FloatField(default=0.0, db_index=True)
    hotScore = models.FloatField(default=0.0, db_index=True)
    isActive = models.BooleanField(default=True)
    label = models.CharField(max_length=50, blank=True, default='')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Catelogue, self.title, self.pk)
        indexShifting(instance=self,filter_attr='business')
        super(Catelogue, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

class CatelogueImage(models.Model):
    catelougeImage = models.URLField(max_length=2250)
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

    updatedAt = models.DateTimeField(auto_now=True)

    # --- v2.1.0.0 engine fields (additive; legacy productTags TextField kept) ---
    slug = models.SlugField(max_length=255, null=True, blank=True, unique=True)
    viewCount = models.PositiveIntegerField(default=0)
    trendingScore = models.FloatField(default=0.0, db_index=True)
    hotScore = models.FloatField(default=0.0, db_index=True)
    isActive = models.BooleanField(default=True)
    stockQuantity = models.IntegerField(null=True, blank=True)
    ratingValue = models.FloatField(default=0.0)
    totalReviews = models.PositiveIntegerField(default=0)
    ratingBreakdown = models.JSONField(default=dict, blank=True)
    label = models.CharField(max_length=50, blank=True, default='')
    tags = models.ManyToManyField('app_ib.Tag', blank=True, related_name='products')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.displayPrice = applyDiscount(self)
        if not self.slug:
            self.slug = _unique_slug(Product, self.title, self.pk)
        indexShifting(instance=self,filter_attr='business')
        super(Product, self).save(*args, **kwargs)
    
class ProductImage(models.Model):
    image = models.URLField(max_length=2250)
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
    updatedAt = models.DateTimeField(auto_now=True)

    # --- v2.1.0.0 engine fields (additive) ---
    slug = models.SlugField(max_length=255, null=True, blank=True, unique=True)
    viewCount = models.PositiveIntegerField(default=0)
    trendingScore = models.FloatField(default=0.0, db_index=True)
    hotScore = models.FloatField(default=0.0, db_index=True)
    isActive = models.BooleanField(default=True)
    stockQuantity = models.IntegerField(null=True, blank=True)
    # Services have no stock — only a bookable/not-bookable switch the owner flips.
    # Distinct from isActive (listed/unlisted on the marketplace): an unavailable
    # service stays visible on its detail page but is marked "Not available".
    isAvailable = models.BooleanField(
        default=True,
        help_text="Owner-controlled availability (accepting work right now). "
                  "NOT the same as isActive, which means listed/unlisted.")
    ratingValue = models.FloatField(default=0.0)
    totalReviews = models.PositiveIntegerField(default=0)
    ratingBreakdown = models.JSONField(default=dict, blank=True)
    label = models.CharField(max_length=50, blank=True, default='')
    serviceAreas = models.JSONField(default=list, blank=True)
    tags = models.ManyToManyField('app_ib.Tag', blank=True, related_name='services')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.displayPrice = applyDiscount(self)
        if not self.slug:
            self.slug = _unique_slug(Service, self.title, self.pk)
        indexShifting(instance=self,filter_attr='business')
        super(Service, self).save(*args, **kwargs)
    
class ServiceImage(models.Model):
    image = models.URLField(max_length=2250)
    service = models.ForeignKey(Service, on_delete=models.CASCADE,related_name='serviceImages')
    index = models.IntegerField(default=1)
    link = models.URLField(null=True, blank=True)

    def save(self, *args, **kwargs):
        indexShifting(instance=self,filter_attr='service')
        super(ServiceImage, self).save(*args, **kwargs)

    def __str__(self):
        return f"Image {self.index} for ({self.service.title or 'Untitled'})"
    
class InteriorServices(models.Model):
    value = models.CharField(max_length=250)
    lable = models.CharField(max_length=250)
    imageSQUrl = models.CharField(max_length=2250,null=True,blank=True)
    imageRTUrl = models.CharField(max_length=2250,null=True,blank=True)

    link= models.CharField(max_length=2250, null=True, blank=True)
    index= models.IntegerField(default=0)
   
    def __str__(self):
        return f'Interior Service - {self.lable}'
    def save(self, *args, **kwargs):
        if not self.index:
            self.index = self.__class__.objects.all().count()+1
        indexShifting(instance=self,filter_attr='index')
        super(InteriorServices, self).save(*args, **kwargs)