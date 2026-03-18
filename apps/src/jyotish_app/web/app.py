"""FastAPI web app — Jyotish AI with Google OAuth and Jinja2 templates.

Entry point for the web dashboard. Sets up middleware, auth, templates,
static files, and route registration. All computation goes through
products/ layer — zero computation here.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path


logger = logging.getLogger(__name__)

_APP_DIR = Path(__file__).parent
_TEMPLATE_DIR = _APP_DIR / "templates"
_STATIC_DIR = _APP_DIR / "static"


def create_app():
    """Create and configure the FastAPI application."""
    try:
        from fastapi import FastAPI, Request
        from fastapi.responses import RedirectResponse
        from fastapi.staticfiles import StaticFiles
        from fastapi.templating import Jinja2Templates
        from starlette.middleware.sessions import SessionMiddleware
    except ImportError as e:
        raise ImportError("Install with: pip install 'jyotish[web]'") from e

    app = FastAPI(title="Jyotish AI", version="2.0.0",
                  description="Vedic Astrology — श्री गणेशाय नमः")

    # ── Middleware ──
    secret = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    app.add_middleware(SessionMiddleware, secret_key=secret, max_age=86400 * 30)

    # ── Static files ──
    if _STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    # ── Templates ──
    templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

    # ── Auth setup ──
    from jyotish_app.web.auth import (
        _AuthRequiredError,
        auth_callback,
        login_redirect,
        logout,
        setup_oauth,
    )
    setup_oauth()

    # ── Auth routes ──
    @app.get("/auth/google")
    async def google_login(request: Request):
        """Redirect to Google OAuth."""
        return await login_redirect(request)

    @app.get("/auth/callback")
    async def google_callback(request: Request):
        """Handle Google OAuth callback."""
        return await auth_callback(request)

    @app.get("/auth/logout")
    async def google_logout(request: Request):
        """Logout and clear session."""
        return logout(request)

    # ── Auth exception handler ──
    @app.exception_handler(_AuthRequiredError)
    async def auth_required_handler(request: Request, exc: _AuthRequiredError):
        return RedirectResponse(url="/", status_code=302)

    # ── Register page routes ──
    from jyotish_app.web.routes import register_routes
    register_routes(app, templates)

    # ── Health check ──
    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "2.0.0"}

    return app
