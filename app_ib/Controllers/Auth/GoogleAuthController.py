"""
GoogleAuthController — server-side Google OAuth (auth-code exchange).

Flow: frontend obtains an authorization `code` (web client) and POSTs it with the
`redirect_uri` it used. Backend exchanges code -> tokens at Google's token endpoint
using client_id + client_secret, validates the id_token (aud/iss), then find-or-creates
a CustomUser (username = Google email) and issues the app's own JWT pair.
"""
import base64
import json
import logging

import requests
from django.conf import settings
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_TOKENINFO_URI = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


class GoogleAuthError(Exception):
    pass


def _b64url_decode(segment):
    pad = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + pad)


def _decode_id_token_payload(id_token):
    try:
        _, payload_b64, _ = id_token.split(".")
        return json.loads(_b64url_decode(payload_b64))
    except Exception as e:
        raise GoogleAuthError(f"malformed id_token: {e}")


def _validate_claims(claims):
    aud = claims.get("aud")
    allowed = getattr(settings, "GOOGLE_OAUTH2_ALLOWED_AUDIENCES", [])
    if allowed and aud not in allowed:
        raise GoogleAuthError(f"id_token audience mismatch: {aud}")
    if claims.get("iss") not in GOOGLE_ISSUERS:
        raise GoogleAuthError(f"unexpected issuer: {claims.get('iss')}")
    if not claims.get("email"):
        raise GoogleAuthError("id_token missing email")
    return claims


class _GoogleAuthController:

    def exchange_code(self, code, redirect_uri):
        """Exchange an auth code for Google tokens; return validated id_token claims."""
        if not getattr(settings, "GOOGLE_OAUTH2_CLIENT_SECRET", ""):
            raise GoogleAuthError("Google OAuth client secret not configured")
        resp = requests.post(GOOGLE_TOKEN_URI, data={
            "code": code,
            "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }, timeout=30)
        if resp.status_code != 200:
            raise GoogleAuthError(f"token exchange failed ({resp.status_code}): {resp.text[:200]}")
        token_data = resp.json()
        id_token = token_data.get("id_token")
        if not id_token:
            raise GoogleAuthError("no id_token in Google response")
        return _validate_claims(_decode_id_token_payload(id_token))

    def verify_id_token(self, id_token):
        """Alt entry: verify a Google ID token directly via Google's tokeninfo."""
        resp = requests.get(GOOGLE_TOKENINFO_URI, params={"id_token": id_token}, timeout=30)
        if resp.status_code != 200:
            raise GoogleAuthError(f"id_token verification failed ({resp.status_code})")
        return _validate_claims(resp.json())

    def find_or_create_user(self, claims):
        from app_ib.models import CustomUser, UserProfile
        email = claims["email"].strip().lower()
        user = CustomUser.objects.filter(username=email).first()
        created = False
        if not user:
            user = CustomUser(username=email, type="user", is_active=True, is_delete=False,
                              selfCreated=False)
            user.password = make_password(None)  # unusable password (OAuth-only)
            user.save()
            UserProfile.objects.get_or_create(user=user, defaults={
                "name": claims.get("name", ""), "email": email,
                "profileImageUrl": claims.get("picture", "") or "",
            })
            created = True
        return user, created

    def login_with_code(self, code, redirect_uri):
        claims = self.exchange_code(code, redirect_uri)
        return self._issue(*self.find_or_create_user(claims), claims)

    def login_with_id_token(self, id_token):
        claims = self.verify_id_token(id_token)
        return self._issue(*self.find_or_create_user(claims), claims)

    def _issue(self, user, created, claims):
        refresh = RefreshToken.for_user(user)
        return {
            "accessToken": str(refresh.access_token),
            "refreshToken": str(refresh),
            "userId": user.id,
            "username": user.username,
            "type": user.type,
            "email": claims.get("email"),
            "name": claims.get("name", ""),
            "isNewUser": created,
        }


GOOGLE_AUTH_CONTROLLER = _GoogleAuthController()
