# app_ib/Utils/CashfreeClient.py
import requests
from django.conf import settings

class CashfreeClientWrapper:
    """
    Wrapper for Cashfree REST API client.
    """

    @staticmethod
    def get_headers():
        """
        Prepare headers for Cashfree API.
        """
        # print("CASHFREE_CLIENT_ID:", settings.CASHFREE_CLIENT_ID)
        # print("CASHFREE_CLIENT_SECRET:", settings.CASHFREE_CLIENT_SECRET)
        # print("CASHFREE_API_VERSION:", settings.CASHFREE_API_VERSION)
        return {
            "x-client-id": settings.CASHFREE_CLIENT_ID,
            "x-client-secret": settings.CASHFREE_CLIENT_SECRET,
            "x-api-version": settings.CASHFREE_API_VERSION,
            "Content-Type": "application/json",
        }

    @staticmethod
    def get_base_url():
        """
        Returns correct base URL based on environment.
        """
        if getattr(settings, "CASHFREE_ENVIRONMENT", "SANDBOX") == "PRODUCTION":
            return "https://api.cashfree.com/pg"
        return "https://sandbox.cashfree.com/pg"

    @staticmethod
    def create_order(payload):
        """
        Create a new Cashfree order via REST API.
        """
        url = f"{CashfreeClientWrapper.get_base_url()}/orders"
        headers = CashfreeClientWrapper.get_headers()
        # print("Cashfree Create Order Payload:", payload)
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        # print("Cashfree Create Order Response Status Code:", response.status_code)?
        return response.json()

    @staticmethod
    def fetch_order(order_id):
        """
        Fetch order details from Cashfree.
        """
        url = f"{CashfreeClientWrapper.get_base_url()}/orders/{order_id}"
        headers = CashfreeClientWrapper.get_headers()
        response = requests.get(url, headers=headers, timeout=15)
        return response.json()

    @staticmethod
    def create_refund(order_id, refund_payload):
        """
        Create a refund for an order.
        """
        url = f"{CashfreeClientWrapper.get_base_url()}/orders/{order_id}/refunds"
        headers = CashfreeClientWrapper.get_headers()
        response = requests.post(url, headers=headers, json=refund_payload, timeout=15)
        return response.json()
