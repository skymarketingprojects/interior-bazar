"""
FacebookAuthController — server-side Facebook OAuth (auth-code exchange).

Flow: frontend opens the Facebook login dialog (response_type=code) in a popup and
POSTs the returned `code` with the `redirect_uri` it used. Backend exchanges the code
for an access_token at Facebook's Graph token endpoint using app_id + app_secret, then
reads the profile from /me, find-or-creates a CustomUser (username = email) and issues
the app's own JWT pair. Mirrors GoogleAuthController.
"""
import logging

import requests
from django.conf import settings
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)


def _graph_base():
    version = getattr(settings, "FACEBOOK_GRAPH_VERSION", "v19.0")
    return f"https://graph.facebook.com/{version}"


class FacebookAuthError(Exception):
    pass


class _FacebookAuthController:

    def exchange_code(self, code, redirect_uri):
        """Exchange an auth code for a Facebook access_token; return the profile claims."""
        if not getattr(settings, "FACEBOOK_APP_SECRET", "") or not getattr(settings, "FACEBOOK_APP_ID", ""):
            raise FacebookAuthError("Facebook OAuth app id/secret not configured")
        token_resp = requests.get(f"{_graph_base()}/oauth/access_token", params={
            "client_id": settings.FACEBOOK_APP_ID,
            "client_secret": settings.FACEBOOK_APP_SECRET,
            "redirect_uri": redirect_uri,
            "code": code,
        }, timeout=30)
        if token_resp.status_code != 200:
            raise FacebookAuthError(f"token exchange failed ({token_resp.status_code}): {token_resp.text[:200]}")
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise FacebookAuthError("no access_token in Facebook response")
        return self._fetch_profile(access_token)

    def _fetch_profile(self, access_token):
        resp = requests.get(f"{_graph_base()}/me", params={
            "fields": "id,name,email,picture.type(large)",
            "access_token": access_token,
        }, timeout=30)
        if resp.status_code != 200:
            raise FacebookAuthError(f"profile fetch failed ({resp.status_code}): {resp.text[:200]}")
        profile = resp.json()
        fb_id = profile.get("id")
        if not fb_id:
            raise FacebookAuthError("Facebook profile missing id")
        # Facebook only returns email when the user granted it and has a verified email.
        email = (profile.get("email") or f"fb_{fb_id}@facebook.oauth").strip().lower()
        picture = ""
        pic = profile.get("picture", {})
        if isinstance(pic, dict):
            picture = pic.get("data", {}).get("url", "") or ""
        return {
            "email": email,
            "name": profile.get("name", ""),
            "picture": picture,
        }

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


FACEBOOK_AUTH_CONTROLLER = _FacebookAuthController()
