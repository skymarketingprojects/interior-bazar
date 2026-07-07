from asgiref.sync import sync_to_async
from django.db.models import Q
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from interior_admin.models import AdminAuditLog
from .Validators.AuditValidators import AuditQueryFilters


async def append_audit(actor=None, role: str = None, action: str = "",
                       module_key: str = "", detail: str = "") -> None:
    """Append one row to the admin audit trail. Call from every level-3
    (sensitive) admin action AFTER it succeeds. Best-effort: never let an audit
    write break the caller's action.
    ponytail: swallow errors — an audit-write failure must not fail the mutation
    it records; upgrade to a queued/retried writer only if audit loss matters."""
    try:
        resolved_role = role
        if resolved_role is None and actor is not None:
            first = await sync_to_async(
                lambda: actor.roles.first() if hasattr(actor, "roles") else None
            )()
            resolved_role = first.name if first else None
        await AdminAuditLog.objects.acreate(
            actor=actor if (actor is not None and getattr(actor, "is_authenticated", False)) else None,
            role=resolved_role,
            action=action,
            moduleKey=module_key,
            detail=detail,
        )
    except Exception as e:
        print(f"[AUDIT] append_audit failed (non-fatal): {e}")


def _serialize(entry: AdminAuditLog) -> Dict[str, Any]:
    return {
        "id": entry.id,
        "actor": entry.actor.username if entry.actor else None,
        "role": entry.role,
        "action": entry.action,
        "module": entry.moduleKey,
        "detail": entry.detail,
        "ts": entry.createdAt.isoformat() if entry.createdAt else None,
    }


class AuditController:

    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.default_error,
        responseFunc=LocalResponse,
    )
    async def GetAuditLog(cls, queryParams: AuditQueryFilters) -> Tuple[bool, Dict[str, Any]]:
        filters = Q()
        if queryParams.module:
            filters &= Q(moduleKey=queryParams.module)
        if queryParams.role:
            filters &= Q(role=queryParams.role)
        if queryParams.dateFrom:
            filters &= Q(createdAt__date__gte=queryParams.dateFrom)
        if queryParams.dateTo:
            filters &= Q(createdAt__date__lte=queryParams.dateTo)

        pageNo = max(1, queryParams.pageNo or 1)
        pageSize = min(100, max(1, queryParams.pageSize or 20))
        start = (pageNo - 1) * pageSize

        qs = AdminAuditLog.objects.filter(filters).select_related("actor")
        total = await qs.acount()
        rows = await sync_to_async(list)(qs[start:start + pageSize])

        return True, {
            "entries": [_serialize(r) for r in rows],
            "total": total,
            "pageNo": pageNo,
            "pageSize": pageSize,
        }


AUDIT_CONTROLLER = AuditController()
