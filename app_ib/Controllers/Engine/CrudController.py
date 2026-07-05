"""
CrudController — write operations for Shop, Architect, and Review (engine entities).
Ownership is always via request.user. Permission checks reject edits by non-owners.
"""
from django.db import IntegrityError

from app_ib.Utils.EngineConfig import ENTITY_TYPE, SHOP_TYPE


class PermissionError_(Exception):
    pass


class NotFound_(Exception):
    pass


class Conflict_(Exception):
    pass


class _CrudController:

    # ------------------- Buy-first: link entity to an active, unlinked plan -------------------
    def _link_active_plan(self, user, entity_type, entity):
        """Link the entity to the plan that authorizes it (fills the nullable FK from
        Prompt 5). Delegates to the EntitlementService so a dedicated per-type plan OR an
        automation BUNDLE (which grants all three) both satisfy the buy-first gate. Raises
        Conflict_ if the user holds no active plan granting this entity type."""
        from app_ib.Controllers.Plans.EntitlementService import ENTITLEMENT_SERVICE
        return ENTITLEMENT_SERVICE.link_entity(user, entity_type, entity)
        # NOTE: frontend entitlement gating reads my/plans/.entitledEntityTypes (tabs)
        #       and .activeEntityTypes (publishing).

    # ------------------- Shop -------------------
    def create_shop(self, user, payload):
        from app_ib.models import Shop, Business
        business = None
        if payload.get("businessId"):
            business = Business.objects.filter(id=payload["businessId"]).first()
        shop = Shop(
            user=user, business=business,
            name=payload.get("name", "").strip() or "Untitled Shop",
            shopType=payload.get("shopType", SHOP_TYPE.OFFLINE),
            bio=payload.get("bio", ""), coverImage=payload.get("coverImage", ""),
            bannerImage=payload.get("bannerImage", ""), bannerLink=payload.get("bannerLink", ""),
            city=payload.get("city", ""), state=payload.get("state", ""),
        )
        shop.save()
        # Buy-first: every shop must be backed by a paid ShopPlan (Prompt 7/8).
        self._link_active_plan(user, ENTITY_TYPE.SHOP, shop)
        return self._shop_dict(shop)

    def update_shop(self, user, shop_id, payload):
        from app_ib.models import Shop
        shop = Shop.objects.filter(id=shop_id).first()
        if not shop:
            raise NotFound_("shop not found")
        if shop.user_id != user.id:
            raise PermissionError_("not the shop owner")
        for field in ("name", "shopType", "bio", "coverImage", "bannerImage", "bannerLink",
                      "city", "state"):
            if field in payload:
                setattr(shop, field, payload[field])
        shop.save()
        return self._shop_dict(shop)

    def delete_shop(self, user, shop_id):
        from app_ib.models import Shop
        shop = Shop.objects.filter(id=shop_id).first()
        if not shop:
            raise NotFound_("shop not found")
        if shop.user_id != user.id:
            raise PermissionError_("not the shop owner")
        # Soft delete — keep the row (reviews/leads/plan link stay intact) but hide it
        # from public reads + owner lists (get_shop / my_shops already filter isActive).
        shop.isActive = False
        shop.save(update_fields=["isActive"])
        return True

    def _shop_dict(self, s):
        return {"shopId": s.id, "name": s.name, "slug": s.slug, "shopType": s.shopType,
                "bio": s.bio, "coverImage": s.coverImage, "isActive": s.isActive,
                "city": s.city, "state": s.state,
                "rating": s.rating, "totalReviews": s.totalReviews,
                "completionPercent": s.completionPercent}

    # ------------------- Architect -------------------
    def create_architect(self, user, payload):
        from app_ib.models import Architect
        # 1 architect per user (OneToOne) — return the existing one if present.
        existing = Architect.objects.filter(user=user).first()
        if existing:
            self._link_active_plan(user, ENTITY_TYPE.ARCHITECT, existing)
            return self._arch_dict(existing)
        arch = Architect(
            user=user, name=payload.get("name", "").strip() or "Architect",
            city=payload.get("city", ""), state=payload.get("state", ""),
            bio=payload.get("bio", ""), coverImage=payload.get("coverImage", ""),
        )
        arch.save()
        # Buy-first: link the active ArchitectPlan (1 per user).
        self._link_active_plan(user, ENTITY_TYPE.ARCHITECT, arch)
        return self._arch_dict(arch)

    # ------------------- Business (engine create, buy-first) -------------------
    def create_business(self, user, payload):
        """Create (or fetch) the user's Business and link the active BusinessPlan.
        Business is 1:1 with the user; tolerates partial/optional fields."""
        from app_ib.models import Business
        existing = Business.objects.filter(user=user).first()
        if existing:
            self._link_active_plan(user, ENTITY_TYPE.BUSINESS, existing)
            return self._business_dict(existing)
        biz = Business(
            user=user,
            businessName=(payload.get("name") or payload.get("businessName") or "My Business").strip(),
        )
        for src, dst in (("brandName", "brandName"), ("whatsapp", "whatsapp"),
                         ("gst", "gst"), ("since", "since")):
            if payload.get(src):
                setattr(biz, dst, payload[src])
        biz.save()
        self._link_active_plan(user, ENTITY_TYPE.BUSINESS, biz)
        return self._business_dict(biz)

    def _business_dict(self, b):
        return {"businessId": b.id, "name": b.businessName,
                "brandName": getattr(b, "brandName", ""), "gst": getattr(b, "gst", ""),
                "isActive": b.isActive}

    # Field map: incoming v3 payload key -> Business model attribute. Only keys
    # present in the payload are written (PATCH-friendly partial updates).
    _BUSINESS_FIELD_MAP = {
        "name": "businessName", "businessName": "businessName",
        "brandName": "brandName", "whatsapp": "whatsapp", "gst": "gst",
        "since": "since", "bio": "bio", "label": "label",
        "coverImage": "coverImageUrl", "coverImageUrl": "coverImageUrl",
        "bannerImage": "bannerImageUrl", "bannerImageUrl": "bannerImageUrl",
        "bannerLink": "bannerLink", "bannerText": "bannerText",
    }

    def update_business(self, user, business_id, payload):
        from app_ib.models import Business
        biz = Business.objects.filter(id=business_id).first()
        if not biz:
            raise NotFound_("business not found")
        if biz.user_id != user.id:
            raise PermissionError_("not the business owner")
        for key, attr in self._BUSINESS_FIELD_MAP.items():
            if key in payload and payload[key] is not None:
                setattr(biz, attr, payload[key])
        biz.save()
        return self._business_dict(biz)

    def delete_business(self, user, business_id):
        from app_ib.models import Business
        biz = Business.objects.filter(id=business_id).first()
        if not biz:
            raise NotFound_("business not found")
        if biz.user_id != user.id:
            raise PermissionError_("not the business owner")
        # Soft delete — reversible; reads filter isActive (see get_business / profile).
        biz.isActive = False
        biz.save(update_fields=["isActive"])
        return True

    def update_architect(self, user, arch_id, payload):
        from app_ib.models import Architect
        arch = Architect.objects.filter(id=arch_id).first()
        if not arch:
            raise NotFound_("architect not found")
        if arch.user_id != user.id:
            raise PermissionError_("not the architect owner")
        for field in ("name", "city", "state", "bio", "coverImage"):
            if field in payload:
                setattr(arch, field, payload[field])
        arch.save()
        return self._arch_dict(arch)

    def delete_architect(self, user, arch_id):
        from app_ib.models import Architect
        arch = Architect.objects.filter(id=arch_id).first()
        if not arch:
            raise NotFound_("architect not found")
        if arch.user_id != user.id:
            raise PermissionError_("not the architect owner")
        # Soft delete — reversible; get_architect / my_architects filter isActive.
        arch.isActive = False
        arch.save(update_fields=["isActive"])
        return True

    def _arch_dict(self, a):
        return {"architectId": a.id, "name": a.name, "slug": a.slug, "city": a.city,
                "state": a.state, "bio": a.bio, "rating": a.rating,
                "totalReviews": a.totalReviews, "completionPercent": a.completionPercent}

    # ------------------- Review -------------------
    _REVIEW_FK = {
        ENTITY_TYPE.BUSINESS: "business", ENTITY_TYPE.SHOP: "shop",
        ENTITY_TYPE.PRODUCT: "product", ENTITY_TYPE.SERVICE: "service",
        ENTITY_TYPE.ARCHITECT: "architect",
    }

    def create_review(self, user, payload):
        from app_ib.models import Review
        from app_ib.algorithms.helpers import get_model
        et = payload.get("entityType")
        fk = self._REVIEW_FK.get(et)
        if not fk:
            raise NotFound_("unsupported entity type for review")
        target = get_model(et).objects.filter(id=payload.get("objectId")).first()
        if not target:
            raise NotFound_(f"{et} not found")
        rating = int(payload.get("rating", 0))
        if not 1 <= rating <= 5:
            raise Conflict_("rating must be 1-5")
        if Review.objects.filter(reviewer=user, **{fk: target}).exists():
            raise Conflict_("you already reviewed this")
        review = Review.objects.create(
            reviewer=user, rating=rating, title=payload.get("title", ""),
            body=payload.get("body", ""), **{fk: target})
        self._recompute_one(et, target)
        return {"reviewId": review.id, "rating": review.rating}

    def update_review(self, user, review_id, payload):
        from app_ib.models import Review
        review = Review.objects.filter(id=review_id).first()
        if not review:
            raise NotFound_("review not found")
        if review.reviewer_id != user.id:
            raise PermissionError_("not your review")
        if "rating" in payload:
            r = int(payload["rating"])
            if not 1 <= r <= 5:
                raise Conflict_("rating must be 1-5")
            review.rating = r
        for f in ("title", "body"):
            if f in payload:
                setattr(review, f, payload[f])
        review.save()
        return {"reviewId": review.id, "rating": review.rating}

    def delete_review(self, user, review_id):
        from app_ib.models import Review
        review = Review.objects.filter(id=review_id).first()
        if not review:
            raise NotFound_("review not found")
        if review.reviewer_id != user.id:
            raise PermissionError_("not your review")
        review.isDeleted = True
        review.save(update_fields=["isDeleted"])
        return True

    def mark_helpful(self, review_id):
        from app_ib.models import Review
        from django.db.models import F
        Review.objects.filter(id=review_id).update(helpfulCount=F("helpfulCount") + 1)
        review = Review.objects.filter(id=review_id).first()
        if not review:
            raise NotFound_("review not found")
        return {"reviewId": review.id, "helpfulCount": review.helpfulCount}

    def list_reviews(self, entity_type, object_id):
        from app_ib.models import Review
        fk = self._REVIEW_FK.get(entity_type)
        if not fk:
            raise NotFound_("unsupported entity type")
        rows = Review.objects.filter(**{f"{fk}_id": object_id, "isDeleted": False, "isApproved": True}) \
            .select_related("reviewer", "reviewer__user_profile") \
            .order_by("-timestamp")[:100]
        out = []
        for r in rows:
            # Additive display fields for the v3 detail pages. Never expose the
            # raw username (it is an email) — profile name, else its local part.
            profile = getattr(r.reviewer, "user_profile", None) if r.reviewer_id else None
            name = (profile.name or "").strip() if profile else ""
            if not name and r.reviewer_id:
                name = (r.reviewer.username or "").split("@")[0]
            out.append({"reviewId": r.id, "rating": r.rating, "title": r.title, "body": r.body,
                        "reviewer": r.reviewer_id, "helpfulCount": r.helpfulCount,
                        "timestamp": r.timestamp.isoformat(),
                        "reviewerName": name or "User",
                        "reviewerAvatarUrl": (profile.profileImageUrl or "") if profile else "",
                        # Seller reply + attribute tags (task 64).
                        "reply": ({"text": r.replyText, "at": r.replyAt.isoformat() if r.replyAt else None}
                                  if r.replyText else None),
                        "attributeTags": r.attributeTags or []})
        return out

    def _review_owner_id(self, review):
        """The user id that owns the entity a review targets (the seller who may reply)."""
        if review.business_id:
            return getattr(review.business, "user_id", None)
        if review.shop_id:
            return getattr(review.shop, "user_id", None)
        if review.architect_id:
            return getattr(review.architect, "user_id", None)
        if review.product_id:
            return getattr(getattr(review.product, "business", None), "user_id", None)
        if review.service_id:
            return getattr(getattr(review.service, "business", None), "user_id", None)
        return None

    def _sanitize_tags(self, raw):
        """Normalize attribute tags to [{id,label,kind}] — kind constrained to the chip set."""
        tags = []
        for t in (raw or [])[:20]:
            if isinstance(t, str):
                label = t.strip()
                if label:
                    tags.append({"id": label.lower().replace(" ", "-"), "label": label, "kind": "neutral"})
                continue
            if not isinstance(t, dict):
                continue
            label = (t.get("label") or "").strip()
            if not label:
                continue
            kind = t.get("kind") if t.get("kind") in ("positive", "neutral", "negative") else "neutral"
            tags.append({"id": (t.get("id") or label.lower().replace(" ", "-")), "label": label, "kind": kind})
        return tags

    def reply_to_review(self, user, review_id, text, tags=None):
        """Post/replace the seller reply on one review, and optionally set attribute
        tags. Only the owner of the reviewed entity may reply (task 64)."""
        from app_ib.models import Review
        from django.utils import timezone
        review = (Review.objects
                  .filter(id=review_id, isDeleted=False)
                  .select_related("business", "shop", "architect", "product", "service")
                  .first())
        if not review:
            raise NotFound_("review not found")
        owner_id = self._review_owner_id(review)
        if not owner_id or owner_id != user.id:
            raise PermissionError_("only the reviewed business owner can reply")
        text = (text or "").strip()
        update_fields = []
        if text:
            review.replyText = text
            review.replyAt = timezone.now()
            update_fields += ["replyText", "replyAt"]
        if tags is not None:
            review.attributeTags = self._sanitize_tags(tags)
            update_fields += ["attributeTags"]
        if not update_fields:
            raise Conflict_("nothing to update: provide reply text or tags")
        review.save(update_fields=update_fields)
        return {"reviewId": review.id,
                "reply": ({"text": review.replyText,
                           "at": review.replyAt.isoformat() if review.replyAt else None}
                          if review.replyText else None),
                "attributeTags": review.attributeTags or []}

    def _recompute_one(self, entity_type, target):
        """Immediately refresh one entity's rating after a write (batch job also covers it)."""
        from app_ib.models import Review
        from app_ib.algorithms.aggregation import _percent_breakdown
        fk = self._REVIEW_FK[entity_type]
        reviews = Review.objects.filter(**{fk: target, "isDeleted": False, "isApproved": True})
        total = reviews.count()
        rating_field = "ratingValue" if hasattr(target, "ratingValue") else "rating"
        if total == 0:
            setattr(target, rating_field, 0.0)
            target.totalReviews, target.ratingBreakdown = 0, {}
        else:
            star = {i: 0 for i in range(1, 6)}
            s = 0
            for r in reviews.values("rating"):
                star[max(1, min(5, r["rating"]))] += 1
                s += r["rating"]
            setattr(target, rating_field, round(s / total, 2))
            target.totalReviews = total
            target.ratingBreakdown = _percent_breakdown(star, total)
        target.save(update_fields=[rating_field, "totalReviews", "ratingBreakdown"])


CRUD_CONTROLLER = _CrudController()
