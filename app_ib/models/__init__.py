"""app_ib models — split into a package by domain (TASK 17) so no single file is
huge. Same app_label "app_ib" and same db tables → the split needs NO migration.

`from app_ib.models import X` keeps resolving unchanged for every existing call
site: the local domain files are re-exported here, and so are the models that were
moved OUT of app_ib into the domain apps in TASK 13–17 (same class object via all
paths; the domain apps use string FKs and never import app_ib.models → no cycle).
"""
from .core import *      # noqa: F401,F403
from .chat import *      # noqa: F401,F403
from .support import *   # noqa: F401,F403

# Re-export the models relocated to domain apps so legacy imports keep working.
from interior_business.models import *      # noqa: E402,F401,F403  TASK 18 (Business cluster)
from interior_engine.models import *        # noqa: E402,F401,F403  TASK 13
from interior_billing.models import *       # noqa: E402,F401,F403  TASK 14
from interior_leads.models import *         # noqa: E402,F401,F403  TASK 15
from interior_cms.models import *           # noqa: E402,F401,F403  TASK 16
from interior_notification.models import *  # noqa: E402,F401,F403  TASK 17 (Notification)
