# Local verification only (NOT for prod): real settings with the redis cache
# swapped for in-memory, since the local machine has no redis service.
# Delete after migration verification. Run: DJANGO_SETTINGS_MODULE=interior_bazzar.settings_verify
from .settings import *  # noqa

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
