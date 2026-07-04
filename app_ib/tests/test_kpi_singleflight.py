"""ponytail self-check: trending/kpi 10-min cache + single-flight. While a
recompute lock is held and the fresh cache is expired, concurrent callers must
serve the stale copy WITHOUT recomputing (no DB stampede). Run from backend root:
    python app_ib/tests/test_kpi_singleflight.py
"""
import os
import sys
import time

if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    os.environ["DJANGO_SETTINGS_MODULE"] = "interior_bazzar.settings"
    import django
    django.setup()

from app_ib.Utils.SafeCache import safe_cache as cache
from app_ib.Controllers.Engine.GapsController import trending_kpi


def test_cache_and_single_flight():
    for k in ("trending:kpi", "trending:kpi:lock", "trending:kpi:stale"):
        cache.delete(k)

    fresh = trending_kpi()
    assert "verifiedBusinesses" in fresh, "kpi must include proof-band stats"
    assert cache.get("trending:kpi") is not None, "fresh copy must be cached (10m)"
    assert cache.get("trending:kpi:stale") is not None, "stale copy must be kept"

    # simulate another request already recomputing: lock held + fresh cache gone
    cache.delete("trending:kpi")
    cache.set("trending:kpi:lock", 1, 30)
    t = time.time()
    served = trending_kpi()
    elapsed = time.time() - t
    assert served == fresh, "must serve the stale copy while a recompute is in flight"
    assert elapsed < 0.05, "stale serve must be fast (no DB recompute)"
    cache.delete("trending:kpi:lock")


if __name__ == "__main__":
    test_cache_and_single_flight()
    print("ok")
