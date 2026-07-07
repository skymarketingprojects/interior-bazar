from asgiref.sync import sync_to_async
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.Names import NAMES

from app_ib.models import TransectionData
from interior_admin.models import Expense
from .Validators.RevenueValidators import ExpenseSchema


def _num(s) -> Decimal:
    try:
        return Decimal(str(s or "0").replace(",", "").strip() or "0")
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _expense_dict(e: Expense) -> Dict[str, Any]:
    return {"id": e.id, "label": e.label, "amount": float(e.amount), "category": e.category,
            "incurredAt": e.incurredAt.isoformat() if e.incurredAt else None}


class RevenueController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Overview(cls) -> Tuple[bool, Dict[str, Any]]:
        # Real revenue: sum of PAID transactions, less refunded ones.
        paid = await sync_to_async(list)(
            TransectionData.objects.filter(orderStatus=NAMES.CF_PAID).values_list("amount", "refundStatus"))
        gross = sum((_num(a) for a, _ in paid), Decimal("0"))
        refunded = sum((_num(a) for a, rs in paid if rs == "REFUNDED"), Decimal("0"))
        net_revenue = gross - refunded
        paying_customers = len(paid)

        expenses = await sync_to_async(list)(Expense.objects.all())
        expenses_total = sum((e.amount for e in expenses), Decimal("0"))

        cac = (expenses_total / paying_customers) if paying_customers else Decimal("0")
        net = net_revenue - expenses_total

        return True, {
            "grossRevenue": float(gross),
            "refunded": float(refunded),
            "netRevenue": float(net_revenue),
            "mrr": float(net_revenue),          # ponytail: net paid used as MRR proxy until a recurring-billing model exists
            "cac": float(round(cac, 2)),
            "payingCustomers": paying_customers,
            "expensesTotal": float(expenses_total),
            "net": float(net),
            "expenses": [_expense_dict(e) for e in expenses],
        }

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def AddExpense(cls, payload: ExpenseSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        e = await Expense.objects.acreate(
            label=payload.label, amount=Decimal(str(payload.amount)),
            category=payload.category or '', incurredAt=payload.incurredAt or None,
            createdBy=actor if getattr(actor, "is_authenticated", False) else None)
        return True, _expense_dict(e)


REVENUE_CONTROLLER = RevenueController()
