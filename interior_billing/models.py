"""interior_billing models — the payments/billing domain cluster.
Moved out of app_ib/models.py (TASK 14). Tables keep their pinned app_ib_*
db_table names — state-only move, no data touched. FKs to CustomUser/Business
(still app_ib) and Shop/Architect (interior_engine) are cross-app string refs;
intra-set refs (Subscription) stay direct. Constants come from
app_ib.Utils.EngineConfig (same source interior_engine uses) — no import of
app_ib.models, so no cycle."""
from django.db import models

from app_ib.Utils.EngineConfig import PLAN_STATUS, PLAN_FAMILY, PLAN_GRANTS, ENTITY_TYPE


class Subscription(models.Model):
    type= models.CharField(max_length=800,null=True, blank=True) #listing or #Filter
    # Which entity this plan unlocks (business/shop/architect). Default 'business'
    # so legacy rows + the frozen v1/plan/template/ response stay valid.
    entityType= models.CharField(max_length=50, null=True, blank=True, default='business')
    # Frontend plan category (plans-checkout sidebar): automation/business/shop/architect.
    # 'automation' is the bundle that unlocks all three entity tabs. Defaults to
    # entityType for legacy rows (filled at save() when blank).
    planFamily= models.CharField(max_length=50, null=True, blank=True, default=PLAN_FAMILY.BUSINESS)
    # The entity tabs this plan grants (e.g. automation → ["business","shop","architect"]).
    # Single source of truth for "what does buying this plan unlock" — the entitlement
    # service reads it instead of branching on type. Backfilled from planFamily at save().
    grantsEntityTypes= models.JSONField(default=list, null=True, blank=True)
    # Upgrade-ordering rank (higher = better tier); used by the upgrade flow (Prompt 9).
    tier= models.IntegerField(null=True, blank=True, default=0)
    title= models.CharField(max_length=800,null=True, blank=True)
    subtitle= models.CharField(max_length=800,null=True, blank=True)
    services= models.TextField()
    duration= models.CharField(max_length=800,null=True, blank=True)
    tag= models.CharField(max_length=800,null=True, blank=True)
    amount= models.CharField(max_length=800,null=True, blank=True)
    leadcount= models.IntegerField(null=True, blank=True,default=0)
    discountPercentage= models.CharField(max_length=800,null=True, blank=True)
    discountAmount= models.CharField(max_length=800,null=True, blank=True)
    payableAmount= models.CharField(max_length=800,null=True, blank=True)
    availableDuration = models.JSONField(
        default=list,
        null=True,
        blank=True,
        help_text="List of objects with duration and price. Example: "
                "[{'duration': 3, 'price': 100}, {'duration': 6, 'price': 180}]"
    )
    # ── v3 plans-page display catalogue (promptr2 task 78) ──
    # Display-only: money still flows from `amount`. Rows seeded VERBATIM from the
    # commercial catalogue in migration 0055; per-cycle display strings
    # (price/gstLine/total/oldPrice/savingNote/badgeLabel) live inside
    # availableDuration entries — never computed.
    features = models.JSONField(default=list, blank=True)  # [{"text": …, "subItem"?: …}]
    badge = models.CharField(max_length=100, null=True, blank=True)  # "Most popular" …
    badgeIcon = models.CharField(max_length=100, null=True, blank=True)  # tabler icon name
    # This plan's compare-table column (automation family only):
    # {"column": "Elite ⭐", "popular": true, "values": [{"feature", "value"}]}
    compareRows = models.JSONField(default=dict, blank=True)

    # cover_image= models.FileField(null=True, blank=True, upload_to='subscription/attachment')
    fallbackImageUrl= models.URLField(max_length=2250, null=True, blank=True)
    # video= models.FileField(null=True, blank=True, upload_to='subscription/video')
    videoUrl= models.URLField(max_length=2250, null=True, blank=True)
    # plan_pdf= models.FileField(null=True, blank=True, upload_to='subscription/pdf')
    planPdfUrl= models.URLField(max_length=2250, null=True, blank=True)

    isActive= models.BooleanField(default=False)
    # Soft delete (admin): hides the plan everywhere (admin list + public catalogue)
    # without breaking the FK on already-purchased BusinessPlan/ShopPlan/... rows.
    is_delete= models.BooleanField(default=False)
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'ID:{self.id} rating:{self.title}'

    def save(self, *args, **kwargs):
        # Backfill the family from the legacy entityType when unset, then derive the
        # granted tabs from the family (automation → all three). Keeps a hand-set
        # grantsEntityTypes (e.g. a custom bundle) untouched.
        if not self.planFamily:
            self.planFamily = self.entityType or PLAN_FAMILY.BUSINESS
        if not self.grantsEntityTypes:
            self.grantsEntityTypes = list(
                PLAN_GRANTS.get(self.planFamily, [self.entityType or ENTITY_TYPE.BUSINESS])
            )
        super().save(*args, **kwargs)

    class Meta:
        db_table = "app_ib_subscription"
        app_label = "interior_billing"


