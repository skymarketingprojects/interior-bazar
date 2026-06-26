"""AI Specialization — auto-generated "what they specialize in" cards.

Two sequential mechanisms (see CLAUDE.md / the feature plan):
  1. Bootstrap: a one-time, debounced SpecializationJob creates the FIRST
     BusinessSpecialization ~1 hr after the owner starts populating the business.
     Re-arming the timer (enqueue_bootstrap_refresh) only happens while no
     specialization exists yet.
  2. Drift cron: once a specialization exists, scan_specialization_drift regenerates
     it ONLY when the business+profile TEXT has changed >= ALGO.SPEC_CHANGE_THRESHOLD
     vs. the stored snapshot. Products/services do NOT count toward the gate.

All functions degrade gracefully — generation falls back to template cards, and
enqueue never raises into the caller (signals).
"""
import difflib
import hashlib

from django.core.cache import cache
from django.utils import timezone

from app_ib.Utils.EngineConfig import ALGO
from app_ib.Utils.StaticValues import SPEC_JOB_STATUS, SPEC_SOURCE
from app_ib.algorithms import ai
from app_ib.algorithms.text import normalize


# ---------------------------------------------------------------------------
# Canonical profile text + drift measurement (business + profile text ONLY)
# ---------------------------------------------------------------------------
def _canonical_profile_text(business):
    """Normalized text that the 25% drift gate is measured on. Business + profile
    text only — products/services are deliberately excluded."""
    parts = [
        business.businessName or "",
        business.brandName or "",
        business.bio or "",
        str(business.since or ""),
    ]
    profile = getattr(business, "business_profile", None)
    if profile is not None:
        parts.append(profile.about or "")
    parts += [s.lable for s in business.businessSegment.all()]
    parts += [c.lable for c in business.businessCategory.all()]
    return normalize(" ".join(p for p in parts if p))


def _hash(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _change_ratio(old, new):
    """Fraction (0-1) of the canonical text that changed. 0 = identical."""
    if not old and not new:
        return 0.0
    if not old or not new:
        return 1.0
    ratio = difflib.SequenceMatcher(None, old.split(), new.split()).ratio()
    return 1.0 - ratio


# ---------------------------------------------------------------------------
# Bootstrap enqueue (debounced, one-time)
# ---------------------------------------------------------------------------
def enqueue_bootstrap_refresh(business, reason=""):
    """Arm/re-arm the one-time bootstrap job for a business. No-op once a
    BusinessSpecialization already exists (ongoing regen is the drift cron's job).
    Never raises — callers are post_save signals."""
    from app_ib.engine_models import BusinessSpecialization, SpecializationJob
    try:
        if business is None or business.pk is None:
            return None
        if BusinessSpecialization.objects.filter(business=business).exists():
            return None  # bootstrap already done
        run_at = timezone.now() + timezone.timedelta(seconds=ALGO.SPEC_DEBOUNCE_SECONDS)
        job, created = SpecializationJob.objects.get_or_create(
            business=business, status=SPEC_JOB_STATUS.pending,
            defaults={"scheduledAt": run_at, "reason": reason},
        )
        if not created:
            # Reschedule the existing pending job ("remove old task, create new 1 hr").
            job.scheduledAt = run_at
            job.reason = reason or job.reason
            job.save(update_fields=["scheduledAt", "reason", "updatedAt"])
        return job
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Generation worker (used by both the bootstrap processor and the drift cron)
# ---------------------------------------------------------------------------
def run_specialization_for_business(business, force=False):
    """Generate or refresh a business's specialization cards, applying the 25% gate
    when a specialization already exists. Returns a small status dict."""
    from app_ib.engine_models import BusinessSpecialization

    current_text = _canonical_profile_text(business)
    spec = BusinessSpecialization.objects.filter(business=business).first()

    if spec is None:
        decision = "bootstrap"
    elif force:
        decision = "forced"
    else:
        ratio = _change_ratio(spec.profileSnapshot, current_text)
        if ratio >= ALGO.SPEC_CHANGE_THRESHOLD:
            decision = "drift"
        else:
            return {"generated": False, "reason": "below_threshold",
                    "changeRatio": round(ratio, 3)}

    cards, used_gemini = _generate_cards(business)

    BusinessSpecialization.objects.update_or_create(
        business=business,
        defaults={
            "cards": cards,
            "profileSnapshot": current_text,
            "snapshotHash": _hash(current_text),
            "source": SPEC_SOURCE.gemini if used_gemini else SPEC_SOURCE.template,
        },
    )
    # Invalidate the cached business detail (mirrors app_ib/signals.py).
    cache.delete(f"cache:business:{business.id}")
    return {"generated": True, "reason": decision, "cards": len(cards),
            "source": SPEC_SOURCE.gemini if used_gemini else SPEC_SOURCE.template}


def _generate_cards(business):
    """Gather context and call the AI generator. Returns (cards, used_gemini)."""
    category = ", ".join([c.lable for c in business.businessCategory.all()][:3])
    if not category:
        category = ", ".join([s.lable for s in business.businessSegment.all()][:3])
    profile = getattr(business, "business_profile", None)
    about = (profile.about if profile is not None else "") or ""
    location = _business_location(business)
    product_titles = list(
        business.products.filter(isActive=True).values_list("title", flat=True)[:20]
    ) if hasattr(business, "products") else []
    service_titles = list(
        business.services.filter(isActive=True).values_list("title", flat=True)[:20]
    ) if hasattr(business, "services") else []

    return ai.generate_specialization_cards(
        business_name=business.businessName or "",
        category=category,
        bio=business.bio or "",
        about=about,
        product_titles=product_titles,
        service_titles=service_titles,
        location=location,
        since=str(business.since or ""),
    )


def _business_location(business):
    loc = getattr(business, "business_location", None)
    if loc is None:
        return ""
    city = getattr(loc, "city", "") or ""
    state = getattr(loc, "state", "") or ""
    return ", ".join([p for p in (city, state) if p])
