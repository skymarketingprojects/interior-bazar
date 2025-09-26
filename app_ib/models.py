import uuid
from django.db import models
from django_quill.fields import QuillField
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import uuid
from django.db import models,transaction
from .Utils.ModelHelper import indexShifting
from app_ib.Utils.MyMethods import MY_METHODS
# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username field must be set")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)  # securely hashes the password
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)
        
# Create your models here.
# Custom User Model
class CustomUser(AbstractBaseUser, PermissionsMixin):
    my_id = models.TextField()
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    username = models.CharField(max_length=500, unique=True)
    type = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Needed for Django admin
    is_delete = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)  # From AbstractBaseUser but can override

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'       # Login with username
    REQUIRED_FIELDS = []              # Extra required fields when creating superusers

    def __str__(self):
        return f'date: {self.timestamp} username: {self.username}'

class UserProfile(models.Model):
    user= models.OneToOneField(CustomUser,on_delete=models.CASCADE, null=True, blank=True,related_name='user_profile')
    name= models.CharField(max_length=250,default='',null=True, blank=True)
    phone= models.CharField(max_length=100,default='',null=True, blank=True)
    email= models.CharField(max_length=250,default='',null=True, blank=True)
    profile_image= models.FileField(null=True, blank=True, upload_to='user/profile_image')
    profile_image_url = models.TextField(default='',null=True, blank=True)
    timestamp= models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'profile - {self.user.pk}'
class BusinessBadge(models.Model):
    type = models.CharField(max_length=250)
    image_url = models.URLField(max_length=2250, null=True, blank=True)
    isDefault = models.BooleanField(default=False)

    def __str__(self):
        return f'badge - {self.type}'

class Business(models.Model):
    user= models.OneToOneField(CustomUser,on_delete=models.CASCADE, null=True, blank=True,related_name='user_business')
    business_name= models.CharField(max_length=250)
    whatsapp= models.CharField(max_length=100,default='',null=True, blank=True)
    cover_image_url = models.TextField(default='',null=True, blank=True)
    gst= models.CharField(max_length=250,null=True, blank=True)
    since= models.CharField(max_length=250,null=True, blank=True)
    segment= models.TextField() # "manufraturer"
    catigory= models.TextField() # ["interior", "exterior","office"]
    badge = models.TextField(null=True, blank=True)
    businessBadge= models.ForeignKey(BusinessBadge, on_delete=models.SET_NULL, null=True, blank=True)
    bio = models.TextField( null=True, blank=True)
    timestamp= models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'business name - {self.business_name} : pk: {self.pk}'

class BusinessProfile(models.Model):
    business= models.OneToOneField(Business,on_delete=models.CASCADE, null=True, blank=True,related_name='business_profile')
    primary_image= models.FileField(null=True, blank=True , upload_to='business/primary_image')
    secondary_images= models.FileField(null=True, blank=True, upload_to='business/secondary_images')
    primary_image_url = models.TextField(default='',null=True, blank=True)
    secondary_images_url = models.TextField(default='',null=True, blank=True)
    about= models.TextField()
    youtube_link= models.TextField()

    def __str__(self):
        return f'business profile - {self.business.pk}'
    
class Location(models.Model):
    user= models.OneToOneField(CustomUser,on_delete=models.CASCADE, null=True, blank=True)
    business= models.OneToOneField(Business,on_delete=models.CASCADE, null=True, blank=True, related_name='business_location')
    pin_code= models.CharField(max_length=500)
    city= models.CharField(max_length=500)
    state= models.CharField(max_length=500)
    country= models.CharField(max_length=500)
    location_link= models.TextField()
    timestamp= models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.business:
            return f'State: {self.state}  business location{self.business.pk}'
        elif self.user:
            return f'State: {self.state}  user location{self.user.pk}'
        return f'State: {self.state}'

