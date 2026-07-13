import logging
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# UA parsing helper — simple substring heuristic, no external dependency
# ---------------------------------------------------------------------------
def _parse_ua(ua: str) -> str:
    """Return a short human-readable device label from a User-Agent string.

    Examples: "Chrome on macOS", "Safari on iPhone", "Firefox on Windows".
    Deliberately simple — never raises, never returns empty string.
    """
    if not ua:
        return "Unknown Device"
    ua_lower = ua.lower()

    # Browser detection (order matters — Edge/OPR before Chrome, Mobile Safari before Safari)
    if "edg/" in ua_lower or "edge/" in ua_lower:
        browser = "Edge"
    elif "opr/" in ua_lower or "opera" in ua_lower:
        browser = "Opera"
    elif "firefox/" in ua_lower or "fxios/" in ua_lower:
        browser = "Firefox"
    elif "samsungbrowser/" in ua_lower:
        browser = "Samsung Browser"
    elif "crios/" in ua_lower:
        browser = "Chrome on iOS"
    elif "chrome/" in ua_lower or "chromium/" in ua_lower:
        browser = "Chrome"
    elif "mobile safari/" in ua_lower or "safari/" in ua_lower:
        browser = "Safari"
    else:
        browser = "Browser"

    # Platform / OS detection
    if "iphone" in ua_lower:
        platform = "iPhone"
    elif "ipad" in ua_lower:
        platform = "iPad"
    elif "android" in ua_lower:
        platform = "Android"
    elif "windows" in ua_lower:
        platform = "Windows"
    elif "macintosh" in ua_lower or "mac os" in ua_lower:
        platform = "macOS"
    elif "linux" in ua_lower:
        platform = "Linux"
    else:
        platform = "Unknown OS"

    return f"{browser} on {platform}"


# ---------------------------------------------------------------------------
# Session recording — best-effort, never raises
# ---------------------------------------------------------------------------
def _get_client_ip(request) -> str:
    """Extract real client IP (X-Forwarded-For first hop, else REMOTE_ADDR)."""
    try:
        xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "") or ""
    except Exception:
        return ""


def _record_session_sync(user, refresh_jti: str, request=None) -> None:
    """Write a UserSession row. Called synchronously inside sync_to_async context."""
    try:
        from app_ib.engine_models import UserSession
        ua = ""
        ip = ""
        device_label = "Unknown Device"
        if request is not None:
            ua = request.META.get("HTTP_USER_AGENT", "") or ""
            ip = _get_client_ip(request) or None
            device_label = _parse_ua(ua)

        UserSession.objects.create(
            user=user,
            jti=refresh_jti,
            deviceLabel=device_label,
            userAgent=ua,
            ipAddress=ip or None,
            city="",
        )
    except Exception as exc:
        logger.warning("UserSession record failed (non-fatal): %s", exc)


# ---------------------------------------------------------------------------
# Custom JWT serializer — adds sjti claim to both refresh and access tokens
# ---------------------------------------------------------------------------
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    @sync_to_async
    def get_token(cls, user):
        token = super().get_token(user)

        # Grab the refresh jti BEFORE stringifying (it's on the RefreshToken object)
        refresh_jti = str(token.get("jti", ""))

        # Task 2 — propagate sjti (session jti) to access token so the sessions
        # list view can flag isCurrent by comparing sjti from the access token claim.
        token["sjti"] = refresh_jti          # lives on the refresh token payload
        token.access_token["sjti"] = refresh_jti  # survives into the access token

        generatedToken = {
            'refresh': str(token),
            'access': str(token.access_token),
        }
        return generatedToken


# ---------------------------------------------------------------------------
# Task 3 — Rotation-aware refresh view
# After the parent rotates the refresh token (old blacklisted, new minted),
# find the UserSession by OLD jti and update it to the NEW jti.
# Same URL, same request/response contract as TokenRefreshView.
# ---------------------------------------------------------------------------
class SessionAwareTokenRefreshSerializer(TokenRefreshSerializer):
    """Thin subclass: identical request/response to TokenRefreshSerializer,
    but side-effects the UserSession row after rotation."""

    def validate(self, attrs):
        # Grab the OLD jti from the incoming refresh token BEFORE super() rotates it.
        old_jti = ""
        try:
            from rest_framework_simplejwt.tokens import RefreshToken as _RT
            old_rt = _RT(attrs.get("refresh", ""))
            old_jti = str(old_rt.get("jti", ""))
        except Exception:
            pass

        # Let the parent do the full rotation + blacklisting
        data = super().validate(attrs)

        # Now extract the NEW jti from the newly minted refresh token
        try:
            from rest_framework_simplejwt.tokens import RefreshToken as _RT2
            new_rt = _RT2(data.get("refresh", ""))
            new_jti = str(new_rt.get("jti", ""))
            if old_jti and new_jti:
                _bump_session(old_jti, new_jti)
            # Task 8 — the parent mints the new ACCESS token WITHOUT sjti; re-add it
            # (= the new refresh jti, matching the bumped session) so refreshed tokens
            # stay enforceable by SessionAwareJWTAuthentication and keep flagging
            # isCurrent in my_sessions.
            if new_jti and data.get("access"):
                from rest_framework_simplejwt.tokens import AccessToken
                at = AccessToken(data["access"])
                at["sjti"] = new_jti
                data["access"] = str(at)
        except Exception as exc:
            logger.warning("Session jti bump failed (non-fatal): %s", exc)

        return data


def _bump_session(old_jti: str, new_jti: str) -> None:
    """Update the UserSession's jti from old to new after rotation, and bump
    lastActiveAt. Uses save(update_fields=...) (NOT queryset .update(), which
    bypasses the auto_now field) so lastActiveAt actually advances on refresh.
    Runs synchronously (inside the DRF sync refresh view).
    """
    try:
        from app_ib.engine_models import UserSession
        session = UserSession.objects.filter(jti=old_jti, revokedAt__isnull=True).first()
        if session is None:
            return
        session.jti = new_jti
        # lastActiveAt is auto_now → save() refreshes it; list it so only these change.
        session.save(update_fields=["jti", "lastActiveAt"])
    except Exception as exc:
        logger.warning("_bump_session DB update failed (non-fatal): %s", exc)


class SessionAwareTokenRefreshView(TokenRefreshView):
    """Drop-in replacement for TokenRefreshView — identical URL contract."""
    serializer_class = SessionAwareTokenRefreshSerializer
