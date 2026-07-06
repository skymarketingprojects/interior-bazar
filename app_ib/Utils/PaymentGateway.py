# app_ib/Utils/PaymentGateway.py
#
# Single plug-and-play seam for the payment gateway. Every gateway-specific
# operation the money path performs (create order, fetch order status, refund,
# hosted-checkout URL) routes through ACTIVE_GATEWAY — nothing else in the
# codebase names the provider.
#
# To swap providers: write a new adapter class exposing the same four
# callables and point ACTIVE_GATEWAY at it. Contract the controllers rely on:
#   create_order(payload) -> dict containing "payment_session_id"
#   fetch_order(order_id) -> dict containing "order_status" ("PAID", ...)
#   create_refund(order_id, refund_payload) -> dict containing "refund_status"
#   checkout_url(session_id) -> str the buyer is redirected to
# A new provider's adapter must normalize its responses to those keys
# (see app_ib/Utils/Names.py: PAYMENT_SESSION_ID / ORDER_STATUS / CF_PAID).
from app_ib.Utils.CashfreeClient import CashfreeClientWrapper


class CashfreeGateway:
    """Adapter over the current provider (Cashfree REST client)."""
    name = "cashfree"
    create_order = staticmethod(CashfreeClientWrapper.create_order)
    fetch_order = staticmethod(CashfreeClientWrapper.fetch_order)
    create_refund = staticmethod(CashfreeClientWrapper.create_refund)

    @staticmethod
    def checkout_url(session_id):
        return f"https://payments.cashfree.com/pgui/v2/checkout?payment_session_id={session_id}"


ACTIVE_GATEWAY = CashfreeGateway
