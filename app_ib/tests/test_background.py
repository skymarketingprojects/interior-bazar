"""ponytail self-check: background.enqueue runs the job off-thread and dedupes a
second identical job while one is in flight. Run from backend root:
    python app_ib/tests/test_background.py
"""
import os
import sys
import threading

if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    os.environ["DJANGO_SETTINGS_MODULE"] = "interior_bazzar.settings"
    import django
    django.setup()

from app_ib.algorithms import background
from app_ib.Utils.SafeCache import safe_cache as cache


def test_enqueue_runs_and_dedupes():
    ran = threading.Event()
    started = threading.Event()

    def slow_job():
        started.set()
        # hold long enough that the dedupe check below happens while in flight
        ran.wait(timeout=2)

    key = "selfcheck_job"
    cache.delete(f"bg:lock:{key}")
    assert background.enqueue(key, slow_job) is True          # newly started
    assert started.wait(timeout=2), "job thread never started"
    assert background.is_running(key) is True                  # lock held while running
    assert background.enqueue(key, slow_job) is False          # deduped: already in flight
    ran.set()                                                  # let the job finish


def test_enqueue_actually_executes():
    done = threading.Event()
    background.enqueue("selfcheck_exec", done.set)
    assert done.wait(timeout=2), "enqueued fn did not execute"


if __name__ == "__main__":
    test_enqueue_runs_and_dedupes()
    test_enqueue_actually_executes()
    print("ok")