class PlanBillingCycle(models.Model):
    """One time/price option of a Subscription plan (Stripe Product→Price shape).
    Replaces the old "one Subscription row per cycle" + availableDuration JSON: a plan
    is ONE Subscription row, each purchasable duration is a PlanBillingCycle child.
    Money source of truth for the plan lives here (price), keyed by durationMonths."""
    plan = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="billingCycles")
    # Store ONE unit: months (1/3/6/12). No days/months heuristic — legacy _duration_months
    # only exists for old Subscription.duration strings, never for cycles.
    durationMonths = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)          # charged, GST-inclusive
    oldPrice = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # strike-through
    badgeLabel = models.CharField(max_length=100, blank=True, default='')  # "Best value" etc.
    isActive = models.BooleanField(default=True)                          # disable without deleting
    timestamp = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "app_ib_planbillingcycle"
        app_label = "interior_billing"
        unique_together = ('plan', 'durationMonths')
        ordering = ['durationMonths']

    def __str__(self):
        return f'cycle plan={self.plan_id} {self.durationMonths}mo ₹{self.price}'


# Shared status<->isActive reconciliation for all purchased plan models. `status` is
# the source of truth; the legacy `isActive` bool is derived from it so old reads keep
# working. Terminal states (cancelled/refunded) are preserved. Call from each save().
def _sync_plan_status(instance):
    if not instance.status:
        instance.status = PLAN_STATUS.PENDING
    instance.isActive = (instance.status == PLAN_STATUS.ACTIVE)


class BusinessPlan(models.Model):
    # Buy-before-entity: a plan is bought by a USER and may exist before the
    # Business is created (business FK stays nullable, filled later in-dashboard).
    user= models.ForeignKey('app_ib.CustomUser',on_delete=models.CASCADE, null=True, blank=True,related_name='business_plans')
    business= models.ForeignKey('interior_business.Business',on_delete=models.CASCADE, null=True, blank=True,related_name='business_plan')
    services= models.TextField()
    amount= models.CharField(max_length=500,default='')
    plan = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    # Months bought, snapshotted from the chosen PlanBillingCycle at purchase so expiry/
    # renewal math never re-reads plan.duration (meaningless for multi-cycle plans).
    durationMonths = models.PositiveIntegerField(null=True, blank=True)
    # Lifecycle source of truth (pending/active/expired/cancelled/refunded). isActive
    # is the derived legacy shim (isActive == status==active), kept in sync in save().
    status= models.CharField(max_length=20, default=PLAN_STATUS.PENDING, db_index=True)
    isActive= models.BooleanField(default=False)
    transactionId= models.CharField(max_length=500,default='',null=True, blank=True)
    planSummary= models.TextField()
    lastActivate= models.DateTimeField(auto_now_add=True)
    expireDate= models.DateTimeField(null=True, blank=True)
    buyIntent = models.CharField(max_length=1000,null=True, blank=True,default='website')
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'is_active:{self.isActive} expire_date:{self.expireDate}'

    def save(self, *args, **kwargs):
        _sync_plan_status(self)
        if self.isActive and self.business:
            plans = BusinessPlan.objects.filter(
                business=self.business,
                isActive=True
            ).exclude(id=self.id)
            for plan in plans:
                if int((plan.amount or '0').replace(",", "") or 0) >= int((self.amount or '0').replace(",", "") or 0):
                    self.status = PLAN_STATUS.EXPIRED
                    self.isActive = False
                    continue
                # this plan supersedes a lower active one → retire the lower one
                plan.status = PLAN_STATUS.EXPIRED
                plan.save()

        super().save(*args, **kwargs)

    class Meta:
        db_table = "app_ib_businessplan"
        app_label = "interior_billing"

