"""
CrudController — write operations for Shop, Architect, and Review (engine entities).
Ownership is always via request.user. Permission checks reject edits by non-owners.
"""
import re as _re
from datetime import time as _time

from django.db import IntegrityError

from app_ib.Utils.EngineConfig import ENTITY_TYPE, SHOP_TYPE


_MIDNIGHT = _time(0, 0)


def _parse_hours(text):
    """"10:00 – 19:00" → (time,time,True) · "Closed" → (00:00,00:00,False) · ""/None → None.
    DaySchedule.startTime/endTime are NOT NULL, so a closed day stores midnight and is
    flagged isWorking=False (which is exactly how the detail payload reports it back).
    Tolerates any dash and H:MM / HH:MM — the wizard field is free text."""
    if not isinstance(text, str) or not text.strip():
        return None
    found = _re.findall(r"(\d{1,2}):(\d{2})", text)
    if len(found) < 2:
        return (_MIDNIGHT, _MIDNIGHT, False)  # "Closed" — or anything unparseable
    (h1, m1), (h2, m2) = found[0], found[1]
    try:
        return (_time(int(h1), int(m1)), _time(int(h2), int(m2)), True)
    except ValueError:
        return (_MIDNIGHT, _MIDNIGHT, False)


def _demo():
    assert _parse_hours("") is None and _parse_hours(None) is None
    assert _parse_hours("Closed") == (_MIDNIGHT, _MIDNIGHT, False)
    assert _parse_hours("10:00 – 19:00") == (_time(10, 0), _time(19, 0), True)
    assert _parse_hours("9:30-18:45") == (_time(9, 30), _time(18, 45), True)
    assert _parse_hours("25:00 – 19:00") == (_MIDNIGHT, _MIDNIGHT, False)

    # F2 publish gate: every gate key must be a REAL checklist key, else it silently
    # never gates (a typo would make publish accept an incomplete profile).
    from app_ib.Utils.EngineConfig import COMPLETION_CHECKLIST
    keys = {i["key"] for i in COMPLETION_CHECKLIST.BUSINESS}
    assert set(_CrudController._PUBLISH_GATE_KEYS) <= keys, "publish gate names a non-existent checklist key"
    # `category` is deliberately NOT gated — the wizard cannot set BusinessCategory
    # (vocab disjoint, see §F1), so gating on it would make publishing impossible.
    assert "category" not in _CrudController._PUBLISH_GATE_KEYS

    # F4 shop go-live: the gate is the SHOP checklist's isLiveGate items. If none were
    # flagged, publish_shop would accept every empty shop; if one were unsatisfiable,
    # no shop could ever open (that was the bug — `hours` was hardcoded False).
    from app_ib.algorithms.completion import _shop_satisfaction
    gates = [i["key"] for i in COMPLETION_CHECKLIST.SHOP if i["isLiveGate"]]
    assert gates, "shop publish would accept anything: no isLiveGate item"

    class _FakeShop:  # ponytail: a stub beats a DB fixture; pk=0 matches no plan/contact row
        pk = 0; business_id = None; business = None; city = "Mumbai"
        bannerLink = ""; coverImage = "x"; bio = "b"
    sat = _shop_satisfaction(_FakeShop())
    assert sat["location"] is True, "location must be satisfiable from the shop's own city"
    assert set(sat) == {i["key"] for i in COMPLETION_CHECKLIST.SHOP}, "shop evaluator drifted from the checklist"
    print("ok")


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
        for field in ("name", "shopType", "label", "bio", "coverImage", "bannerImage", "bannerLink",
                      "city", "state", "holidayMode", "walkInBooking", "walkInLeadTime",
                      "appointmentRequired", "amenities"):
            if field in payload:
                setattr(shop, field, payload[field])
        # F5 "Close shop": isActive is the only real status column (see publish_shop /
        # delete_shop). The CLOSE direction is a plain PATCH; the OPEN direction is
        # publish_shop's alone — it runs the live gate, so a bare PATCH must never be
        # able to set isActive=True and bypass it.
        if payload.get("isActive") is False:
            shop.isActive = False
        shop.save()
        # Gallery: payload["images"] = full ordered URL list → replace ShopImage rows
        # (dashboard "Photos & media" tab sends the whole list on every change).
        if isinstance(payload.get("images"), list):
            from app_ib.engine_models import ShopImage
            shop.images.all().delete()
            urls = [u for u in payload["images"] if isinstance(u, str) and u]
            ShopImage.objects.bulk_create([
                ShopImage(shop=shop, imageUrl=url, index=i) for i, url in enumerate(urls)
            ])
            # F4: the gallery is the only photo UI a seller has, and the completion
            # checklist gates on coverImage — so the first gallery photo becomes the
            # cover when none is set. Without this, uploading photos moved no needle.
            if urls and not shop.coverImage:
                shop.coverImage = urls[0]
                shop.save(update_fields=["coverImage"])
        # Schedules: payload["schedules"] = full day-by-day schedule list → replace all
        if isinstance(payload.get("schedules"), list):
            from interior_engine.models import ShopDaySchedule
            shop.schedules.all().delete()
            for i, row in enumerate(payload["schedules"]):
                day = row.get("day", i + 1)
                is_closed = row.get("isClosed", False) or row.get("closed", False)
                ShopDaySchedule.objects.create(
                    shop=shop, day=day,
                    openTime=row.get("openTime") or row.get("open") or None,
                    closeTime=row.get("closeTime") or row.get("close") or None,
                    isClosed=is_closed,
                )
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

    # ---- F4: shop go-live ----
    # The gate is the checklist's own isLiveGate items — i.e. exactly canGoLive. No
    # second field list (unlike publish_business, whose gate must exclude `category`).
    def publish_shop(self, user, shop_id):
        """Owner-gated shop publish (mirrors publish_business). Recomputes completion,
        then flips isActive=True or reports exactly WHICH live-gate items are unmet."""
        from app_ib.models import Shop
        from app_ib.algorithms.completion import compute_completion
        shop = Shop.objects.filter(id=shop_id).first()
        if not shop:
            raise NotFound_("shop not found")
        if shop.user_id != user.id:
            raise PermissionError_("not the shop owner")
        res = compute_completion(ENTITY_TYPE.SHOP, shop)  # persists completionPercent + canGoLive
        missing = [{"key": i["key"], "label": i["label"]} for i in res["checklist"]
                   if i["isLiveGate"] and not i["satisfied"]]
        if not missing and not shop.isActive:
            # isActive doubles as the soft-delete flag (no separate publish column exists);
            # publishing is what brings a shop back into public reads. See delete_shop.
            shop.isActive = True
            shop.save(update_fields=["isActive"])
        return {"published": not missing, "missing": missing,
                "isActive": shop.isActive, "canGoLive": res["canGoLive"],
                "completionPercent": res["percentage"]}

    def _shop_dict(self, s):
        from interior_engine.models import ShopDaySchedule
        schedules = s.schedules.all().order_by("day")
        DAY_NAMES = {1:"Monday",2:"Tuesday",3:"Wednesday",4:"Thursday",5:"Friday",6:"Saturday",7:"Sunday"}
        return {"shopId": s.id, "name": s.name, "slug": s.slug, "shopType": s.shopType,
                "label": s.label, "bio": s.bio, "coverImage": s.coverImage, "isActive": s.isActive,
                "city": s.city, "state": s.state,
                "holidayMode": s.holidayMode, "walkInBooking": s.walkInBooking,
                "walkInLeadTime": s.walkInLeadTime, "appointmentRequired": s.appointmentRequired,
                "amenities": s.amenities or [],
                "hours": [
                    {"day": DAY_NAMES.get(sc.day, ""), "open": sc.openTime.strftime("%H:%M") if sc.openTime else "",
                     "close": sc.closeTime.strftime("%H:%M") if sc.closeTime else "",
                     "closed": sc.isClosed}
                    for sc in schedules
                ],
                "rating": s.rating, "totalReviews": s.totalReviews,
                "completionPercent": s.completionPercent}

    # ------------------- Architect -------------------
    def create_architect(self, user, payload):
        from app_ib.models import Architect
        # 1 architect per user (OneToOne) — return the existing one if present.
        existing = Architect.objects.filter(user=user).first()
        if existing:
            self._link_active_plan(user, ENTITY_TYPE.ARCHITECT, existing)
            self._write_architect_relations(existing, payload)
            return self._arch_dict(existing)
        arch = Architect(
            user=user, name=payload.get("name", "").strip() or "Architect",
            city=payload.get("city", ""), state=payload.get("state", ""),
            bio=payload.get("bio", ""), coverImage=payload.get("coverImage", ""),
        )
        arch.save()
        # Buy-first: link the active ArchitectPlan (1 per user).
        self._link_active_plan(user, ENTITY_TYPE.ARCHITECT, arch)
        self._write_architect_relations(arch, payload)
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
        "brandName": "brandName", "legalName": "brandName", "whatsapp": "whatsapp", "gst": "gst",
        "since": "since", "bio": "bio", "label": "label",
        "coverImage": "coverImageUrl", "coverImageUrl": "coverImageUrl",
        "bannerImage": "bannerImageUrl", "bannerImageUrl": "bannerImageUrl",
        "bannerLink": "bannerLink", "bannerText": "bannerText",
        # F1 (2026-07-16): profile-wizard fields the persist used to discard.
        "cin": "cin", "pan": "pan", "udyam": "udyam",
        "founderName": "founderName", "teamSize": "teamSize",
        "businessModel": "businessModel", "productPriceTiers": "productPriceTiers",
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
        self._write_business_relations(user, biz, payload)
        return self._business_dict(biz)

    # ---- F1: relation-backed profile-wizard fields ----
    # Every block is guarded on the KEY BEING PRESENT in the payload — a partial
    # PATCH must never clear a relation the client didn't send.
    @staticmethod
    def _write_business_relations(user, biz, payload):
        from interior_business.models import (BusinessProfile, Location, SocialMedia,
                                              BusinessSocialMedia, DaySchedule)

        # description → BusinessProfile.about · logoUrl → BusinessProfile.primaryImageUrl
        if "description" in payload or "logoUrl" in payload:
            prof, _ = BusinessProfile.objects.get_or_create(
                business=biz, defaults={"about": "", "youtubeLink": ""})
            if payload.get("description") is not None:
                prof.about = payload["description"] or ""
            if payload.get("logoUrl") is not None:
                prof.primaryImageUrl = payload["logoUrl"] or ""
            prof.save()

        # headquartersCity / headquartersState → the business's Location row
        if "headquartersCity" in payload or "headquartersState" in payload:
            from app_ib.models import State
            loc, _ = Location.objects.get_or_create(
                business=biz, defaults={"pinCode": "", "city": "", "locationLink": ""})
            if payload.get("headquartersCity") is not None:
                loc.city = payload["headquartersCity"] or ""
            if "headquartersState" in payload:
                name = (payload.get("headquartersState") or "").strip()
                loc.locationState = State.objects.filter(name__iexact=name).first() if name else None
            loc.save()

        # publicEmail / website → the primary ContactInfo row (created on demand)
        if "publicEmail" in payload or "website" in payload:
            from interior_engine.models import ContactInfo
            c = (ContactInfo.objects.filter(business=biz).order_by("-isPrimary", "id").first()
                 or ContactInfo(business=biz, label=biz.businessName, isPrimary=True))
            if payload.get("publicEmail") is not None:
                c.email = payload["publicEmail"] or ""
            if payload.get("website") is not None:
                c.website = payload["website"] or ""
            c.save()

        # socialLinks {instagram,linkedin,facebook,youtube} → BusinessSocialMedia rows.
        # Blank link = the seller cleared it → drop the row.
        social = payload.get("socialLinks")
        if isinstance(social, dict):
            for key, name in (("instagram", "Instagram"), ("linkedin", "LinkedIn"),
                              ("facebook", "Facebook"), ("youtube", "YouTube")):
                if key not in social:
                    continue
                link = (social.get(key) or "").strip()
                sm = (SocialMedia.objects.filter(name__iexact=name).first()
                      or SocialMedia.objects.create(name=name))
                if link:
                    BusinessSocialMedia.objects.update_or_create(
                        business=biz, socialMedia=sm, defaults={"link": link})
                else:
                    BusinessSocialMedia.objects.filter(business=biz, socialMedia=sm).delete()

        # businessHours {mon..sun: "10:00 – 19:00" | "Closed" | ""} → DaySchedule rows.
        hours = payload.get("businessHours")
        if isinstance(hours, dict):
            day_num = {"mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6, "sun": 7}
            for key, num in day_num.items():
                if key not in hours:
                    continue
                parsed = _parse_hours(hours.get(key))
                if parsed is None:            # blank → the day has no schedule at all
                    DaySchedule.objects.filter(business=biz, day=num).delete()
                    continue
                start, end, working = parsed
                DaySchedule.objects.update_or_create(
                    business=biz, day=num,
                    defaults={"startTime": start, "endTime": end, "isWorking": working})

        # serviceKeywords → the seller's business-scoped AutogrowthKeyword rows.
        # Judgement call (F1): the wizard is a second writer for the same store as the
        # Autogrowth tab; the tab's plan-tier cap lives on its own add endpoint and is
        # NOT applied here — the wizard offers a fixed 6-item list, not free entry.
        kws = payload.get("serviceKeywords")
        if isinstance(kws, list):
            from interior_engine.models import AutogrowthKeyword
            terms = [t.strip() for t in kws if isinstance(t, str) and t.strip()]
            AutogrowthKeyword.objects.filter(user=user, business=biz).exclude(term__in=terms).delete()
            for t in terms:
                AutogrowthKeyword.objects.update_or_create(
                    user=user, term=t[:100], defaults={"business": biz})

    # ---- F2: publish gate ----
    # The completion checklist (COMPLETION_CHECKLIST.BUSINESS) is the single source of
    # truth for "is this profile good enough to be public" — publish reuses it rather
    # than inventing a second field list that would drift from completionPercent.
    # `category` is DELIBERATELY excluded: it is the BusinessCategory M2M, whose
    # vocabulary is disjoint from the wizard's option list (see §F1) — the wizard cannot
    # set it, so gating on it would make publishing impossible for a new seller.
    # ponytail: a tuple, not a config table — one caller, one list.
    _PUBLISH_GATE_KEYS = ("subscription", "business_name", "bio", "cover_image",
                          "contact_info", "location")

    def publish_business(self, user, business_id):
        """Owner-gated publish. Recomputes completion, then either flips isActive=True
        or reports exactly WHICH checklist items are unmet. Never raises for the
        incomplete case — the caller needs the field list, not an error string."""
        from app_ib.models import Business
        from app_ib.algorithms.completion import compute_completion
        biz = Business.objects.filter(id=business_id).first()
        if not biz:
            raise NotFound_("business not found")
        if biz.user_id != user.id:
            raise PermissionError_("not the business owner")
        res = compute_completion(ENTITY_TYPE.BUSINESS, biz)  # persists completionPercent + canGoLive
        missing = [{"key": i["key"], "label": i["label"]} for i in res["checklist"]
                   if i["key"] in self._PUBLISH_GATE_KEYS and not i["satisfied"]]
        if not missing and not biz.isActive:
            # isActive doubles as the soft-delete flag (no separate publish column exists);
            # publishing is what brings a business back into public reads.
            biz.isActive = True
            biz.save(update_fields=["isActive"])
        return {"published": not missing, "missing": missing,
                "isActive": biz.isActive, "canGoLive": res["canGoLive"],
                "completionPercent": res["percentage"]}

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
            if field in payload and payload[field] is not None:
                setattr(arch, field, payload[field])
        # slug (custom profile URL) — only accept a unique, non-empty value; a
        # collision would raise IntegrityError and fail the whole save.
        slug = (payload.get("slug") or "").strip()
        if slug and not Architect.objects.filter(slug=slug).exclude(id=arch.id).exists():
            arch.slug = slug
        arch.save()
        self._write_architect_relations(arch, payload)
        return self._arch_dict(arch)

    # ---- F6 (task 158): relation-backed architect editor fields ----
    # The 6-tab editor collects ~35 fields; the direct Architect columns hold only
    # name/bio/coverImage/state/slug. The rest route into the SAME relation models the
    # detail endpoint already reads (ContactInfo / Award / expertiseTags / ArchitectPackage),
    # mirroring the Business F1 _write_business_relations pattern. Every block is guarded on
    # the key being PRESENT — a partial PATCH never clears a relation the client didn't send.
    #
    # NO SCHEMA HOME (persisted nowhere — needs new columns, deferred per night-shift no-ask):
    #   title, firm, type, experienceYears, teamSize, serviceRadius, acceptingNewProjects,
    #   leadTime, responseTime, enquiryRoutingMode, enquiryForms, magicalWords, philosophy,
    #   linkedin, headshot, statesServed[1:]  → logged in the run ledger, not silently dropped.
    @staticmethod
    def _write_architect_relations(arch, payload):
        from interior_engine.models import ContactInfo, Award, Tag, ArchitectPackage

        # contacts → single primary ContactInfo(architect) row.
        contact_keys = ("phone", "whatsapp", "email", "website")
        if any(k in payload for k in contact_keys):
            c = (ContactInfo.objects.filter(architect=arch).order_by("-isPrimary", "id").first()
                 or ContactInfo(architect=arch, label=arch.name, isPrimary=True))
            for k in contact_keys:
                if payload.get(k) is not None:
                    setattr(c, k, payload[k] or "")
            c.save()

        # credentials (COA no. + education institutions) → Award(kind="credential").
        if "credentials" in payload:
            creds = [t.strip() for t in (payload.get("credentials") or [])
                     if isinstance(t, str) and t.strip()]
            Award.objects.filter(architect=arch, kind="credential").delete()
            for i, title in enumerate(creds):
                Award.objects.create(architect=arch, kind="credential", title=title[:255], index=i)

        # awards (free text, one per line) → Award(kind="award").
        if "awards" in payload:
            aw = payload.get("awards")
            items = aw if isinstance(aw, list) else ([aw] if aw else [])
            titles = [t.strip() for t in items if isinstance(t, str) and t.strip()]
            Award.objects.filter(architect=arch, kind="award").delete()
            for i, title in enumerate(titles):
                Award.objects.create(architect=arch, kind="award", title=title[:255], index=i)

        # expertise (specialisations + design styles) → expertiseTags M2M.
        # Resolve tags by value OR slug before creating — Tag.getOrCreateFromText matches
        # on value only, so a normalized value whose slug collides with a different
        # existing tag raises a UNIQUE(slug) IntegrityError and would abort the save.
        if "expertise" in payload:
            from app_ib.algorithms.text import normalize
            from django.utils.text import slugify
            resolved = []
            for x in (payload.get("expertise") or []):
                if not isinstance(x, str) or not x.strip():
                    continue
                value = normalize(x, strip_stopwords=True)
                if not value:
                    continue
                slug = slugify(value) or value
                tag = (Tag.objects.filter(value=value).first()
                       or Tag.objects.filter(slug=slug).first()
                       or Tag.objects.create(value=value, slug=slug))
                resolved.append(tag)
            arch.expertiseTags.set(resolved)

        # startingPrice → primary ArchitectPackage.fromValue (detail price card).
        if "startingPrice" in payload:
            digits = "".join(ch for ch in str(payload.get("startingPrice") or "") if ch.isdigit())
            pkg = arch.packages.order_by("index", "id").first() or ArchitectPackage(architect=arch, index=0)
            pkg.fromValue = int(digits) if digits else None
            pkg.save()

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
                        # Already on the model and already set — it just never reached the UI.
                        "isVerifiedPurchase": r.isVerifiedPurchase,
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
