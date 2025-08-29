import uuid
from django.db import models
from django_quill.fields import QuillField
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import uuid

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
    user= models.ForeignKey(CustomUser,on_delete=models.CASCADE, null=True, blank=True)
    name= models.CharField(max_length=250,default='',null=True, blank=True)
    phone= models.CharField(max_length=100,default='',null=True, blank=True)
    email= models.CharField(max_length=250,default='',null=True, blank=True)
    profile_image= models.FileField(null=True, blank=True, upload_to='user/profile_image')
    timestamp= models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'profile{self.user.pk}'

class Business(models.Model):
    user= models.ForeignKey(CustomUser,on_delete=models.CASCADE, null=True, blank=True)
    business_name= models.CharField(max_length=250)
    whatsapp= models.CharField(max_length=100,default='',null=True, blank=True)
    gst= models.CharField(max_length=250)
    since= models.CharField(max_length=250)
    segment= models.TextField() # "manufraturer"
    catigory= models.TextField() # ["interior", "exterior","office"]
    badge= models.TextField()
    timestamp= models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'business name{self.business_name} : pk: {self.pk}'

class BusinessProfile(models.Model):
    business= models.ForeignKey(Business,on_delete=models.CASCADE, null=True, blank=True)
    primary_image= models.FileField(null=True, blank=True , upload_to='business/primary_image')
    secondary_images= models.FileField(null=True, blank=True, upload_to='business/secondary_images')
    about= models.TextField()
    youtube_link= models.TextField()

    def __str__(self):
        return f'business profile{self.business.pk}'
    
class Location(models.Model):
    user= models.ForeignKey(CustomUser,on_delete=models.CASCADE, null=True, blank=True)
    business= models.ForeignKey(Business,on_delete=models.CASCADE, null=True, blank=True)
    pin_code= models.CharField(max_length=500)
    city= models.CharField(max_length=500)
    state= models.CharField(max_length=500)
    country= models.CharField(max_length=500)
    location_link= models.TextField()
    timestamp= models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'State: {self.state}  business location{self.business.pk}'

class LeadQuery(models.Model):
    business= models.ForeignKey(Business,on_delete=models.CASCADE, null=True, blank=True)
    user= models.ForeignKey(CustomUser,on_delete=models.CASCADE, null=True, blank=True)
    name= models.CharField(max_length=500,default='')
    phone= models.CharField(max_length=500,default='')
    email= models.CharField(max_length=500,default='')
    interested= models.TextField(default='')
    query= models.TextField(default='')
    city= models.CharField(max_length=500,default='')
    state= models.CharField(max_length=500,default='')
    country= models.CharField(max_length=500,default='')
    status= models.TextField(default='')
    tag= models.TextField(default='')
    priority= models.TextField(default='')
    remark= models.TextField(default='',null=True,blank=True)
    timestamp= models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'business_id {self.pk}  name: {self.name}  phone{self.phone} date {self.timestamp}'


class BusinessPlan(models.Model):
    business= models.ForeignKey(Business,on_delete=models.CASCADE, null=True, blank=True)
    services= models.TextField()
    is_active= models.BooleanField(default=False)
    plan_summary= models.TextField()
    last_activate= models.DateTimeField(auto_now_add=True)
    expire_date= models.DateTimeField(auto_now_add=True)
    timestamp= models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'is_active:{self.is_active} expire_date:{self.expire_date}'


    def __str__(self):
        return f'phone:{self.phone} query:{self.query}'

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
    timestamp= models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f' ID {self.pk} phone:{self.phone} stage:{self.stage}'
        
# Plan Buy Quate related to service
class Quate(models.Model):
    name= models.CharField(max_length=500,default='')
    phone= models.CharField(max_length=500,default='')
    interested= models.CharField(max_length=500,default='')
    email= models.CharField(max_length=500,default='')
    note= models.CharField(max_length=500,default='')
    stage= models.CharField(max_length=500,default='') #{"1":"Lead","2":"Contacted","3":"Followed Up","4":"Closed"} Admin
    timestamp= models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'ID {self.pk} phone:{self.phone} stage:{self.stage}'


class Feedback(models.Model):
    user= models.ForeignKey(CustomUser,on_delete=models.CASCADE, null=True, blank=True)
    contact= models.CharField(max_length=500) # lable : Contact detail 
    feedback= models.TextField() # lable : Feedback rating
    status= models.TextField() # lable : [view,]
    timestamp= models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'pk:{self.pk}  feedback:{self.feedback}'


class Subscription(models.Model):
    type= models.CharField(max_length=800,null=True, blank=True) #listing or #Filter
    title= models.CharField(max_length=800,null=True, blank=True) 
    subtitle= models.CharField(max_length=800,null=True, blank=True) 
    services= models.TextField()
    cover_image= models.FileField(null=True, blank=True, upload_to='subscription/attachment')
    video= models.FileField(null=True, blank=True, upload_to='subscription/video')
    duration= models.CharField(max_length=800,null=True, blank=True) 
    tag= models.CharField(max_length=800,null=True, blank=True) 
    amount= models.CharField(max_length=800,null=True, blank=True) 
    discount_percentage= models.CharField(max_length=800,null=True, blank=True) 
    discount_amount= models.CharField(max_length=800,null=True, blank=True) 
    payable_amount= models.CharField(max_length=800,null=True, blank=True) 
    plan_pdf= models.FileField(null=True, blank=True, upload_to='subscription/pdf')
    is_active= models.BooleanField(default=False)
    timestamp= models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f'ID:{self.id} rating:{self.title}'

class Blog(models.Model):
    user= models.ForeignKey(CustomUser,on_delete=models.CASCADE, null=True, blank=True)
    title= models.TextField() 
    cover= models.FileField(null=True, blank=True,upload_to='blog/cover')
    description=QuillField(null=True, blank=True)
    author= models.TextField()
    timestamp= models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'author {self.author} title:{self.title} timestamp:{self.timestamp}'

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
    
class QNA(models.Model):
    question = models.TextField()
    answer = models.TextField()
    is_active = models.BooleanField(default=False)
    def __str__(self):
        return f' pk {self.pk} question:{self.question}'