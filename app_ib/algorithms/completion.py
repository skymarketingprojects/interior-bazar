"""Algorithm 5 — Profile Completion. Computes completionPercent + canGoLive for
Business / Shop / Architect from a weighted checklist. canGoLive is True only
when every isLiveGate item is satisfied (independent of percentage).
"""
from app_ib.Utils.EngineConfig import ENTITY_TYPE, COMPLETION_CHECKLIST


def _business_satisfaction(obj):
    from app_ib.models import ContactInfo
    has_plan = obj.business_plan.filter(isActive=True).exists() if hasattr(obj, "business_plan") else False
    has_contact = bool(obj.whatsapp) or ContactInfo.objects.filter(business=obj).exists()
    has_location = hasattr(obj, "business_location") and getattr(obj, "business_location", None) is not None \
        and bool(getattr(obj.business_location, "city", ""))
    return {
        "subscription": has_plan,
        "business_name": bool(obj.businessName),
        "bio": bool(obj.bio),
        "cover_image": bool(obj.coverImageUrl),
        "category": obj.businessCategory.exists(),
        "contact_info": has_contact,
        "location": has_location,
    }


def _architect_satisfaction(obj):
    has_plan = False  # architects have no plan model yet; treated as not-subscribed
    return {
        "subscription": has_plan,
        "portfolio": obj.businesses.exists() if hasattr(obj, "businesses") else False,
        "bio": bool(obj.bio),
        "cover_image": bool(obj.coverImage),
        "city_state": bool(obj.city) and bool(obj.state),
    }


def _shop_satisfaction(obj):
    from app_ib.models import ContactInfo
    has_plan = bool(obj.business and obj.business.business_plan.filter(isActive=True).exists()) \
        if obj.business_id else False
    has_contact = ContactInfo.objects.filter(shop=obj).exists()
    return {
        "subscription": has_plan,
        "location": bool(obj.bannerLink) or has_contact,   # proxy: no Location.shop FK in v1
        "contact_info": has_contact,
        "cover_image": bool(obj.coverImage),
        "hours": False,                                     # DaySchedule.shop not wired in v1
        "bio": bool(obj.bio),
    }


_EVALUATOR = {
    ENTITY_TYPE.BUSINESS: _business_satisfaction,
    ENTITY_TYPE.ARCHITECT: _architect_satisfaction,
    ENTITY_TYPE.SHOP: _shop_satisfaction,
}


def compute_completion(entity_type, obj):
    """Return (percentage, canGoLive, checklist, itemsLeft) and persist on obj."""
    checklist_def = COMPLETION_CHECKLIST.BY_ENTITY[entity_type]
    sat = _EVALUATOR[entity_type](obj)

    earned = 0
    can_go_live = True
    checklist, items_left = [], []
    for item in checklist_def:
        ok = bool(sat.get(item["key"], False))
        if ok:
            earned += item["weight"]
        else:
            items_left.append(item["key"])
            if item["isLiveGate"]:
                can_go_live = False
        checklist.append({**item, "satisfied": ok})

    total_weight = sum(i["weight"] for i in checklist_def) or 1
    percentage = int(round(earned * 100.0 / total_weight))

    obj.completionPercent = percentage
    if hasattr(obj, "canGoLive"):
        obj.canGoLive = can_go_live
        obj.save(update_fields=["completionPercent", "canGoLive"])
    else:
        obj.save(update_fields=["completionPercent"])
    return {"percentage": percentage, "canGoLive": can_go_live,
            "checklist": checklist, "itemsLeft": items_left}


def recompute_all_completion():
    from app_ib.algorithms.helpers import get_model
    n = 0
    for entity_type in ENTITY_TYPE.COMPLETION:
        for obj in get_model(entity_type).objects.all():
            compute_completion(entity_type, obj)
            n += 1
    return n