class ShopPlan(models.Model):
    """Per-shop subscription (shops are 1:M per user). Buy-before-entity: bought by
    a USER, links to a Shop later (nullable shop FK). Mirrors BusinessPlan."""
    user= models.ForeignKey('app_ib.CustomUser',on_delete=models.CASCADE, null=True, blank=True,related_name='shop_plans')
    shop= models.ForeignKey('interior_engine.Shop',on_delete=models.CASCADE, null=True, blank=True,related_name='shop_plan')
    services= models.TextField(blank=True, default='')
    amount= models.CharField(max_length=500,default='')
    plan = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    # Months bought, snapshotted from the chosen PlanBillingCycle at purchase so expiry/
    # renewal math never re-reads plan.duration (meaningless for multi-cycle plans).
    durationMonths = models.PositiveIntegerField(null=True, blank=True)
    status= models.CharField(max_length=20, default=PLAN_STATUS.PENDING, db_index=True)
    isActive= models.BooleanField(default=False)
    transactionId= models.CharField(max_length=500,default='',null=True, blank=True)
    planSummary= models.TextField(blank=True, default='')
    lastActivate= models.DateTimeField(auto_now_add=True)
    expireDate= models.DateTimeField(null=True, blank=True)
    buyIntent = models.CharField(max_length=1000,null=True, blank=True,default='website')
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'shop_plan is_active:{self.isActive} expire_date:{self.expireDate}'

    def save(self, *args, **kwargs):
        _sync_plan_status(self)
        super().save(*args, **kwargs)

    class Meta:
        db_table = "app_ib_shopplan"
        app_label = "interior_billing"


class ArchitectPlan(models.Model):
    """Architect subscription (1 per user). Buy-before-entity: bought by a USER, links
    to an Architect later (nullable architect FK). Mirrors BusinessPlan."""
    user= models.ForeignKey('app_ib.CustomUser',on_delete=models.CASCADE, null=True, blank=True,related_name='architect_plans')
    architect= models.ForeignKey('interior_engine.Architect',on_delete=models.CASCADE, null=True, blank=True,related_name='architect_plan')
    services= models.TextField(blank=True, default='')
    amount= models.CharField(max_length=500,default='')
    plan = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    # Months bought, snapshotted from the chosen PlanBillingCycle at purchase so expiry/
    # renewal math never re-reads plan.duration (meaningless for multi-cycle plans).
    durationMonths = models.PositiveIntegerField(null=True, blank=True)
    status= models.CharField(max_length=20, default=PLAN_STATUS.PENDING, db_index=True)
    isActive= models.BooleanField(default=False)
    transactionId= models.CharField(max_length=500,default='',null=True, blank=True)
    planSummary= models.TextField(blank=True, default='')
    lastActivate= models.DateTimeField(auto_now_add=True)
    expireDate= models.DateTimeField(null=True, blank=True)
    buyIntent = models.CharField(max_length=1000,null=True, blank=True,default='website')
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'architect_plan is_active:{self.isActive} expire_date:{self.expireDate}'

    def save(self, *args, **kwargs):
        _sync_plan_status(self)
        super().save(*args, **kwargs)

    class Meta:
        db_table = "app_ib_architectplan"
        app_label = "interior_billing"


