"""
LinkedInAuthController — server-side LinkedIn OAuth (auth-code exchange, OIDC).

Flow: frontend opens LinkedIn's authorization page (response_type=code, scope
"openid profile email") in a popup and POSTs the returned `code` with the
`redirect_uri` it used. Backend exchanges the code for an access_token at LinkedIn's
token endpoint using client_id + client_secret, reads the profile from the OpenID
Connect /userinfo endpoint, find-or-creates a CustomUser (username = email) and issues
the app's own JWT pair. Mirrors GoogleAuthController.
"""
import logging

import requests
from django.conf import settings
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)

LINKEDIN_TOKEN_URI = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URI = "https://api.linkedin.com/v2/userinfo"


class LinkedInAuthError(Exception):
    pass


class _LinkedInAuthController:

    def exchange_code(self, code, redirect_uri):
        """Exchange an auth code for a LinkedIn access_token; return userinfo claims."""
        if not getattr(settings, "LINKEDIN_CLIENT_SECRET", "") or not getattr(settings, "LINKEDIN_CLIENT_ID", ""):
            raise LinkedInAuthError("LinkedIn OAuth client id/secret not configured")
        token_resp = requests.post(LINKEDIN_TOKEN_URI, data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "client_secret": settings.LINKEDIN_CLIENT_SECRET,
        }, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=30)
        if token_resp.status_code != 200:
            raise LinkedInAuthError(f"token exchange failed ({token_resp.status_code}): {token_resp.text[:200]}")
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise LinkedInAuthError("no access_token in LinkedIn response")
        return self._fetch_userinfo(access_token)

    def _fetch_userinfo(self, access_token):
        resp = requests.get(LINKEDIN_USERINFO_URI,
                            headers={"Authorization": f"Bearer {access_token}"}, timeout=30)
        if resp.status_code != 200:
            raise LinkedInAuthError(f"userinfo fetch failed ({resp.status_code}): {resp.text[:200]}")
        info = resp.json()
        email = info.get("email")
        if not email:
            raise LinkedInAuthError("LinkedIn userinfo missing email (grant the 'email' scope)")
        return {
            "email": email.strip().lower(),
            "name": info.get("name", "") or " ".join(
                p for p in [info.get("given_name", ""), info.get("family_name", "")] if p
            ),
            "picture": info.get("picture", "") or "",
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


LINKEDIN_AUTH_CONTROLLER = _LinkedInAuthController()
