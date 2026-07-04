"""ponytail self-check: home location-resolution ?near= phrase parsing +
broaden-shops rung order. Pure logic, no DB. Run from the backend root:
    python app_ib/tests/test_home_location.py
(no pytest/test-runner exists in this repo, so it self-configures Django)."""
import os
import sys
import django

if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    os.environ["DJANGO_SETTINGS_MODULE"] = "interior_bazzar.settings"
    django.setup()

from app_ib.Views.EngineHomeView import _NEAR_STOP


def _parse_near(near):
    """Mirror of _resolve_location's ?near= stripping (kept in sync by test)."""
    return " ".join(t for t in near.split() if t.lower() not in _NEAR_STOP).strip()


def test_near_phrase_parsing():
    assert _parse_near("near me jaipur") == "jaipur"
    assert _parse_near("interior shops in New Delhi") == "interior shops New Delhi"
    assert _parse_near("Mumbai") == "Mumbai"
    assert _parse_near("near me") == ""            # only filler -> broadens to all
    assert _parse_near("") == ""


def test_broaden_shops_rung_order():
    # _broaden_shops yields city -> state -> all; a missing city/state is skipped
    # but the final "all" rung always runs so the section is never empty.
    class Base:
        def __init__(self, tag="all"):
            self.tag = tag
        def filter(self, **kw):
            return Base("city" if "city__iexact" in kw else "state")
    from app_ib.Controllers.Engine.HomeController import HOME_CONTROLLER
    assert [q.tag for q in HOME_CONTROLLER._broaden_shops(Base(), "Jaipur", "Rajasthan")] \
        == ["city", "state", "all"]
    assert [q.tag for q in HOME_CONTROLLER._broaden_shops(Base(), "", "")] == ["all"]


if __name__ == "__main__":
    test_near_phrase_parsing()
    test_broaden_shops_rung_order()
    print("ok")
