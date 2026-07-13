"""Session-aware JWT authentication.

Stock simplejwt validates only the access token's signature + expiry — it never
consults per-session revocation, so signing a device out (UserSession.revokedAt)
did nothing to that device's ACCESS token until it expired (60 days). Every access
token already carries the session's `sjti` claim; this class reads it and rejects
the request when the matching UserSession has been revoked.

Task 8.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed


class SessionAwareJWTAuthentication(JWTAuthentication):
    """JWTAuthentication + one indexed UserSession lookup to enforce per-session
    sign-out on the access token.

    - Token WITHOUT an `sjti` claim passes through unchanged (pre-feature tokens
      keep working — no mass logout on deploy).
    - Token WITH `sjti` is rejected when the matching UserSession row is revoked
      or no longer exists.

    # ponytail: direct DB lookup per request; add a short-TTL cache of revoked
    # jtis only if profiling ever shows it.
    """

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        self._enforce_session(validated_token)
        return user

    @staticmethod
    def _enforce_session(validated_token):
        sjti = validated_token.get("sjti")
        if not sjti:
            return  # pre-feature token — nothing to enforce

        from app_ib.engine_models import UserSession

        # .values(...).first() → dict when the row exists, None when it doesn't,
        # so "no row" (None) and "active row" ({"revokedAt": None}) stay distinct.
        row = UserSession.objects.filter(jti=sjti).values("revokedAt").first()
        if row is None:
            raise AuthenticationFailed("Session no longer exists", code="session_gone")
        if row["revokedAt"] is not None:
            raise AuthenticationFailed("Session has been signed out", code="session_revoked")
