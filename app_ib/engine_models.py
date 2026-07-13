"""engine_models — compat shim.

The v2.1.0.0 discovery-engine models moved to interior_engine (TASK 13); the
remaining chat/support/session/ad models de-cramped into the app_ib/models/
package and Notification into interior_notification (TASK 17). This module is now
a pure re-export so the ~60 existing `from app_ib.engine_models import X` call
sites keep resolving unchanged (same class object as `from app_ib.models import X`).
"""
from app_ib.models import *  # noqa: F401,F403
