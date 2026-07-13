"""interior_leads/models.py — the marketplace lead/intake domain.

Moved out of app_ib (TASK 15, state-only move — db_table names pinned so the
tables are untouched). Business/CustomUser FKs stay cross-app string refs to
app_ib (until TASK 18); Product/Service/Catelogue stay cross-app refs to
interior_products. LeadQuery still emits interior_notification.business_changed
from its save() — the signal wiring travels with the model.
"""
from datetime import datetime

from django.conf import settings
from django.db import models

from app_ib.Utils.Names import NAMES
from interior_notification.signals import business_changed

USER = settings.AUTH_USER_MODEL


class LeadQuery(models.Model):
    business= models.ForeignKey('interior_business.Business',on_delete=models.CASCADE, null=True, blank=True,related_name='business_lead_query')
    user= models.ForeignKey('app_ib.CustomUser',on_delete=models.CASCADE, null=True, blank=True,related_name='user_lead_query')
    name= models.CharField(max_length=500,default='',null=True,blank=True)
    phone= models.CharField(max_length=500,default='',null=True,blank=True)
    email= models.CharField(max_length=500,default='',null=True,blank=True)
    interested= models.TextField(default='',null=True,blank=True)
    query= models.TextField(default='',null=True,blank=True)
    city= models.CharField(max_length=500,default='',null=True,blank=True)
    state= models.CharField(max_length=500,default='',null=True,blank=True)
    country= models.CharField(max_length=500,default='',null=True,blank=True)
    category=models.CharField(max_length=500,default='',null=True,blank=True)
    status= models.TextField(default='',null=True,blank=True)
    leadStatus= models.TextField(default='',null=True,blank=True)
    stage= models.TextField(default='',null=True,blank=True)
    tag= models.TextField(default='',null=True,blank=True)
    priority= models.TextField(default='',null=True,blank=True)
    remark= models.TextField(default='',null=True,blank=True)

    product= models.ForeignKey('interior_products.Product', on_delete=models.SET_NULL, null=True, blank=True,related_name='product_lead_query')
    service = models.ForeignKey('interior_products.Service', on_delete=models.SET_NULL, null=True, blank=True,related_name='service_lead_query')
    catalouge = models.ForeignKey('interior_products.Catelogue', on_delete=models.SET_NULL, null=True, blank=True,related_name='catalouge_lead_query')

    logs = models.JSONField(default=list, null=True, blank=True)
    clientLogs = models.JSONField(default=list, null=True, blank=True,help_text="{'by':'client/business','message':'Text message','date':'date in dmy format(02-12-2026)'}")

    # --- v2.1.0.0 engine fields (additive) ---
    respondedAt = models.DateTimeField(null=True, blank=True)  # first business action on the lead
    sourceChannel = models.CharField(max_length=200, blank=True, default='')
    originType = models.CharField(max_length=50, blank=True, default='')
    originId = models.IntegerField(null=True, blank=True)
    formType = models.CharField(max_length=50, blank=True, default='')
    messageCount = models.PositiveIntegerField(default=0)

    # Qualification (task 13): computed ONCE at creation from the weights
    # singleton (QualificationWeightConfig). Never recomputed on update, so
    # tuning weights only affects NEW leads.
    tier = models.CharField(max_length=1, default='', blank=True, db_index=True)
    score = models.PositiveIntegerField(default=0)
    # Buyer's stated timeline — sources the urgency qualification signal (task 33).
    # Blank on old rows / when unanswered → urgency contributes 0.
    TIMELINE_CHOICES = [('30d', 'Within 30 days'), ('90d', '30–90 days'),
                        ('90plus', '90+ days'), ('browsing', 'Just browsing')]
    timeline = models.CharField(max_length=10, choices=TIMELINE_CHOICES, default='', blank=True)

    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_business = self.business
        self._initial_state = self._get_log_state()

    def _get_log_state(self):
        return {
            'business': self.business.businessName if self.business else None,
            'status': self.status,
            'leadStatus': self.leadStatus,
            'stage': self.stage,
            'priority': self.priority,
            'remark': self.remark,
            'tag': self.tag
        }

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        current_state = self._get_log_state()
        events = []

        if is_new:
            events.append("Lead Query Created")
        else:
            for field, old_val in self._initial_state.items():
                new_val = current_state[field]
                if old_val != new_val:
                    events.append(f"{field} updated from '{old_val}' to '{new_val}'")

        if events:
            if not isinstance(self.logs, list):
                self.logs = []

            self.logs.append({
                "event": ", ".join(events),
                "timestamp": datetime.now().strftime(NAMES.DMY_12M)
            })

        business_changed_flag = self.pk is not None and self.business != self._original_business

        super().save(*args, **kwargs)  # Save once

        if business_changed_flag:
            business_changed.send(sender=self.__class__, instance=self)

        self._original_business = self.business
        self._initial_state = current_state

    def __str__(self):
        return f'business_id {self.pk}  name: {self.name}  phone{self.phone} date {self.timestamp}'

    class Meta:
        db_table = "app_ib_leadquery"


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
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.phoneNumber and not self.stage:
            return f'ID {self.pk} phone:{self.phoneNumber}'
        elif self.phoneNumber and self.stage:
            return f'ID {self.pk} phone:{self.phoneNumber} stage:{self.stage}'
        return f'ID {self.pk}'

    class Meta:
        db_table = "app_ib_quate"
        verbose_name = "Leads for company"
        verbose_name_plural = "Platform Own Leads"


