"""
settings_engine — non-invasive settings overlay for running the v2.1.0.0 engine
locally without a Redis server.

Usage:
    python manage.py <cmd> --settings=interior_bazzar.settings_engine

Inherits everything from the real settings, then swaps the Redis cache backend
for Django's in-process LocMemCache so cache-invalidation signals and the
engine's cache.set/get calls work without external infrastructure.
"""
from .settings import *  # noqa: F401,F403

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "engine-locmem",
    }
}
