import re
from asgiref.sync import sync_to_async
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Tuple

from django.db.models import Q
from django.utils import timezone

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.Names import NAMES

from app_ib.models import (
    TransectionData, BusinessPlan, ShopPlan, ArchitectPlan, AutomationPlan,
)
from interior_admin.models import Expense, RevenueAssumption
from interior_admin.Controllers.Audit.AuditController import append_audit
from interior_admin.Controllers.WebAnalytics.WebAnalyticsController import _parse_date
from .Validators.RevenueValidators import ExpenseSchema, AssumptionsSchema


def _num(s) -> Decimal:
    try:
        return Decimal(str(s or "0").replace(",", "").strip() or "0")
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _duration_months(dur) -> Decimal:
    """Subscription.duration is a free string: DAYS ('30','90'), MONTHS ('3','6','12')
    or word forms from old prod ('1 year', '6 months'). Bare-number heuristic:
    >=28 → days, else months. Unparseable → 1 (monthly) as before."""
    m = re.match(r"^(\d+(?:\.\d+)?)\s*([a-z]*)", str(dur or "").strip().lower())
    if not m:
        return Decimal("1")
    n, unit = float(m.group(1)), m.group(2)
    if unit.startswith("year"):
        return Decimal(int(n * 12) or 1)
    if unit.startswith("month"):
        return Decimal(int(n) or 1)
    if unit.startswith("day"):
        return Decimal(max(1, round(n / 30)))
    n = int(n)
    if n <= 0:
        return Decimal("1")
    if n >= 28:
        return Decimal(max(1, round(n / 30)))
    return Decimal(n)


def _last_6_month_keys():
    now = timezone.now()
    keys = []
    y, m = now.year, now.month
    for i in range(5, -1, -1):
        mm, yy = m - i, y
        while mm <= 0:
            mm += 12
            yy -= 1
        keys.append(f"{yy:04d}-{mm:02d}")
    return keys


def _expense_dict(e: Expense) -> Dict[str, Any]:
    return {"id": e.id, "label": e.label, "amount": float(e.amount), "category": e.category,
            "kind": e.kind, "incurredAt": e.incurredAt.isoformat() if e.incurredAt else None}


