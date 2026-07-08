from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.models import CustomUser, Business, LeadQuery, Blog


class WebAnalyticsController:
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Get(cls) -> Tuple[bool, Dict[str, Any]]:
        return True, {
            "totalUsers": await CustomUser.objects.filter(is_delete=False).acount(),
            "buyers": await CustomUser.objects.filter(type="user", is_delete=False).acount(),
            "businesses": await Business.objects.acount(),
            "verifiedBusinesses": await Business.objects.filter(isVerified=True).acount(),
            "leads": await LeadQuery.objects.acount(),
            "blogs": await Blog.objects.acount(),
        }


WEB_ANALYTICS_CONTROLLER = WebAnalyticsController()
