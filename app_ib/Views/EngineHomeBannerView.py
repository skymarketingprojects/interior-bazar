"""Home-page hero banner view (sync DRF, public).

Kept in its own file (not EngineHomeView) so parallel work on other home
sections never collides with the banner flow; same house style as
EngineHomeView — thin AllowAny view delegating to a singleton controller.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Controllers.Engine.HomeBannerController import HOME_BANNER_CONTROLLER


# Hero carousel slides (tag/title/description + background + buttons +
# metrics + 2 featured businesses per slide, trending-backfilled).
@api_view(["GET"])
@permission_classes([AllowAny])
def HomeBannersView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message="ok",
                          data=HOME_BANNER_CONTROLLER.hero_banners(page="home"))


# Generic per-page hero carousel slides: GET /engine/banners/?page=architects
# Same payload shape as HomeBannersView; `page` selects which page's banners to
# serve (defaults to "home"). An unknown/empty page returns [] and the frontend
# keeps its static fallback.
@api_view(["GET"])
@permission_classes([AllowAny])
def BannersView(request):
    page = request.GET.get("page") or "home"
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message="ok",
                          data=HOME_BANNER_CONTROLLER.hero_banners(page=page))