class RevenueController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Overview(cls, start: str = None, end: str = None) -> Tuple[bool, Dict[str, Any]]:
        startD = _parse_date(start); endD = _parse_date(end)
        # A refunded row WAS paid (the refund action flips orderStatus to REFUNDED),
        # so it belongs in gross — include it and let the refundStatus branch net it
        # out. Filtering PAID-only made refunded permanently 0 and vanished the amount.
        rangeQ = Q(orderStatus__in=[NAMES.CF_PAID, "REFUNDED"])
        if startD:
            rangeQ &= Q(createdAt__date__gte=startD)
        if endD:
            rangeQ &= Q(createdAt__date__lte=endD)
        paid = await sync_to_async(list)(
            TransectionData.objects.filter(rangeQ)
            .values_list("amount", "refundStatus", "paymentFor", "refundAmount", "planFamily"))

        gross = Decimal("0"); refunded = Decimal("0")
        by_family = defaultdict(Decimal)
        for amount, rs, fam, refundAmt, planFam in paid:
            amt = _num(amount)
            gross += amt
            if rs == "REFUNDED":
                # Partial refunds carry refundAmount; blank = the whole amount refunded.
                refunded += _num(refundAmt) if str(refundAmt or "").strip() else amt
                continue
            # Real per-family split: planFamily captured at write time, else paymentFor
            # (old rows / ads / upgrades w/o a plan stay in their paymentFor bucket).
            by_family[planFam or fam or "other"] += amt
        net_revenue = gross - refunded

        # 6-month trend is a deliberate fixed trailing window — un-ranged. PAID-only rows
        # are the non-refunded sales (refunds flip orderStatus), matching prior behavior.
        by_month = defaultdict(Decimal)
        trend_rows = await sync_to_async(list)(
            TransectionData.objects.filter(orderStatus=NAMES.CF_PAID)
            .values_list("amount", "createdAt"))
        for amount, created in trend_rows:
            if created:
                by_month[created.strftime("%Y-%m")] += _num(amount)

        months = _last_6_month_keys()
        monthlyRevenue = [{"month": k, "amount": float(by_month.get(k, Decimal("0")))} for k in months]
        salesThisMonth = float(by_month.get(months[-1], Decimal("0")))
        salesPrevMonth = float(by_month.get(months[-2], Decimal("0"))) if len(months) >= 2 else 0.0
        if salesPrevMonth:
            momDeltaPct = round((salesThisMonth - salesPrevMonth) / salesPrevMonth * 100, 1)
        else:
            momDeltaPct = 100.0 if salesThisMonth else 0.0
        revenueByFamily = [{"label": f, "amount": float(v)} for f, v in
                           sorted(by_family.items(), key=lambda kv: -kv[1])]

        # Real MRR: active plans, amount normalised to a monthly figure.
        # payingCustomers is point-in-time (all-time), NOT ranged — sourced here off the
        # active paid plans (TransectionData is near-empty and only ever covers future
        # gateway purchases). Distinct paying users: a paid (amount>0) active plan with a
        # non-null user; renewals/multiple plans per user collapse to one.
        mrr = Decimal("0"); active_subscribers = 0; paying_user_ids = set()
        for model in (BusinessPlan, ShopPlan, ArchitectPlan, AutomationPlan):
            rows = await sync_to_async(list)(
                model.objects.filter(isActive=True).select_related("plan")
                .values_list("amount", "durationMonths", "plan__duration", "user_id"))
            for amt, dm, dur, user_id in rows:
                active_subscribers += 1
                # purchased-row snapshot first (ground truth); legacy string parse as fallback
                mrr += _num(amt) / (Decimal(dm) if dm else _duration_months(dur))
                if _num(amt) > 0 and user_id is not None:
                    paying_user_ids.add(user_id)
        arpu = (mrr / active_subscribers) if active_subscribers else Decimal("0")
        paying_customers = len(paying_user_ids)

        # Expenses split for the P&L waterfall — ranged by incurredAt so net compares
        # the same period as revenue. (No range = all-time. Undated expenses have no
        # incurredAt, so they only count when the range is open.)
        expenseQ = Q()
        if startD:
            expenseQ &= Q(incurredAt__gte=startD)
        if endD:
            expenseQ &= Q(incurredAt__lte=endD)
        expenses = await sync_to_async(list)(Expense.objects.filter(expenseQ))
        expenses_total = sum((e.amount for e in expenses), Decimal("0"))
        expenses_fixed = sum((e.amount for e in expenses if e.kind == "fixed"), Decimal("0"))
        expenses_reinvest = sum((e.amount for e in expenses if e.kind == "reinvestment"), Decimal("0"))

        # Tunable assumption inputs → transparent LTV/CAC/payback estimates.
        assume, _ = await RevenueAssumption.objects.aget_or_create(id=1)
        avg_lifetime = Decimal(assume.avgLifetimeMonths or 0)
        gross_margin = assume.grossMargin or Decimal("0")
        new_customers = assume.newCustomersThisMonth or 0
        ltv = arpu * avg_lifetime * gross_margin
        cac = (expenses_total / new_customers) if new_customers else Decimal("0")
        ltv_cac = (ltv / cac) if cac else Decimal("0")
        payback_months = (cac / arpu) if arpu else Decimal("0")
        net = net_revenue - expenses_total

        def f(x):
            return float(round(x, 2))

        return True, {
            "grossRevenue": f(gross), "refunded": f(refunded), "netRevenue": f(net_revenue),
            "mrr": f(mrr), "arpu": f(arpu), "activeSubscribers": active_subscribers,
            "payingCustomers": paying_customers,
            "salesThisMonth": f(Decimal(str(salesThisMonth))), "momDeltaPct": momDeltaPct,
            "revenueByFamily": revenueByFamily, "monthlyRevenue": monthlyRevenue,
            "expensesTotal": f(expenses_total), "expensesFixed": f(expenses_fixed),
            "expensesReinvest": f(expenses_reinvest), "net": f(net),
            "cac": f(cac), "ltv": f(ltv), "ltvCac": f(ltv_cac), "paybackMonths": f(payback_months),
            "assumptions": {
                "avgLifetimeMonths": assume.avgLifetimeMonths,
                "grossMargin": float(assume.grossMargin),
                "revenueTarget": float(assume.revenueTarget),
                "newCustomersThisMonth": assume.newCustomersThisMonth,
            },
            "expenses": [_expense_dict(e) for e in expenses],
        }

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def AddExpense(cls, payload: ExpenseSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        kind = payload.kind if payload.kind in ("fixed", "reinvestment") else "fixed"
        e = await Expense.objects.acreate(
            label=payload.label, amount=Decimal(str(payload.amount)),
            category=payload.category or '', kind=kind, incurredAt=payload.incurredAt or None,
            createdBy=actor if getattr(actor, "is_authenticated", False) else None)
        return True, _expense_dict(e)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def SetAssumptions(cls, payload: AssumptionsSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        a, _ = await RevenueAssumption.objects.aget_or_create(id=1)
        if payload.avgLifetimeMonths is not None:
            a.avgLifetimeMonths = payload.avgLifetimeMonths
        if payload.grossMargin is not None:
            a.grossMargin = Decimal(str(payload.grossMargin))
        if payload.revenueTarget is not None:
            a.revenueTarget = Decimal(str(payload.revenueTarget))
        if payload.newCustomersThisMonth is not None:
            a.newCustomersThisMonth = payload.newCustomersThisMonth
        await sync_to_async(a.save)()
        await append_audit(actor=actor, action='revenue_assumptions_updated', module_key='revenue',
                           detail=f"lifetime={a.avgLifetimeMonths} margin={a.grossMargin} target={a.revenueTarget}")
        return True, {
            "avgLifetimeMonths": a.avgLifetimeMonths, "grossMargin": float(a.grossMargin),
            "revenueTarget": float(a.revenueTarget), "newCustomersThisMonth": a.newCustomersThisMonth,
        }


REVENUE_CONTROLLER = RevenueController()
