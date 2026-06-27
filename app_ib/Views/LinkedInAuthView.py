"""LinkedIn login endpoint (sync DRF, public)."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Controllers.Auth.LinkedInAuthController import LINKEDIN_AUTH_CONTROLLER, LinkedInAuthError


@api_view(["POST"])
@permission_classes([AllowAny])
def LinkedInLoginView(request):
    """Auth-code exchange: body { code, redirectUri }."""
    code = request.data.get("code")
    redirect_uri = request.data.get("redirectUri") or request.data.get("redirect_uri")
    if not code or not redirect_uri:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request,
                              message="code and redirectUri are required", data={})
    try:
        data = LINKEDIN_AUTH_CONTROLLER.login_with_code(code, redirect_uri)
        return ServerResponse(response=True, code=RESPONSE_CODES.success,
                              message="Login successful", data=data)
    except LinkedInAuthError as e:
        return ServerResponse(response=False, code=RESPONSE_CODES.auth_error, message=str(e), data={})
