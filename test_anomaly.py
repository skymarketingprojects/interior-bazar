"""Runnable check for lead anomaly detection (task 14).

    cd interior-bazzar-backend/interior-bazar && python test_anomaly.py

Asserts the _detect_anomaly heuristic quarantines fake/garbage leads and passes
genuine ones. No pytest/framework — plain asserts (ponytail).
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interior_bazzar.settings")
django.setup()

from app_ib.Controllers.Query.Tasks.QueryTasks import _detect_anomaly


def demo():
    good_phone = "9876543210"  # 10 digits

    # --- anomalies (should quarantine) ---
    assert _detect_anomaly("aaa", good_phone) == "name_repeated_char"      # single repeated char
    assert _detect_anomaly("a1", good_phone) == "name_trivial"             # too short (<3)
    assert _detect_anomaly("xyz", good_phone) == "name_no_vowel"           # no vowel
    assert _detect_anomaly("Priya4", good_phone) == "name_has_digits"      # digits in name
    assert _detect_anomaly("Priya Menon", "987654321") == "phone_digits"   # 9 digits
    assert _detect_anomaly("Priya Menon", "98765-4321-00") == "phone_digits"  # 11 digits after strip
    assert _detect_anomaly("Priya Menon", "") == "phone_digits"            # empty phone

    # --- genuine (should pass) ---
    assert _detect_anomaly("Priya Menon", good_phone) is None
    assert _detect_anomaly("Priya Menon", "98765 43210") is None           # spaces stripped -> 10
    assert _detect_anomaly("Ravi", good_phone) is None

    print("test_anomaly: all assertions passed")


if __name__ == "__main__":
    demo()
