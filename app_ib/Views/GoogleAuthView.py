"""Google login endpoints (sync DRF, public)."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Controllers.Auth.GoogleAuthController import GOOGLE_AUTH_CONTROLLER, GoogleAuthError


@api_view(["POST"])
@permission_classes([AllowAny])
def GoogleLoginView(request):
    """Auth-code exchange: body { code, redirectUri }."""
    code = request.data.get("code")
    redirect_uri = request.data.get("redirectUri") or request.data.get("redirect_uri")
    if not code or not redirect_uri:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request,
                              message="code and redirectUri are required", data={})
    try:
        data = GOOGLE_AUTH_CONTROLLER.login_with_code(code, redirect_uri)
        return ServerResponse(response=True, code=RESPONSE_CODES.success,
                              message="Login successful", data=data)
    except GoogleAuthError as e:
        return ServerResponse(response=False, code=RESPONSE_CODES.auth_error, message=str(e), data={})


@api_view(["POST"])
@permission_classes([AllowAny])
def GoogleIdTokenLoginView(request):
    """ID-token flow: body { idToken }."""
    id_token = request.data.get("idToken") or request.data.get("id_token")
    if not id_token:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request,
                              message="idToken is required", data={})
    try:
        data = GOOGLE_AUTH_CONTROLLER.login_with_id_token(id_token)
        return ServerResponse(response=True, code=RESPONSE_CODES.success,
                              message="Login successful", data=data)
    except GoogleAuthError as e:
        return ServerResponse(response=False, code=RESPONSE_CODES.auth_error, message=str(e), data={})
