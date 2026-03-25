"""FastAPI web app — DaivAI with Google OAuth and Jinja2 templates.

Entry point for the web dashboard. Sets up middleware, auth, templates,
static files, error handlers, and route registration.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)

_APP_DIR = Path(__file__).parent
_TEMPLATE_DIR = _APP_DIR / "templates"
_STATIC_DIR = _APP_DIR / "static"


def create_app() -> Any:
    """Create and configure the FastAPI application."""
    try:
        from fastapi import FastAPI, Request
        from fastapi.responses import RedirectResponse
        from fastapi.staticfiles import StaticFiles
        from fastapi.templating import Jinja2Templates
        from starlette.middleware.sessions import SessionMiddleware
        from starlette.responses import Response
    except ImportError as e:
        raise ImportError("Install with: pip install 'daivai[web]'") from e

    app = FastAPI(
        title="DaivAI — दैव AI",
        version="2.0.0",
        description="DaivAI — Divine Intelligence, Computational Precision",
    )

    # ── Middleware ──
    secret = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    app.add_middleware(
        SessionMiddleware, secret_key=secret, max_age=86400 * 30, https_only=False, same_site="lax"
    )

    # ── Security headers ──
    @app.middleware("http")
    async def security_headers(request: Request, call_next: Any) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # ── Static files ──
    if _STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    # ── Templates ──
    templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

    # ── Auth setup ──
    from daivai_app.web.auth import (
        _AuthRequiredError,
        auth_callback,
        login_redirect,
        logout,
        setup_oauth,
    )

    setup_oauth()

    # ── Auth routes ──
    @app.get("/auth/google")
    async def google_login(request: Request) -> RedirectResponse:
        return await login_redirect(request)

    @app.get("/auth/callback")
    async def google_callback(request: Request) -> RedirectResponse:
        return await auth_callback(request)

    @app.get("/auth/logout")
    async def google_logout(request: Request) -> RedirectResponse:
        return logout(request)

    # ── Error handlers ──
    @app.exception_handler(_AuthRequiredError)
    async def auth_required_handler(request: Request, exc: _AuthRequiredError) -> RedirectResponse:
        return RedirectResponse(url="/", status_code=302)

    @app.exception_handler(404)
    async def not_found(request: Request, exc: Exception) -> Response:
        return templates.TemplateResponse(
            request, "error.html", context={"code": 404}, status_code=404
        )

    @app.exception_handler(500)
    async def server_error(request: Request, exc: Exception) -> Response:
        logger.exception("Internal server error: %s", exc)
        return templates.TemplateResponse(
            request, "error.html", context={"code": 500}, status_code=500
        )

    # ── Register routes ──
    from daivai_app.web.routes import register_routes

    register_routes(app, templates)

    from daivai_app.web.routes_standalone import register_standalone_routes

    register_standalone_routes(app, templates)

    # ── Health check ──
    @app.get("/health")
    async def health() -> dict[str, str]:
        status = {"status": "ok", "version": "2.0.0", "timestamp": datetime.now().isoformat()}
        try:
            import swisseph  # noqa: F401

            status["engine"] = "swiss_ephemeris_available"
        except ImportError:
            status["engine"] = "swiss_ephemeris_missing"
        try:
            from daivai_app.web.database import get_engine

            get_engine()
            status["database"] = "connected"
        except Exception:
            status["database"] = "error"
        return status

    return app