class AutomationPlan(models.Model):
    """Automation BUNDLE subscription. Unlike the single-entity plans, buying it unlocks
    ALL THREE seller tabs (business/shop/architect) — its Subscription.grantsEntityTypes
    is the full set. It is entity-less itself, but carries one nullable FK per entity so a
    single automation purchase can be linked to the user's business + shop + architect as
    each is created. Mirrors the other plan models' lifecycle (status + isActive shim)."""
    user= models.ForeignKey('app_ib.CustomUser',on_delete=models.CASCADE, null=True, blank=True,related_name='automation_plans')
    business= models.ForeignKey('interior_business.Business',on_delete=models.SET_NULL, null=True, blank=True,related_name='automation_plan')
    shop= models.ForeignKey('interior_engine.Shop',on_delete=models.SET_NULL, null=True, blank=True,related_name='automation_plan')
    architect= models.ForeignKey('interior_engine.Architect',on_delete=models.SET_NULL, null=True, blank=True,related_name='automation_plan')
    services= models.TextField(blank=True, default='')
    amount= models.CharField(max_length=500,default='')
    plan = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    # Months bought, snapshotted from the chosen PlanBillingCycle at purchase so expiry/
    # renewal math never re-reads plan.duration (meaningless for multi-cycle plans).
    durationMonths = models.PositiveIntegerField(null=True, blank=True)
    status= models.CharField(max_length=20, default=PLAN_STATUS.PENDING, db_index=True)
    isActive= models.BooleanField(default=False)
    transactionId= models.CharField(max_length=500,default='',null=True, blank=True)
    planSummary= models.TextField(blank=True, default='')
    lastActivate= models.DateTimeField(auto_now_add=True)
    expireDate= models.DateTimeField(null=True, blank=True)
    buyIntent = models.CharField(max_length=1000,null=True, blank=True,default='website')
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'automation_plan is_active:{self.isActive} expire_date:{self.expireDate}'

    def save(self, *args, **kwargs):
        _sync_plan_status(self)
        super().save(*args, **kwargs)

    class Meta:
        db_table = "app_ib_automationplan"
        app_label = "interior_billing"


# payment gateway related models
class TransectionData(models.Model):
    orderId= models.CharField(max_length=500,default='')
    transactionId= models.CharField(max_length=500,default='')
    amount= models.CharField(max_length=500,default='')
    paymentFor= models.CharField(max_length=500,default='')
    createdAt = models.DateTimeField()
    expiryAt= models.DateTimeField()
    orderStatus= models.CharField(max_length=500,default='')
    paymentSessionId= models.CharField(max_length=1000,default='')
    # Plan family (business/shop/architect/automation) captured at write time so
    # revenue-by-family analytics can split plan purchases. Blank on old rows and
    # non-plan payments (ads) → analytics falls back to paymentFor.
    planFamily= models.CharField(max_length=50, default='', blank=True)
    # Refund tracking (admin ops console, promptsadmin task 46). Extends this
    # model in place rather than forking the payments schema.
    refundStatus= models.CharField(max_length=50, default='', blank=True)  # '' | REFUNDED | REJECTED
    refundAmount= models.CharField(max_length=500, default='', blank=True)
    refundReason= models.TextField(default='', blank=True)
    refundedAt= models.DateTimeField(null=True, blank=True)
    refundedBy= models.ForeignKey('app_ib.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='refunds_actioned')
    # Manual-payment verification (promptsadmin task 11). 'manual' rows carry a
    # SUBMITTED->PAID/REJECTED lifecycle in orderStatus, verified by an admin.
    paymentMethod= models.CharField(max_length=20, default='gateway')  # 'gateway' | 'manual'
    proofUrl= models.TextField(default='', blank=True)  # buyer-uploaded UPI/NEFT payment proof (manual)
    verifiedBy= models.ForeignKey('app_ib.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments_verified')
    verifiedAt= models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f" transection data for {self.paymentFor} with transaction id {self.transactionId}"

    class Meta:
        db_table = "app_ib_transectiondata"
        app_label = "interior_billing"

# Platform own Plan buy query
class PlanQuery(models.Model):
    user= models.ForeignKey('app_ib.CustomUser',on_delete=models.CASCADE, null=True, blank=True)
    plan= models.CharField(max_length=500,default='')
    name= models.CharField(max_length=500,default='')
    email= models.CharField(max_length=500,default='')
    phone= models.CharField(max_length=500,default='')
    state= models.CharField(max_length=500,default='')
    country= models.CharField(max_length=500,default='')
    address= models.TextField(default='')
    transactionId= models.CharField(max_length=500,default='')
    stage= models.CharField(max_length=500,default='') #{"1":"Lead","2":"Contacted","3":"Followed Up","4":"Closed"}
    attachment= models.FileField(null=True, blank=True, upload_to='lead_query/attachment')
    attachmentUrl = models.URLField(default='',null=True, blank=True)
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f' ID {self.pk} phone:{self.phone} stage:{self.stage}'

    class Meta:
        db_table = "app_ib_planquery"
        app_label = "interior_billing"
