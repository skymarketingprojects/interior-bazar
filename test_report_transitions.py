"""Runnable check for the reported-listings 4-state machine (task 21).

    cd interior-bazzar-backend/interior-bazar && python test_report_transitions.py

Asserts the legal walk open→reviewing→actioned→dismissed works and an illegal
jump (actioned→open) is rejected. Plain asserts (ponytail), cleans up its row.
"""
import os
import asyncio
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interior_bazzar.settings")
django.setup()

from interior_admin.models import ListingReport
from interior_admin.Controllers.Reports.ReportsController import REPORTS_CONTROLLER


async def demo():
    r = await ListingReport.objects.acreate(targetType="business", targetId="1", reason="test", status="open")
    try:
        assert (await REPORTS_CONTROLLER.Transition(r.id, "reviewing")).response, "open→reviewing should pass"
        assert (await REPORTS_CONTROLLER.Transition(r.id, "actioned")).response, "reviewing→actioned should pass"

        # illegal: actioned → open must be rejected
        bad = await REPORTS_CONTROLLER.Transition(r.id, "open")
        assert not bad.response, "actioned→open must be rejected"
        assert bad.data.get("message") == "Invalid transition", bad.data

        # illegal skip already covered; terminal move must still work
        assert (await REPORTS_CONTROLLER.Transition(r.id, "dismissed")).response, "actioned→dismissed should pass"

        # dismissed is terminal
        term = await REPORTS_CONTROLLER.Transition(r.id, "actioned")
        assert not term.response, "dismissed is terminal — no further transitions"

        print("test_report_transitions: all assertions passed")
    finally:
        await ListingReport.objects.filter(id=r.id).adelete()


if __name__ == "__main__":
    asyncio.run(demo())