class LeadQuery(models.Model):
    business= models.ForeignKey(Business,on_delete=models.CASCADE, null=True, blank=True,related_name='business_lead_query')
    user= models.ForeignKey(CustomUser,on_delete=models.CASCADE, null=True, blank=True,related_name='user_lead_query')
    name= models.CharField(max_length=500,default='',null=True,blank=True)
    phone= models.CharField(max_length=500,default='',null=True,blank=True)
    email= models.CharField(max_length=500,default='',null=True,blank=True)
    interested= models.TextField(default='',null=True,blank=True)
    query= models.TextField(default='',null=True,blank=True)
    city= models.CharField(max_length=500,default='',null=True,blank=True)
    state= models.CharField(max_length=500,default='',null=True,blank=True)
    country= models.CharField(max_length=500,default='',null=True,blank=True)
    status= models.TextField(default='',null=True,blank=True)
    tag= models.TextField(default='',null=True,blank=True)
    priority= models.TextField(default='',null=True,blank=True)
    remark= models.TextField(default='',null=True,blank=True)
    timestamp= models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'business_id {self.pk}  name: {self.name}  phone{self.phone} date {self.timestamp}'


class BusinessPlan(models.Model):
    business= models.ForeignKey(Business,on_delete=models.CASCADE, null=True, blank=True,related_name='business_plan')
    services= models.TextField()
    is_active= models.BooleanField(default=False)
    plan_summary= models.TextField()
    last_activate= models.DateTimeField(auto_now_add=True)
    expire_date= models.DateTimeField(auto_now_add=True)
    timestamp= models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'is_active:{self.is_active} expire_date:{self.expire_date}'
# Platform own Plan buy query
class PlanQuery(models.Model):
    user= models.ForeignKey(CustomUser,on_delete=models.CASCADE, null=True, blank=True)
    plan= models.CharField(max_length=500,default='')
    name= models.CharField(max_length=500,default='')
    email= models.CharField(max_length=500,default='')
    phone= models.CharField(max_length=500,default='')
    state= models.CharField(max_length=500,default='')
    country= models.CharField(max_length=500,default='')
    address= models.TextField(default='')
    transaction_id= models.CharField(max_length=500,default='')
    stage= models.CharField(max_length=500,default='') #{"1":"Lead","2":"Contacted","3":"Followed Up","4":"Closed"}
    attachment= models.FileField(null=True, blank=True, upload_to='lead_query/attachment')
    attachment_url = models.URLField(default='',null=True, blank=True)
    timestamp= models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f' ID {self.pk} phone:{self.phone} stage:{self.stage}'
        
# Plan Buy Quate related to service
class Quate(models.Model):
    leadType = models.CharField(max_length=500,default='')
    businessType = models.CharField(max_length=500,default='')
    budget= models.CharField(max_length=500,default='')
    name= models.CharField(max_length=500,default='')
    phoneNumber= models.CharField(max_length=500,default='')
    query= models.TextField(default='')
    email= models.CharField(max_length=500,default='')
    noOfEmp = models.CharField(max_length=500,default='')
    companyName = models.CharField(max_length=500,default='')
    note= models.CharField(max_length=500,default='')
    stage= models.CharField(max_length=500,default='') #{"1":"Lead","2":"Contacted","3":"Followed Up","4":"Closed"} Admin
    city= models.CharField(max_length=500,default='')
    state= models.CharField(max_length=500,default='')
    timestamp= models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.phoneNumber and not self.stage:
            return f'ID {self.pk} phone:{self.phoneNumber}'
        elif self.phoneNumber and self.stage:
            return f'ID {self.pk} phone:{self.phone} stage:{self.stage}'
        return f'ID {self.pk}'
    
    class Meta:
        verbose_name = "Leads for company"
        verbose_name_plural = "Platform Own Leads"


class Feedback(models.Model):
    user= models.ForeignKey(CustomUser,on_delete=models.CASCADE, null=True, blank=True)
    contact= models.CharField(max_length=500) # lable : Contact detail 
    feedback= models.TextField() # lable : Feedback rating
    status= models.TextField() # lable : [view,]
    timestamp= models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'pk:{self.pk}  feedback:{self.feedback}'


