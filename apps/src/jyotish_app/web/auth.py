"""Google OAuth 2.0 authentication for the web app.

Handles login flow, session management via signed cookies,
and role-based access control.
"""
from __future__ import annotations

import os
from typing import Any

from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from starlette.responses import RedirectResponse

from jyotish_app.web.database import get_or_create_user


# ── OAuth setup ──────────────────────────────────────────────────────────

oauth = OAuth()


def setup_oauth() -> None:
    """Register Google as OAuth provider. Call once at app startup."""
    oauth.register(
        name="google",
        client_id=os.environ.get("GOOGLE_CLIENT_ID", ""),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


async def login_redirect(request: Request) -> RedirectResponse:
    """Start Google OAuth flow — redirect to Google consent screen."""
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(request, str(redirect_uri))


async def auth_callback(request: Request) -> RedirectResponse:
    """Handle Google OAuth callback — create session and redirect to dashboard."""
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo", {})

    if not userinfo.get("sub"):
        return RedirectResponse(url="/?error=auth_failed", status_code=302)

    # Check allowed emails (if configured)
    allowed = os.environ.get("ALLOWED_EMAILS", "")
    if allowed:
        allowed_list = [e.strip().lower() for e in allowed.split(",") if e.strip()]
        if allowed_list and userinfo.get("email", "").lower() not in allowed_list:
            return RedirectResponse(url="/?error=not_allowed", status_code=302)

    user = get_or_create_user(
        google_id=userinfo["sub"],
        email=userinfo.get("email", ""),
        name=userinfo.get("name", ""),
        picture_url=userinfo.get("picture"),
    )

    request.session["user_id"] = user.id
    request.session["user_name"] = user.name
    request.session["user_picture"] = user.picture_url
    request.session["user_role"] = user.role

    return RedirectResponse(url="/dashboard", status_code=302)


def logout(request: Request) -> RedirectResponse:
    """Clear session and redirect to home."""
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)


# ── Session helpers ──────────────────────────────────────────────────────

def get_current_user(request: Request) -> dict[str, Any] | None:
    """Get current user from session. Returns None if not authenticated."""
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    return {
        "id": user_id,
        "name": request.session.get("user_name", ""),
        "picture": request.session.get("user_picture"),
        "role": request.session.get("user_role", "family"),
    }


def require_auth(request: Request) -> dict[str, Any]:
    """Get current user or raise redirect. Use in route handlers."""
    user = get_current_user(request)
    if user is None:
        raise _AuthRequiredError()
    return user


class _AuthRequiredError(Exception):
    """Raised when auth is required but user is not logged in."""
