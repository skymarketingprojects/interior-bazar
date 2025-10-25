from django.db import models

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