class Feedback(models.Model):
    user= models.ForeignKey('app_ib.CustomUser',on_delete=models.CASCADE, null=True, blank=True)
    contact= models.CharField(max_length=500) # lable : Contact detail
    feedback= models.TextField() # lable : Feedback rating
    status= models.TextField() # lable : [view,]
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'pk:{self.pk}  feedback:{self.feedback}'

    class Meta:
        db_table = "app_ib_feedback"


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
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'ID {self.pk} tag {self.tag}'

    class Meta:
        db_table = "app_ib_contact"


#funnel form
class FunnelForm(models.Model):
    name = models.CharField(max_length=255, default='', null=True, blank=True)
    companyName = models.CharField(max_length=255, default='', null=True, blank=True)
    email = models.CharField(max_length=255, default='', null=True, blank=True)
    phone = models.CharField(max_length=255, default='', null=True, blank=True)
    planType = models.CharField(max_length=255, default='', null=True, blank=True)
    plan = models.CharField(max_length=255, default='', null=True, blank=True)
    intrest = models.TextField(default='', null=True, blank=True)
    need = models.TextField(default='', null=True, blank=True)
    timestamp= models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=255, default='New', null=True, blank=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f' pk {self.pk} name:{self.name} phone:{self.phone}'

    class Meta:
        db_table = "app_ib_funnelform"


class Quotation(models.Model):
    """A seller-built quotation document (task 63). The buyer/seller blocks and line
    items are document SNAPSHOTS stored as JSON — they are never queried individually,
    always fetched whole with the quotation, so a join model would be pure overhead.
    Money totals are RECOMPUTED server-side from lineItems+gstPercent on every write
    (never trusted from the client). `status` is the last seller/buyer action; the
    client derives "expired" from validUntil and never stores it."""
    user = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="quotations")
    business = models.ForeignKey("interior_business.Business", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="quotations")
    lead = models.ForeignKey("interior_leads.LeadQuery", null=True, blank=True,
                             on_delete=models.SET_NULL, related_name="quotations")
    number = models.CharField(max_length=40)
    status = models.CharField(max_length=20, default="sent")  # sent|viewed|accepted|declined
    # ponytail: persisted for forward-compat; the current builder always sends "custom".
    pricingMode = models.CharField(max_length=20, default="custom")  # package|custom|per_unit
    validUntil = models.DateField(null=True, blank=True)
    fromBlock = models.JSONField(default=dict)   # {businessName,gstin,address,phone,email}
    toBlock = models.JSONField(default=dict)     # {name,phone,email,city,address}
    lineItems = models.JSONField(default=list)   # [{id,type,description,code,qty,unit,rate,amount}]
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    gstPercent = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    gstAmount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    grandTotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    terms = models.TextField(blank=True, default="")
    noteToBuyer = models.TextField(blank=True, default="")
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    sentAt = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "app_ib_quotation"
        ordering = ["-createdAt"]

    def __str__(self):
        return f"Quotation {self.number} ({self.status})"
