# app_ib/Utils/PhonePeClient.py

from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient
from phonepe.sdk.pg.env import Env
from django.conf import settings
from app_ib.Utils.AppMode import APPMODE

class PhonePeClientWrapper:
    _client_instance = None

    @classmethod
    def get_client(cls):
        if not cls._client_instance:
            cls._client_instance = StandardCheckoutClient.get_instance(
                client_id=settings.PHONEPE_CLIENT_ID,
                client_secret=settings.PHONEPE_CLIENT_SECRET,
                client_version=settings.PHONEPE_CLIENT_VERSION,
                env=Env.SANDBOX if settings.ENV == APPMODE.DEV else Env.PRODUCTION,
                should_publish_events=False
            )
        return cls._client_instance
