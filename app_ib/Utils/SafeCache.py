"""
SafeCache — engine-only cache proxy that degrades gracefully when Redis is
unreachable (ConnectionError, timeout, etc.). get() returns the default (i.e.
behaves like a cache miss) and set() becomes a no-op instead of raising, so
engine endpoints fall through to their existing DB-recompute paths and never
500 because the cache backend is down.

Used ONLY by the v2.1 engine layer (EngineController / GapsController /
algorithms). Legacy code paths keep using django.core.cache directly.
"""
import logging

from django.core.cache import cache as _cache

logger = logging.getLogger(__name__)


class _SafeCache:

    def get(self, key, default=None):
        try:
            return _cache.get(key, default)
        except Exception as exc:  # noqa: BLE001 — any backend failure means "miss"
            logger.warning("SafeCache.get(%s) degraded to miss: %s", key, exc)
            return default

    def set(self, key, value, timeout=None):
        try:
            _cache.set(key, value, timeout)
        except Exception as exc:  # noqa: BLE001 — any backend failure means "skip warm"
            logger.warning("SafeCache.set(%s) skipped: %s", key, exc)

    def delete(self, key):
        try:
            _cache.delete(key)
        except Exception as exc:  # noqa: BLE001
            logger.warning("SafeCache.delete(%s) skipped: %s", key, exc)


safe_cache = _SafeCache()
