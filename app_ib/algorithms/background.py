"""Minimal background-task runner for the discovery engine.

The engine has no Celery/task queue (see backend CLAUDE.md). When a home section
finds its cron-populated data empty, it must NOT recompute synchronously — that
would add seconds to the request. Instead it enqueues the recompute here: a
daemon thread runs it off the request/response cycle, and a short cache lock
dedupes concurrent requests so a traffic spike triggers at most one recompute
(no thundering herd) while every request still returns immediately.

The nightly `run_engine_jobs` cron remains the source of truth; this only warms
an empty board between cron runs. Real cron runs overwrite whatever this warms.

ponytail: threads, not Celery — a single-process best-effort offload is all a
warm-the-cache job needs. Ceiling: the get→set lock is not atomic and the lock
is per-process, so a multi-process deployment could run ~one recompute per
process per lock TTL. That is harmless for an idempotent recompute; swap in a
Redis SETNX lock (or Celery) only if that ever becomes a real cost.
"""
import threading

from app_ib.Utils.SafeCache import safe_cache as cache

_LOCK_TTL = 300  # seconds a job key is considered "in flight"


def is_running(job_key):
    return bool(cache.get(f"bg:lock:{job_key}"))


def enqueue(job_key, fn, *args, **kwargs):
    """Run ``fn(*args, **kwargs)`` in a daemon thread unless an identical job is
    already in flight. Returns True if newly started, False if deduped/failed to
    start. Never raises into the caller — a failed enqueue must never break the
    request that triggered it."""
    lock_key = f"bg:lock:{job_key}"
    try:
        if cache.get(lock_key):
            return False
        cache.set(lock_key, 1, _LOCK_TTL)
    except Exception:
        return False

    def _run():
        try:
            fn(*args, **kwargs)
        except Exception:
            pass
        finally:
            try:
                cache.delete(lock_key)
            except Exception:
                pass
            # a spawned thread gets its own DB connection — close it so it isn't leaked
            try:
                from django.db import connection
                connection.close()
            except Exception:
                pass

    try:
        threading.Thread(target=_run, name=f"bg:{job_key}", daemon=True).start()
        return True
    except Exception:
        try:
            cache.delete(lock_key)
        except Exception:
            pass
        return False
