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
        """Link the newest ACTIVE, still-unlinked plan of this entityType to the entity
        (fills the nullable FK from Prompt 5). Buy-first gate: raise Conflict_ if the user
        holds no such plan — the entity tab only opens after a plan is bought."""
        from app_ib.models import BusinessPlan, ShopPlan, ArchitectPlan
        if entity_type == ENTITY_TYPE.SHOP:
            plan = (ShopPlan.objects.filter(user=user, isActive=True, shop__isnull=True)
                    .order_by("-timestamp").first())
            fk = "shop"
        elif entity_type == ENTITY_TYPE.ARCHITECT:
            plan = (ArchitectPlan.objects.filter(user=user, isActive=True, architect__isnull=True)
                    .order_by("-timestamp").first())
            fk = "architect"
        else:
            plan = (BusinessPlan.objects.filter(user=user, isActive=True, business__isnull=True)
                    .order_by("-timestamp").first())
            fk = "business"
        if not plan:
            raise Conflict_(f"No active {entity_type} subscription to link — buy a plan first")
        setattr(plan, fk, entity)
        plan.save()
        return plan
        # NOTE: frontend entitlement gating reads my/plans/.activeEntityTypes

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
        for field in ("name", "shopType", "bio", "coverImage", "bannerImage", "bannerLink"):
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
        shop.delete()
        return True

    def _shop_dict(self, s):
        return {"shopId": s.id, "name": s.name, "slug": s.slug, "shopType": s.shopType,
                "bio": s.bio, "coverImage": s.coverImage, "isActive": s.isActive,
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
                "brandName": getattr(b, "brandName", ""), "gst": getattr(b, "gst", "")}

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
                        "reviewerAvatarUrl": (profile.profileImageUrl or "") if profile else ""})
        return out

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
