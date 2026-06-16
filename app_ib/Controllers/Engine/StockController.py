"""
StockController — engine-side product stock + service availability.

WHY this exists: products track an integer stockQuantity (null = stock not
tracked -> always treated as in stock); services have NO stock at all, only
an owner-controlled `isAvailable` switch. `isActive` is deliberately left
alone on both models — it means listed/unlisted on the marketplace, which is
a different concept from "can be ordered/booked right now".

ORDER-FLOW HOOK (read before wiring stock decrements anywhere):
Buyer enquiries/orders today are created ONLY by the LEGACY lead flow —
POST /api/v1/query/create/ (app_ib/Views/QueryView.CreateQueryView ->
Controllers/Query/QueryController.CreateLeadQuery -> Tasks/QueryTasks), which
persists a LeadQuery with an optional `product` FK and no quantity. That flow
is FROZEN and must not be modified. There is currently NO engine-side
order/quotation creation endpoint; when one is built under /api/v1/engine/,
it must call `check_and_reserve_stock()` below inside its own request
handling BEFORE persisting the order so overselling is impossible.
"""
from app_ib.Controllers.Engine.CrudController import NotFound_, PermissionError_


# ---------------------------------------------------------------------------
# Product availability (public read)
# ---------------------------------------------------------------------------
def product_availability(product_id):
    """{inStock, stockQuantity} — stockQuantity stays null when untracked."""
    from interior_products.models import Product
    p = Product.objects.filter(id=product_id).first()
    if not p:
        raise NotFound_("product not found")
    # null stockQuantity = the seller doesn't track stock -> treat as in stock
    in_stock = p.stockQuantity is None or p.stockQuantity > 0
    return {"inStock": in_stock, "stockQuantity": p.stockQuantity}


# ---------------------------------------------------------------------------
# Service availability (public read, owner-only write)
# ---------------------------------------------------------------------------
def service_availability(service_id, user=None):
    """{isAvailable} (+ isOwner when authenticated) for the detail page.

    isOwner is included only for authenticated callers so the frontend can
    decide whether to render the owner's availability toggle without needing
    a separate ownership endpoint.
    """
    from interior_products.models import Service
    s = Service.objects.filter(id=service_id).first()
    if not s:
        raise NotFound_("service not found")
    out = {"isAvailable": bool(s.isAvailable)}
    if user is not None and getattr(user, "is_authenticated", False):
        # ownership chain: Service.business -> Business.user (see _owner_id in
        # GapsController — same convention, inlined here to avoid a query for
        # the full business row)
        out["isOwner"] = bool(s.business_id) and s.business.user_id == user.id
    return out


def service_availability_set(user, service_id, is_available):
    """Owner-only toggle of Service.isAvailable. Raises PermissionError_ for
    anyone who is not the owning business's user (mapped to code 403)."""
    from interior_products.models import Service
    s = Service.objects.filter(id=service_id).first()
    if not s:
        raise NotFound_("service not found")
    owner_id = s.business.user_id if s.business_id else None
    if owner_id != user.id:
        raise PermissionError_("not the service owner")
    # update() instead of save(): Service.save() recomputes displayPrice and
    # reshuffles index — side effects we must not trigger from a toggle
    Service.objects.filter(id=s.id).update(isAvailable=bool(is_available))
    return {"isAvailable": bool(is_available), "isOwner": True}


# ---------------------------------------------------------------------------
# Product stock guard (check + atomic reserve)
# ---------------------------------------------------------------------------
def product_stock_check(product_id, quantity):
    """Read-only feasibility check: {ok, available}.

    available mirrors stockQuantity (null = untracked -> always ok). This is
    what the detail page calls before letting a buyer submit an enquiry, so
    no extra products get ordered past the stock on hand.
    """
    from interior_products.models import Product
    p = Product.objects.filter(id=product_id).first()
    if not p:
        raise NotFound_("product not found")
    ok = p.stockQuantity is None or p.stockQuantity >= quantity
    return {"ok": ok, "available": p.stockQuantity}


def check_and_reserve_stock(product_id, quantity):
    """Atomically verify AND decrement product stock. Returns {ok, available}
    where `available` is the stock remaining AFTER the decrement (null when
    stock is untracked; pre-decrement count when ok=False).

    Concurrency: select_for_update() serialises competing buyers on the same
    product row and the F-expression decrement happens inside the same
    transaction, so two simultaneous orders can never both take the last unit.
    The queryset .update() path also skips Product.save() on purpose — save()
    recomputes displayPrice and shifts `index`, side effects a stock decrement
    must not trigger.

    NOT yet called from any order flow — order creation lives in the FROZEN
    legacy lead flow (see module docstring). Future engine order/quotation
    endpoints must call this before persisting the order.
    """
    from django.db import transaction
    from django.db.models import F
    from interior_products.models import Product
    quantity = int(quantity)
    if quantity < 1:
        raise ValueError("quantity must be >= 1")
    with transaction.atomic():
        p = Product.objects.select_for_update().filter(id=product_id).first()
        if not p:
            raise NotFound_("product not found")
        if p.stockQuantity is None:
            return {"ok": True, "available": None}  # untracked — nothing to decrement
        if p.stockQuantity < quantity:
            return {"ok": False, "available": p.stockQuantity}
        Product.objects.filter(id=p.id).update(stockQuantity=F("stockQuantity") - quantity)
        return {"ok": True, "available": p.stockQuantity - quantity}
