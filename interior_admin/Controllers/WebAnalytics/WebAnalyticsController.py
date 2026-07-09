from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from asgiref.sync import sync_to_async
from django.db.models import Count, Q
from django.db.models.functions import TruncDate

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.models import CustomUser, Business, LeadQuery, Blog

# NOTE: Sessions / unique visitors / avg session duration / bounce rate / external
# traffic-by-source (Organic/Ads/GMB/Social) are DEFERRED — there is no event store.
# They need a WebEvent(sessionId, visitorId, eventType, path, referrerSource,
# createdAt) model + a public-SPA beacon; that's a separate task. Everything below
# is ENQUIRY-derived from LeadQuery (the closest real data) — never fabricated.


def _parse_date(d: Optional[str]):
    if not d:
        return None
    try:
        return datetime.fromisoformat(d).date()
    except ValueError:
        try:
            return datetime.strptime(d, "%Y-%m-%d").date()
        except ValueError:
            return None


class WebAnalyticsController:
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Get(cls, start: str = None, end: str = None) -> Tuple[bool, Dict[str, Any]]:
        startD = _parse_date(start)
        endD = _parse_date(end)
        rangeQ = Q()
        if startD:
            rangeQ &= Q(timestamp__date__gte=startD)
        if endD:
            rangeQ &= Q(timestamp__date__lte=endD)
        leads = LeadQuery.objects.filter(rangeQ)

        total = await leads.acount()

        # "Traffic by source" analogue — enquiries grouped by their capture channel.
        src_rows = await sync_to_async(list)(
            leads.values("sourceChannel").annotate(c=Count("id")).order_by("-c"))
        leadsBySource = [{"label": (r["sourceChannel"] or "Direct/unknown"), "count": r["c"]} for r in src_rows]

        # "Where the enquiry was generated" — grouped by the origin entity type.
        origin_rows = await sync_to_async(list)(
            leads.values("originType").annotate(c=Count("id")).order_by("-c"))
        leadsByOrigin = [{"label": (r["originType"] or "unknown"), "count": r["c"]} for r in origin_rows]

        # Post-lead funnel. Won token confirmed = LeadQuery.stage == 'won'
        # (HomeController conversion = won/total).
        responded = await leads.filter(respondedAt__isnull=False).acount()
        won = await leads.filter(stage="won").acount()
        funnel = [
            {"label": "Qualified enquiry", "count": total},
            {"label": "Seller responded", "count": responded},
            {"label": "Won", "count": won},
        ]

        daily_rows = await sync_to_async(list)(
            leads.annotate(day=TruncDate("timestamp")).values("day").annotate(c=Count("id")).order_by("day"))
        enquiriesDaily = [{"date": r["day"].isoformat() if r["day"] else None, "count": r["c"]} for r in daily_rows]

        return True, {
            # headline platform totals (unchanged)
            "totalUsers": await CustomUser.objects.filter(is_delete=False).acount(),
            "buyers": await CustomUser.objects.filter(type="user", is_delete=False).acount(),
            "businesses": await Business.objects.acount(),
            "verifiedBusinesses": await Business.objects.filter(isVerified=True).acount(),
            "leads": await LeadQuery.objects.acount(),
            "blogs": await Blog.objects.acount(),
            # enquiry-derived analytics for the selected range
            "rangeTotal": total,
            "leadsBySource": leadsBySource,
            "leadsByOrigin": leadsByOrigin,
            "funnel": funnel,
            "enquiriesDaily": enquiriesDaily,
            "start": startD.isoformat() if startD else None,
            "end": endD.isoformat() if endD else None,
        }


WEB_ANALYTICS_CONTROLLER = WebAnalyticsController()
