"""ponytail self-check: verified-business score invariants (proximity boost,
descending order, verified-preferred, never-empty). Uses the live dev DB.
Run from backend root: python app_ib/tests/test_verified_businesses.py
"""
import os
import sys

if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    os.environ["DJANGO_SETTINGS_MODULE"] = "interior_bazzar.settings"
    import django
    django.setup()

from app_ib.Controllers.Engine.HomeController import HOME_CONTROLLER


def test_ranking_invariants():
    rows = HOME_CONTROLLER.verified_businesses(limit=12)
    assert rows, "verified-businesses must never be empty when businesses exist"
    scores = [r["verifiedScore"] for r in rows]
    assert scores == sorted(scores, reverse=True), "scores must be descending"
    # verified-preferred: with enough verified businesses, the top result is verified
    assert rows[0]["isVerified"] is True


def test_proximity_boost_raises_matching_city():
    rows = HOME_CONTROLLER.verified_businesses(limit=12)
    target = next((r for r in rows if r.get("city")), None)
    assert target, "need a business with a city to test proximity"
    city = target["city"]
    without = {r["id"]: r["verifiedScore"] for r in HOME_CONTROLLER.verified_businesses(limit=50)}
    withcity = {r["id"]: r["verifiedScore"] for r in HOME_CONTROLLER.verified_businesses(city=city, limit=50)}
    # same-city businesses must score strictly higher once their city is supplied
    assert withcity[target["id"]] > without[target["id"]], "proximity boost did not raise the same-city business"


if __name__ == "__main__":
    test_ranking_invariants()
    test_proximity_boost_raises_matching_city()
    print("ok")