class Subscription(models.Model):
    type= models.CharField(max_length=800,null=True, blank=True) #listing or #Filter
    title= models.CharField(max_length=800,null=True, blank=True) 
    subtitle= models.CharField(max_length=800,null=True, blank=True) 
    services= models.TextField()
    duration= models.CharField(max_length=800,null=True, blank=True) 
    tag= models.CharField(max_length=800,null=True, blank=True) 
    amount= models.CharField(max_length=800,null=True, blank=True) 
    discount_percentage= models.CharField(max_length=800,null=True, blank=True) 
    discount_amount= models.CharField(max_length=800,null=True, blank=True) 
    payable_amount= models.CharField(max_length=800,null=True, blank=True) 

    cover_image= models.FileField(null=True, blank=True, upload_to='subscription/attachment')
    fallback_image_url= models.URLField(max_length=2250, null=True, blank=True) 
    video= models.FileField(null=True, blank=True, upload_to='subscription/video')
    video_url= models.URLField(max_length=2250, null=True, blank=True)
    plan_pdf= models.FileField(null=True, blank=True, upload_to='subscription/pdf')
    plan_pdf_url= models.URLField(max_length=2250, null=True, blank=True)

    is_active= models.BooleanField(default=False)
    timestamp= models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'ID:{self.id} rating:{self.title}'

class Blog(models.Model):
    user= models.ForeignKey(CustomUser,on_delete=models.CASCADE, null=True, blank=True)
    title= models.TextField() 
    slug = models.CharField(max_length=800, unique=True, null=True, blank=True)
    cover= models.FileField(null=True, blank=True,upload_to='blog/cover')
    cover_image_url = models.TextField(default='',null=True, blank=True)
    description=QuillField(null=True, blank=True)
    author= models.TextField()
    timestamp= models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'author {self.author} title:{self.title} timestamp:{self.timestamp}'
    
    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = MY_METHODS.generate_slug(self.title)
        super().save(*args, **kwargs)

class Contact(models.Model):
    tag= models.TextField()
    name= models.CharField(max_length=800,null=True, blank=True) 
    phone= models.CharField(max_length=800,null=True, blank=True) 
    mail= models.CharField(max_length=800,null=True, blank=True) 
    company= models.CharField(max_length=800,null=True, blank=True) 
    recognisation= models.CharField(max_length=800,null=True, blank=True) 
    detail= models.TextField()
    attachment= models.FileField(null=True, blank=True,upload_to='contact/attachment')
    timestamp= models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'ID {self.pk} tag {self.tag}'

class Constants(models.Model):
    segments= models.TextField() # {'manu':Manugraturer, 'retailer':Retailer}
    catigory= models.TextField() # {'manu':[furniture,lighting,decor,flooring,wall_coverings,window_treatments,home_textiles,kitchen_cabinets], 'retailer':[bathroom_fixtures,toilets,faucets,sinks,showers,bathtubs,bathroom_accessories,water_systems]}
    payment_detail = models.TextField()
    payment_qr = models.FileField(null=True, blank=True ,upload_to='payment_qr')
    def __str__(self):
        return f' pk {self.pk} segments:{self.segments}'

class Banners(models.Model):
    support_text = models.TextField()
    title = models.TextField()
    banner = models.FileField(null=True, blank=True ,upload_to='banners')
    is_active = models.BooleanField(default=False)
    def __str__(self):
        return f' pk {self.pk} title:{self.title}'

class OfferHeading(models.Model):
    title = models.TextField()
    is_active = models.BooleanField(default=False)
    def __str__(self):
        return f' pk {self.pk} title:{self.title}'


class Pages(models.Model):
    page_name = models.CharField(max_length=500, unique=True)
    title = models.CharField(max_length=500)
    content = QuillField(null=True, blank=True)
    def __str__(self):
        return f'page_name: {self.page_name} title:{self.title}'
    class Meta:
        verbose_name_plural = "information pages"
    
class QNA(models.Model):
    question = models.TextField()
    answer = models.TextField()
    is_active = models.BooleanField(default=False)
    def __str__(self):
        return f' pk {self.pk} question:{self.question}'
    


# Create your models here.
class Page(models.Model):
    name = models.CharField(max_length=255)


    def __str__(self):
        return f"Page {self.name}"
    class Meta:
        verbose_name_plural = "stockimages page"
    
class Section(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"Section {self.name}"

class StockMedia(models.Model):
    image = models.URLField(max_length=2250, null=True, blank=True)
    video = models.URLField(max_length=2250, null=True, blank=True)
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)
    index = models.IntegerField(default=1)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            indexShifting(self)
            super().save(*args, **kwargs)

#offer text
class OfferText(models.Model):
    text = models.TextField()
    link = models.URLField(max_length=2250, null=True, blank=True)
    show = models.BooleanField(default=False)
    def __str__(self):
        return f' pk {self.pk} text:{self.text}'