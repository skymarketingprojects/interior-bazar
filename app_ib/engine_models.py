"""
engine_models.py — New models for the v2.1.0.0 discovery/trending engine
(MODEL_REVIEW_FINAL). Imported at the bottom of app_ib/models.py so every model
here is registered under the `app_ib` app label.

Design rules from the spec:
- All user FKs use on_delete=SET_NULL (content survives an ownerless account).
- Generic FK pattern = contentType (FK->ContentType) + objectId (PositiveIntegerField).
- Choice / status / type / role values come from EngineConfig, never inline.
- Shop / Architect are independent top-level entities owned via .user (never .business).
"""
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify


def _unique_slug(model_class, text, pk, fallback):
    base = slugify(text or "") or fallback
    candidate, n = base, 1
    while model_class.objects.filter(slug=candidate).exclude(pk=pk).exists():
        n += 1
        candidate = f"{base}-{n}"
    return candidate


from app_ib.Utils.EngineConfig import (
    ENTITY_TYPE, TRENDING_PERIOD, LEADERBOARD_PERIOD, LEADERBOARD_BOARD,
    LEADERBOARD_SCOPE, CLICK_TYPE, FEED_EVENT_TYPE, NOTIFICATION_TYPE,
    TEAM_ROLE, SHOP_TYPE, CONVERSATION_STATUS, ENGAGEMENT_VERB, ALGO,
)

USER = settings.AUTH_USER_MODEL


# ---------------------------------------------------------------------------
# Abstract base for the generic-FK event/score models
# ---------------------------------------------------------------------------
class GenericContentBase(models.Model):
    contentType = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    objectId = models.PositiveIntegerField()
    content = GenericForeignKey("contentType", "objectId")

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# Supporting top-level entities
# ---------------------------------------------------------------------------
class Platform(models.Model):
    """Video source platform (YouTube, Instagram, ...). Shared by ShortVideoLink + FallbackVideo."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)

    class Meta:
        app_label = "app_ib"

    def __str__(self):
        return self.name


class Architect(models.Model):
    """Independent top-level entity. Geography via plain city/state strings (no Location rows)."""
    # 1 architect per user (buy-before-entity model). related_name 'user_architect'.
    user = models.OneToOneField(USER, on_delete=models.SET_NULL, null=True, blank=True, related_name="user_architect")
    businesses = models.ManyToManyField("app_ib.Business", blank=True, related_name="linked_architects")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    bio = models.TextField(blank=True, default="")
    coverImage = models.TextField(blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    rating = models.FloatField(default=0.0)
    totalReviews = models.PositiveIntegerField(default=0)
    ratingBreakdown = models.JSONField(default=dict, blank=True)
    trendingScore = models.FloatField(default=0.0, db_index=True)
    hotScore = models.FloatField(default=0.0, db_index=True)
    viewCount = models.PositiveIntegerField(default=0)
    leadCount = models.PositiveIntegerField(default=0)
    completionPercent = models.PositiveIntegerField(default=0)
    canGoLive = models.BooleanField(default=False)
    avgResponseSeconds = models.IntegerField(null=True, blank=True)
    label = models.CharField(max_length=50, blank=True, default="")
    expertiseTags = models.ManyToManyField("app_ib.Tag", blank=True, related_name="expert_architects")
    isActive = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app_ib"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Architect, self.name, self.pk, "architect")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Architect {self.name} (pk {self.pk})"


class Shop(models.Model):
    """Independent top-level entity. Ownership via .user; .business is a soft display link only."""
    user = models.ForeignKey(USER, on_delete=models.SET_NULL, null=True, related_name="shops")
    business = models.ForeignKey("app_ib.Business", null=True, blank=True, on_delete=models.SET_NULL, related_name="linked_shops")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    shopType = models.CharField(max_length=20, default=SHOP_TYPE.OFFLINE)
    bio = models.TextField(blank=True, default="")
    coverImage = models.TextField(blank=True, default="")
    bannerImage = models.TextField(blank=True, default="")
    bannerLink = models.TextField(blank=True, default="")
    isActive = models.BooleanField(default=True)
    isPrimary = models.BooleanField(default=False)
    city = models.CharField(max_length=100, blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    viewCount = models.PositiveIntegerField(default=0)
    leadCount = models.PositiveIntegerField(default=0)
    trendingScore = models.FloatField(default=0.0, db_index=True)
    hotScore = models.FloatField(default=0.0, db_index=True)
    rating = models.FloatField(default=0.0)
    totalReviews = models.PositiveIntegerField(default=0)
    ratingBreakdown = models.JSONField(default=dict, blank=True)
    completionPercent = models.PositiveIntegerField(default=0)
    canGoLive = models.BooleanField(default=False)
    avgResponseSeconds = models.IntegerField(null=True, blank=True)
    label = models.CharField(max_length=50, blank=True, default="")
    expertiseTags = models.ManyToManyField("app_ib.Tag", blank=True, related_name="expert_shops")
    timestamp = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app_ib"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Shop, self.name, self.pk, "shop")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Shop {self.name} (pk {self.pk})"


class Testimonial(models.Model):
    """Platform video testimonials shown in the home 'Video Stories' section."""
    videoUrl = models.TextField()
    thumbnailUrl = models.TextField(blank=True, default="")
    authorName = models.CharField(max_length=150)
    authorRole = models.CharField(max_length=150, blank=True, default="")
    businessName = models.CharField(max_length=200, blank=True, default="")
    quote = models.TextField(blank=True, default="")
    rating = models.PositiveSmallIntegerField(default=5)
    isActive = models.BooleanField(default=True)
    index = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "app_ib"
        ordering = ["index", "-timestamp"]

    def __str__(self):
        return f"Testimonial {self.authorName}"


class ContactInfo(models.Model):
    """Multi-row contact details. Exactly one of business/shop/architect must be set."""
    business = models.ForeignKey("app_ib.Business", null=True, blank=True, on_delete=models.SET_NULL, related_name="contacts")
    shop = models.ForeignKey(Shop, null=True, blank=True, on_delete=models.SET_NULL, related_name="contacts")
    architect = models.ForeignKey(Architect, null=True, blank=True, on_delete=models.SET_NULL, related_name="contacts")
    label = models.CharField(max_length=100, blank=True, default="")
    isPrimary = models.BooleanField(default=False)
    countryCode = models.CharField(max_length=10, default="+91")
    phone = models.CharField(max_length=30, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    whatsapp = models.CharField(max_length=30, blank=True, default="")
    website = models.URLField(blank=True, default="")
    gmb = models.URLField(blank=True, default="")
    workingPlaceLink = models.URLField(blank=True, default="")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "app_ib"

    def clean(self):
        from django.core.exceptions import ValidationError
        owners = [self.business_id, self.shop_id, self.architect_id]
        if sum(1 for o in owners if o) != 1:
            raise ValidationError("Exactly one of business / shop / architect must be set.")

    def __str__(self):
        return f"ContactInfo {self.label or self.phone} (pk {self.pk})"


class Award(models.Model):
    """Awards and credentials. Exactly one of business/shop/architect must be set."""
    business = models.ForeignKey("app_ib.Business", null=True, blank=True, on_delete=models.SET_NULL, related_name="awards")
    shop = models.ForeignKey(Shop, null=True, blank=True, on_delete=models.SET_NULL, related_name="awards")
    architect = models.ForeignKey(Architect, null=True, blank=True, on_delete=models.SET_NULL, related_name="awards")
    title = models.CharField(max_length=255)
    issuer = models.CharField(max_length=255, blank=True, default="")
    year = models.CharField(max_length=10, blank=True, default="")
    description = models.TextField(blank=True, default="")
    imageUrl = models.TextField(blank=True, default="")
    kind = models.CharField(max_length=20, default="award")  # "award" | "credential"
    index = models.PositiveIntegerField(default=0)
    isActive = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "app_ib"
        ordering = ["index", "-timestamp"]

    def clean(self):
        from django.core.exceptions import ValidationError
        owners = [self.business_id, self.shop_id, self.architect_id]
        if sum(1 for o in owners if o) != 1:
            raise ValidationError("Exactly one of business / shop / architect must be set.")

    def __str__(self):
        return f"Award {self.title} [{self.kind}] (pk {self.pk})"


class ProcessStep(models.Model):
    """Process steps / workflow steps. Exactly one of business/shop/architect must be set."""
    business = models.ForeignKey("app_ib.Business", null=True, blank=True, on_delete=models.SET_NULL, related_name="process_steps")
    shop = models.ForeignKey(Shop, null=True, blank=True, on_delete=models.SET_NULL, related_name="process_steps")
    architect = models.ForeignKey(Architect, null=True, blank=True, on_delete=models.SET_NULL, related_name="process_steps")
    stepNumber = models.PositiveSmallIntegerField(default=0)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    index = models.PositiveIntegerField(default=0)
    isActive = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "app_ib"
        ordering = ["index", "-timestamp"]

    def clean(self):
        from django.core.exceptions import ValidationError
        owners = [self.business_id, self.shop_id, self.architect_id]
        if sum(1 for o in owners if o) != 1:
            raise ValidationError("Exactly one of business / shop / architect must be set.")

    def __str__(self):
        return f"ProcessStep {self.stepNumber}: {self.title} (pk {self.pk})"


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------
class Review(models.Model):
    reviewer = models.ForeignKey(USER, on_delete=models.SET_NULL, null=True, related_name="reviews")
    business = models.ForeignKey("app_ib.Business", null=True, blank=True, on_delete=models.SET_NULL, related_name="reviews")
    shop = models.ForeignKey(Shop, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviews")
    product = models.ForeignKey("interior_products.Product", null=True, blank=True, on_delete=models.SET_NULL, related_name="reviews")
    service = models.ForeignKey("interior_products.Service", null=True, blank=True, on_delete=models.SET_NULL, related_name="reviews")
    architect = models.ForeignKey(Architect, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviews")
    rating = models.PositiveSmallIntegerField()  # 1-5
    title = models.CharField(max_length=255, blank=True, default="")
    body = models.TextField(blank=True, default="")
    isVerifiedPurchase = models.BooleanField(default=False)
    helpfulCount = models.PositiveIntegerField(default=0)
    isApproved = models.BooleanField(default=True)
    isDeleted = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app_ib"
        indexes = [models.Index(fields=["business"]), models.Index(fields=["shop"])]

    def clean(self):
        from django.core.exceptions import ValidationError
        owners = [self.business_id, self.shop_id, self.product_id, self.service_id, self.architect_id]
        if sum(1 for o in owners if o) != 1:
            raise ValidationError("Exactly one review target entity must be set.")

    def __str__(self):
        return f"Review {self.rating}* by {self.reviewer_id} (pk {self.pk})"


class ReviewImage(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="images")
    imageUrl = models.TextField()
    index = models.PositiveSmallIntegerField(default=0)

    class Meta:
        app_label = "app_ib"


# ---------------------------------------------------------------------------
# Raw event logs
# ---------------------------------------------------------------------------
class ViewEvent(GenericContentBase):
    user = models.ForeignKey(USER, on_delete=models.SET_NULL, null=True, blank=True, related_name="view_events")
    sessionId = models.CharField(max_length=64, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    dwellSeconds = models.IntegerField(null=True, blank=True)  # null = unmeasured, not zero
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "app_ib"
        indexes = [
            models.Index(fields=["contentType", "objectId", "timestamp"]),
            models.Index(fields=["city", "timestamp"]),
        ]


class SearchEvent(models.Model):
    user = models.ForeignKey(USER, on_delete=models.SET_NULL, null=True, blank=True, related_name="search_events")
    sessionId = models.CharField(max_length=64, blank=True, default="")
    query = models.CharField(max_length=500, db_index=True)
    normalizedQuery = models.CharField(max_length=500, db_index=True)
    resultCount = models.PositiveIntegerField(default=0)
    clickedResultType = models.CharField(max_length=20, blank=True, default="")
    clickedResultId = models.PositiveIntegerField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "app_ib"


class ClickEvent(GenericContentBase):
    user = models.ForeignKey(USER, on_delete=models.SET_NULL, null=True, blank=True, related_name="click_events")
    sessionId = models.CharField(max_length=64, blank=True, default="")
    clickType = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "app_ib"
        indexes = [models.Index(fields=["contentType", "objectId", "timestamp"])]


# ---------------------------------------------------------------------------
# Pre-computed scores / boards
# ---------------------------------------------------------------------------
class TrendingScore(GenericContentBase):
    period = models.CharField(max_length=10)
    city = models.CharField(max_length=100, blank=True, default="")  # blank = national
    score = models.FloatField(default=0.0, db_index=True)
    rank = models.PositiveIntegerField(default=0)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app_ib"
        constraints = [
            models.UniqueConstraint(fields=["contentType", "objectId", "period", "city"],
                                    name="uniq_trendingscore_entity_period_city"),
        ]


class LeaderboardEntry(GenericContentBase):
    boardType = models.CharField(max_length=20)
    period = models.CharField(max_length=20)
    scope = models.CharField(max_length=20, default=LEADERBOARD_SCOPE.GLOBAL)
    entityType = models.CharField(max_length=20)            # denormalized
    displayName = models.CharField(max_length=255, default="")
    imageUrl = models.TextField(blank=True, default="")
    slug = models.SlugField(max_length=255, blank=True, default="")
    rank = models.PositiveIntegerField(default=0)
    score = models.FloatField(default=0.0)
    genuineViews = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    computedAt = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app_ib"
        constraints = [
            models.UniqueConstraint(fields=["boardType", "period", "scope", "contentType", "objectId"],
                                    name="uniq_leaderboard_entry"),
        ]


class BehindTheTrendStory(models.Model):
    business = models.ForeignKey("app_ib.Business", on_delete=models.CASCADE, related_name="trend_stories")
    rank = models.PositiveIntegerField(default=0)
    rankFrom = models.PositiveIntegerField(null=True, blank=True)
    rankTo = models.PositiveIntegerField(null=True, blank=True)
    windowLabel = models.CharField(max_length=100, default="")
    planAtCompute = models.CharField(max_length=50, default="")
    imageUrl = models.TextField(blank=True, default="")
    enquiryGrowthPct = models.FloatField(null=True, blank=True)
    headline = models.CharField(max_length=255, default="")
    eyebrow = models.CharField(max_length=255, default="")
    storyTitle = models.CharField(max_length=255, default="")
    storyBody = models.TextField(default="")
    trendTags = models.JSONField(default=list, blank=True)
    isPublished = models.BooleanField(default=True)
    isAiEdited = models.BooleanField(default=False)
    snapshotDate = models.DateField()

    class Meta:
        app_label = "app_ib"


# ---------------------------------------------------------------------------
# User-facing state
# ---------------------------------------------------------------------------
class SavedItem(GenericContentBase):
    user = models.ForeignKey(USER, on_delete=models.SET_NULL, null=True, related_name="saved_items")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "app_ib"
        constraints = [
            models.UniqueConstraint(fields=["user", "contentType", "objectId"], name="uniq_saved_item"),
        ]


class RecentlyViewed(GenericContentBase):
    user = models.ForeignKey(USER, on_delete=models.SET_NULL, null=True, related_name="recently_viewed")
    viewedAt = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        app_label = "app_ib"
        constraints = [
            models.UniqueConstraint(fields=["user", "contentType", "objectId"], name="uniq_recently_viewed"),
        ]


class EngagementActivity(GenericContentBase):
    """Inbound "recent activity" feed for a seller: one row per action that ANOTHER
    user performed on an entity the seller OWNS (their business/shop/architect
    profile, product, or service) — e.g. "someone viewed your product", "someone
    saved your shop", "someone filled your form".

    Distinct from ViewEvent/ClickEvent (raw analytics keyed by the ACTOR) and from
    RecentlyViewed (the seller's OWN browsing). Here the row is keyed by `owner`
    (the seller) so the dashboard feed is a single indexed `filter(owner=...)`.

    Written fire-and-forget from the engine write points (track_view, track_click,
    toggle_saved) and a LeadQuery post_save signal, via
    algorithms.state.record_engagement(). entityType / entityName / actorName are
    denormalized so the read path needs no extra joins. Self-actions (actor == owner)
    are never recorded.
    """
    owner = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="engagement_received", db_index=True)
    actor = models.ForeignKey(USER, on_delete=models.SET_NULL, null=True, blank=True, related_name="engagement_made")
    actorName = models.CharField(max_length=255, blank=True, default="")  # denormalized (or "Someone" if anon)
    verb = models.CharField(max_length=20)                                # ENGAGEMENT_VERB.*
    entityType = models.CharField(max_length=20, blank=True, default="")  # denormalized owner-entity kind
    entityName = models.CharField(max_length=255, blank=True, default="") # denormalized owner-entity name
    count = models.PositiveIntegerField(default=1)                        # bumped on dedupe within the window
    isRead = models.BooleanField(default=False)
    timestamp = models.DateTimeField(db_index=True)                       # latest activity time (bumped on dedupe)

    class Meta:
        app_label = "app_ib"
        indexes = [
            models.Index(fields=["owner", "timestamp"]),
            models.Index(fields=["owner", "isRead"]),
        ]


class Notification(models.Model):
    """Unread-only store; row deleted on read."""
    user = models.ForeignKey(USER, on_delete=models.SET_NULL, null=True, related_name="notifications")
    type = models.CharField(max_length=20)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True, default="")
    actionUrl = models.CharField(max_length=500, blank=True, default="")
    dedupeKey = models.CharField(max_length=255, blank=True, default="")
    groupCount = models.PositiveIntegerField(default=1)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "app_ib"


# ---------------------------------------------------------------------------
# Team + analytics + tags
# ---------------------------------------------------------------------------
class BusinessTeamMember(models.Model):
    business = models.ForeignKey("app_ib.Business", on_delete=models.CASCADE, related_name="team_members")
    user = models.ForeignKey(USER, on_delete=models.SET_NULL, null=True, related_name="team_memberships")
    role = models.CharField(max_length=20, default=TEAM_ROLE.STAFF)
    isActive = models.BooleanField(default=True)
    invitedBy = models.ForeignKey(USER, null=True, blank=True, on_delete=models.SET_NULL, related_name="invites")
    joinedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "app_ib"
        constraints = [
            models.UniqueConstraint(fields=["business", "user"], name="uniq_team_member"),
        ]


class BusinessAnalytics(GenericContentBase):
    date = models.DateField(db_index=True)
    viewCount = models.PositiveIntegerField(default=0)
    uniqueVisitorCount = models.PositiveIntegerField(default=0)
    leadCount = models.PositiveIntegerField(default=0)
    quoteCount = models.PositiveIntegerField(default=0)
    whatsappTapCount = models.PositiveIntegerField(default=0)
    callTapCount = models.PositiveIntegerField(default=0)
    saveCount = models.PositiveIntegerField(default=0)
    enquiryGrowthPct = models.FloatField(null=True, blank=True)

    class Meta:
        app_label = "app_ib"
        constraints = [
            models.UniqueConstraint(fields=["contentType", "objectId", "date"], name="uniq_business_analytics_day"),
        ]


class Tag(models.Model):
    value = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=100, unique=True)
    usageCount = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = "app_ib"

    @classmethod
    def getOrCreateFromText(cls, text):
        from app_ib.algorithms.text import normalize
        value = normalize(text, strip_stopwords=True)
        if not value:
            return None
        slug = slugify(value)
        obj, _ = cls.objects.get_or_create(value=value, defaults={"slug": slug or value})
        return obj

    def __str__(self):
        return self.value


# ---------------------------------------------------------------------------
# Live feed + videos
# ---------------------------------------------------------------------------
class FeedEvent(models.Model):
    contentType = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    objectId = models.PositiveIntegerField(null=True, blank=True)
    eventType = models.CharField(max_length=20)
    template = models.CharField(max_length=500)
    city = models.CharField(max_length=100, blank=True, default="")
    isSynthetic = models.BooleanField(default=False)   # internal only — never in API output
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "app_ib"


class SyntheticEventTemplate(models.Model):
    template = models.TextField()  # placeholders {city} {plan}
    weight = models.PositiveIntegerField(default=1)
    eventType = models.CharField(max_length=20, default=FEED_EVENT_TYPE.SYNTHETIC)
    isActive = models.BooleanField(default=True)

    class Meta:
        app_label = "app_ib"


class ShortVideoLink(GenericContentBase):
    videoUrl = models.TextField()
    platform = models.ForeignKey(Platform, on_delete=models.SET_NULL, null=True, blank=True)
    isPrimary = models.BooleanField(default=False)
    displayOrder = models.PositiveIntegerField(default=0)
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "app_ib"


class FallbackVideo(models.Model):
    videoUrl = models.TextField()
    platform = models.ForeignKey(Platform, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255, blank=True, default="")
    displayOrder = models.PositiveIntegerField(default=0)
    isActive = models.BooleanField(default=True)

    class Meta:
        app_label = "app_ib"


class Project(models.Model):
    """A design project / 'design idea'. Belongs to an Architect (and optionally a
    Business). Powers the Explore 'Design Ideas' feed."""
    architect = models.ForeignKey(Architect, null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name="projects")
    business = models.ForeignKey("app_ib.Business", null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="projects")
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, null=True, blank=True, unique=True)
    description = models.TextField(blank=True, default="")
    coverImage = models.TextField(blank=True, default="")
    images = models.JSONField(default=list, blank=True)   # list of image URLs
    city = models.CharField(max_length=100, blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    style = models.CharField(max_length=100, blank=True, default="")  # e.g. modern, minimalist
    tags = models.JSONField(default=list, blank=True)
    viewCount = models.PositiveIntegerField(default=0)
    isActive = models.BooleanField(default=True)
    index = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app_ib"
        ordering = ["index", "-timestamp"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Project, self.title, self.pk, "project")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Project {self.title} (pk {self.pk})"


class EditorsPick(models.Model):
    """Editorially-surfaced trending Architect with AI (Gemini) copy + template
    fallback. Written by the `compute_editors_pick` background job — never AI on read."""
    architect = models.ForeignKey(Architect, on_delete=models.CASCADE, related_name="editors_picks")
    rank = models.PositiveIntegerField(default=0)
    eyebrow = models.CharField(max_length=255, default="")
    headline = models.CharField(max_length=255, default="")
    body = models.TextField(default="")
    trendTags = models.JSONField(default=list, blank=True)
    imageUrl = models.TextField(blank=True, default="")
    source = models.CharField(max_length=20, default="template")  # gemini | template
    isPublished = models.BooleanField(default=True)
    isAiEdited = models.BooleanField(default=False)
    snapshotDate = models.DateField()

    class Meta:
        app_label = "app_ib"
        constraints = [
            models.UniqueConstraint(fields=["architect", "snapshotDate"], name="uniq_editors_pick_day"),
        ]


class Conversation(models.Model):
    """A chat thread between a client and a business (owner). Created from a lead."""
    lead = models.ForeignKey("app_ib.LeadQuery", null=True, blank=True, on_delete=models.SET_NULL,
                             related_name="conversations")
    business = models.ForeignKey("app_ib.Business", null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="conversations")
    clientUser = models.ForeignKey(USER, null=True, on_delete=models.SET_NULL, related_name="client_conversations")
    businessUser = models.ForeignKey(USER, null=True, on_delete=models.SET_NULL, related_name="business_conversations")
    status = models.CharField(max_length=20, default=CONVERSATION_STATUS.REQUESTED)
    declineReason = models.CharField(max_length=255, blank=True, default="")
    lastMessageAt = models.DateTimeField(null=True, blank=True, db_index=True)
    # item 6: first-response tracking — set on first business-side reply
    firstResponseSeconds = models.PositiveIntegerField(null=True, blank=True)
    # Per-participant soft delete: hides the thread from that user's list only
    # (task 53 — "Delete enquiry"). The conversation is never hard-deleted so the
    # other party keeps their copy.
    clientDeleted = models.BooleanField(default=False)
    businessDeleted = models.BooleanField(default=False)
    # Attached label ids (buyer inbox organisation, task 54) — e.g. ["l_vip","l_hot"].
    labels = models.JSONField(default=list, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app_ib"
        indexes = [models.Index(fields=["clientUser", "status"]),
                   models.Index(fields=["businessUser", "status"])]

    def other_party(self, user_id):
        return self.businessUser_id if user_id == self.clientUser_id else self.clientUser_id

    def is_participant(self, user_id):
        return user_id in (self.clientUser_id, self.businessUser_id)

    def __str__(self):
        return f"Conversation {self.pk} [{self.status}]"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(USER, null=True, on_delete=models.SET_NULL, related_name="sent_messages")
    body = models.TextField()
    # Uploaded file attachments — list of {name, url, size} (task 56).
    attachments = models.JSONField(default=list, blank=True)
    isRead = models.BooleanField(default=False)
    createdAt = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "app_ib"
        indexes = [models.Index(fields=["conversation", "createdAt"])]


class DailySnapshot(models.Model):
    """Durable snapshot behind the discovery cache (guardian re-warms Redis from here)."""
    listKey = models.CharField(max_length=100, db_index=True)
    snapshotDate = models.DateField()
    payload = models.JSONField(default=dict)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app_ib"
        constraints = [
            models.UniqueConstraint(fields=["listKey", "snapshotDate"], name="uniq_daily_snapshot"),
        ]


# ---------------------------------------------------------------------------
# Platform ads  (item 11)
# ---------------------------------------------------------------------------
class AdPage(models.Model):
    """Named page slot — one row per page that can show ads."""
    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    isActive = models.BooleanField(default=True)

    class Meta:
        app_label = "app_ib"

    def __str__(self):
        return self.slug


class PlatformAd(models.Model):
    """A single ad unit shown on a page."""
    page = models.ForeignKey(AdPage, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name="ads")
    placement = models.CharField(max_length=100, default="inline")
    eyebrow = models.CharField(max_length=255, blank=True, default="")
    heading1 = models.CharField(max_length=255, blank=True, default="")
    heading2 = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    buttonLabel = models.CharField(max_length=100, blank=True, default="")
    buttonLink = models.TextField(blank=True, default="")
    imageUrl = models.TextField(blank=True, default="")
    theme = models.CharField(max_length=50, default="green")
    displayOrder = models.PositiveIntegerField(default=0)
    isActive = models.BooleanField(default=True)
    startsAt = models.DateTimeField(null=True, blank=True)
    endsAt = models.DateTimeField(null=True, blank=True)
    impressionCount = models.PositiveIntegerField(default=0)
    clickCount = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "app_ib"
        ordering = ["placement", "displayOrder", "timestamp"]

    def __str__(self):
        return f"Ad {self.heading1 or self.id} [{self.page}]"


# ---------------------------------------------------------------------------
# Phase 2/3 — UserSession, RelatedItem
# ---------------------------------------------------------------------------
class UserSession(models.Model):
    """Tracks per-device JWT sessions for the active-sessions dashboard."""
    user = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="sessions")
    jti = models.CharField(max_length=64, blank=True, default="", db_index=True)
    deviceLabel = models.CharField(max_length=120, blank=True, default="")
    userAgent = models.TextField(blank=True, default="")
    ipAddress = models.GenericIPAddressField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True, default="")
    lastActiveAt = models.DateTimeField(auto_now=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    revokedAt = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "app_ib"
        ordering = ["-lastActiveAt"]
        indexes = [
            models.Index(fields=["user", "revokedAt"]),
        ]

    def __str__(self):
        return f"UserSession user={self.user_id} jti={self.jti[:12]}… ({self.deviceLabel or 'unknown'})"


class RelatedItem(models.Model):
    """Pre-computed co-view / co-click related entity pairs (source → target)."""
    sourceContentType = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="related_source"
    )
    sourceObjectId = models.PositiveIntegerField(db_index=True)
    targetContentType = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="related_target"
    )
    targetObjectId = models.PositiveIntegerField()
    score = models.FloatField(default=0.0, db_index=True)
    reason = models.CharField(max_length=20, default="co_view")
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app_ib"
        constraints = [
            models.UniqueConstraint(
                fields=["sourceContentType", "sourceObjectId", "targetContentType", "targetObjectId"],
                name="uniq_related_pair",
            ),
        ]
        indexes = [
            models.Index(fields=["sourceContentType", "sourceObjectId", "score"]),
        ]

    def __str__(self):
        return (
            f"RelatedItem {self.sourceContentType_id}:{self.sourceObjectId}"
            f" → {self.targetContentType_id}:{self.targetObjectId}"
            f" score={self.score} [{self.reason}]"
        )


# ---------------------------------------------------------------------------
# AI Specialization — auto-generated "what they specialize in" cards.
# Bootstrap (one-time, debounced) creates the first BusinessSpecialization;
# afterwards the drift cron regenerates only when profile text changes >= 25%.
# (See app_ib/algorithms/specialization.py.)
# ---------------------------------------------------------------------------
from app_ib.Utils.StaticValues import SPEC_JOB_STATUS, SPEC_SOURCE


class BusinessSpecialization(models.Model):
    business = models.OneToOneField(
        "app_ib.Business", on_delete=models.CASCADE, related_name="specialization"
    )
    # [{icon, title, desc}] — served to the business detail page (AboutSection specs).
    cards = models.JSONField(default=list, blank=True)
    # Canonical business+profile text used at the last generation (drift baseline).
    profileSnapshot = models.TextField(default="", blank=True)
    snapshotHash = models.CharField(max_length=64, default="", blank=True)
    source = models.CharField(max_length=20, default=SPEC_SOURCE.template)
    generatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app_ib"

    def __str__(self):
        return f"Specialization(business={self.business_id}, cards={len(self.cards or [])})"


class SpecializationJob(models.Model):
    """One-time bootstrap queue. A pending job is (re)scheduled while the owner is
    still populating their business; the processor drains it after the debounce."""
    entityType = models.CharField(max_length=20, default=ENTITY_TYPE.BUSINESS)
    business = models.ForeignKey(
        "app_ib.Business", on_delete=models.CASCADE, related_name="specialization_jobs"
    )
    scheduledAt = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=20, default=SPEC_JOB_STATUS.pending, db_index=True)
    reason = models.CharField(max_length=50, default="", blank=True)
    attempts = models.PositiveIntegerField(default=0)
    lastError = models.TextField(default="", blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app_ib"
        indexes = [
            models.Index(fields=["status", "scheduledAt"]),
        ]

    def __str__(self):
        return f"SpecializationJob(business={self.business_id}, status={self.status}, at={self.scheduledAt})"


class Differentiator(models.Model):
    """A "What makes IB different" card: an icon chip, heading, description, and a
    variable-length list of `eliminates` — the competing SaaS/tools IB replaces
    (rendered with strikethrough on the frontend). Admin-managed; served to the
    home page by home/differentiators/."""
    icon = models.CharField(max_length=50, default="", blank=True)      # tabler icon name
    iconBg = models.CharField(max_length=40, default="", blank=True)    # chip background colour
    iconColor = models.CharField(max_length=40, default="", blank=True) # chip icon colour
    heading = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    # variable-length list of competitor labels IB eliminates, e.g.
    # ["JustDial — unfiltered volume", "Google Ads — only website traffic"]
    eliminates = models.JSONField(default=list, blank=True)
    index = models.PositiveIntegerField(default=0)
    isActive = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app_ib"
        ordering = ["index", "id"]

    def __str__(self):
        return f"Differentiator({self.heading})"


class JoinUsCta(models.Model):
    """The home 'Join us' final CTA band. Buttons reuse the label+action shape used
    across the hero/header CTAs (action is a HomeCtaAction dict {kind,to,...}).
    Served to the home page by home/join-us/; the ordered process steps live in
    the related JoinUsStep model."""
    eyebrow = models.CharField(max_length=200, blank=True, default="")     # tag / eyebrow
    titleLead = models.CharField(max_length=200, blank=True, default="")   # heading (lead)
    titleAccent = models.CharField(max_length=200, blank=True, default="") # heading (accent/emphasis)
    sub = models.TextField(blank=True, default="")                         # description
    primaryLabel = models.CharField(max_length=100, blank=True, default="")
    primaryAction = models.JSONField(default=dict, blank=True)             # {kind,to,...}
    secondaryLabel = models.CharField(max_length=100, blank=True, default="")
    secondaryAction = models.JSONField(default=dict, blank=True)
    trustBadges = models.JSONField(default=list, blank=True)               # [{icon,label}] sub-tags
    cardHead = models.CharField(max_length=200, blank=True, default="")    # "How matching works"
    responseNote = models.CharField(max_length=300, blank=True, default="")
    isActive = models.BooleanField(default=True)
    index = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app_ib"
        ordering = ["index", "id"]

    def __str__(self):
        return f"JoinUsCta({self.titleLead}{self.titleAccent})"


class JoinUsStep(models.Model):
    """One 'how matching works' process step (key/value + display order). Variable
    number of steps per JoinUsCta."""
    joinUs = models.ForeignKey(JoinUsCta, on_delete=models.CASCADE, related_name="steps")
    key = models.CharField(max_length=40, blank=True, default="")   # bold key / step number
    value = models.TextField(blank=True, default="")                # step description
    index = models.PositiveIntegerField(default=0)                  # display order (s.no)

    class Meta:
        app_label = "app_ib"
        ordering = ["index", "id"]

    def __str__(self):
        return f"JoinUsStep({self.key})"


class ShopUpdate(models.Model):
    """A 'Shop update' card shown in the shops preview sidebar + full-details
    'Updates' tab (served by shop/<id|slug>/ via _shop_full_dict). `badge` is a
    short label like "New"/"Offer"; `color` is an optional CSS gradient/colour for
    the card."""
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="updates")
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True, default="")
    badge = models.CharField(max_length=60, blank=True, default="")   # short label e.g. "New" / "Offer"
    color = models.CharField(max_length=40, blank=True, default="")   # optional CSS gradient/colour
    displayOrder = models.PositiveIntegerField(default=0)
    isActive = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "app_ib"
        ordering = ["displayOrder", "-timestamp"]

    def __str__(self):
        return f"ShopUpdate({self.title})"


class ShopQuestion(models.Model):
    """A customer Q&A entry shown in the shops full-details popup 'Q&A' tab
    (served by shop/<id|slug>/ via _shop_full_dict). `answer` is optional (blank
    until the shop responds); `askedBy` is a short display name."""
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="questions")
    question = models.CharField(max_length=500)
    answer = models.TextField(blank=True, default="")
    askedBy = models.CharField(max_length=120, blank=True, default="")
    displayOrder = models.PositiveIntegerField(default=0)
    isActive = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "app_ib"
        ordering = ["displayOrder", "-timestamp"]

    def __str__(self):
        return f"ShopQuestion({self.question[:40]})"


class ShopImage(models.Model):
    """A gallery image for a shop, shown in the shops preview sidebar hero carousel
    + full-details popup 'Photos' tab (served by shop/<id|slug>/ via _shop_full_dict
    as a plain list of URLs). Falls back to coverImage/bannerImage when empty."""
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="images")
    imageUrl = models.TextField()
    index = models.PositiveIntegerField(default=0)
    isActive = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "app_ib"
        ordering = ["index", "timestamp"]

    def __str__(self):
        return f"ShopImage(shop={self.shop_id}, index={self.index})"
