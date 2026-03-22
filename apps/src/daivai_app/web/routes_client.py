"""Web route handlers — client-specific page endpoints.

All routes under /client/{client_id}/ — overview, dasha, ratna,
kundali preview, PDF download, daily, navamsha, and API.
"""

from __future__ import annotations

import io
import json
import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import Response

from daivai_app.web.auth import require_auth
from daivai_app.web.database import get_client


logger = logging.getLogger(__name__)


def register_client_routes(
    app: FastAPI,
    templates: Jinja2Templates,
    build_chart_context: Any,
) -> None:
    """Register client-specific page routes on the FastAPI app.

    Args:
        app: FastAPI application instance.
        templates: Jinja2Templates instance.
        build_chart_context: Callable that builds template context from chart JSON dict.
    """

    @app.get("/client/{client_id}", response_class=HTMLResponse)
    async def client_overview(request: Request, client_id: int) -> Response:
        """Full kundali overview page for a client."""
        user = require_auth(request)
        client = get_client(client_id)
        if not client or client.user_id != user["id"]:
            return RedirectResponse(url="/dashboard", status_code=302)

        chart_data = json.loads(client.chart_json)
        ctx = build_chart_context(chart_data)

        return templates.TemplateResponse(
            "overview.html",
            {
                "request": request,
                "user": user,
                "client": client,
                "chart": chart_data,
                **ctx,
            },
        )

    @app.get("/client/{client_id}/dasha", response_class=HTMLResponse)
    async def dasha_page(request: Request, client_id: int) -> Response:
        """Dasha deep-dive page."""
        user = require_auth(request)
        client = get_client(client_id)
        if not client or client.user_id != user["id"]:
            return RedirectResponse(url="/dashboard", status_code=302)

        chart_data = json.loads(client.chart_json)
        ctx = build_chart_context(chart_data)

        return templates.TemplateResponse(
            "dasha.html",
            {
                "request": request,
                "user": user,
                "client": client,
                "chart": chart_data,
                **ctx,
            },
        )

    @app.get("/client/{client_id}/ratna", response_class=HTMLResponse)
    async def ratna_page(request: Request, client_id: int) -> Response:
        """Gemstone recommendations page."""
        user = require_auth(request)
        client = get_client(client_id)
        if not client or client.user_id != user["id"]:
            return RedirectResponse(url="/dashboard", status_code=302)

        chart_data = json.loads(client.chart_json)
        ctx = build_chart_context(chart_data)

        return templates.TemplateResponse(
            "ratna.html",
            {
                "request": request,
                "user": user,
                "client": client,
                "chart": chart_data,
                **ctx,
            },
        )

    @app.get("/client/{client_id}/kundali", response_class=HTMLResponse)
    async def kundali_preview(request: Request, client_id: int) -> Response:
        """HTML kundali preview — beautiful print-ready view."""
        user = require_auth(request)
        client = get_client(client_id)
        if not client or client.user_id != user["id"]:
            return RedirectResponse(url="/dashboard", status_code=302)

        from daivai_engine.models.chart import ChartData
        from daivai_products.plugins.kundali.pdf import generate_html

        chart = ChartData.model_validate_json(client.chart_json)
        html = generate_html(chart, fmt="detailed", standalone=False)
        return HTMLResponse(content=html)

    @app.get("/client/{client_id}/pdf")
    async def download_pdf(request: Request, client_id: int) -> Response:
        """Download kundali PDF."""
        user = require_auth(request)
        client = get_client(client_id)
        if not client or client.user_id != user["id"]:
            return RedirectResponse(url="/dashboard", status_code=302)

        from daivai_engine.models.chart import ChartData
        from daivai_products.plugins.kundali.pdf import generate_pdf

        chart = ChartData.model_validate_json(client.chart_json)
        pdf_bytes = generate_pdf(chart, fmt="detailed")
        assert pdf_bytes is not None

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=kundali_{client.name}.pdf"},
        )

    @app.get("/client/{client_id}/daily", response_class=HTMLResponse)
    async def daily_page(request: Request, client_id: int) -> Response:
        """Daily guidance page with transit-based suggestions."""
        user = require_auth(request)
        client = get_client(client_id)
        if not client or client.user_id != user["id"]:
            return RedirectResponse(url="/dashboard", status_code=302)

        chart_data = json.loads(client.chart_json)

        from daivai_engine.compute.daily import compute_daily_suggestion
        from daivai_engine.models.chart import ChartData

        chart = ChartData.model_validate(chart_data)
        suggestion = compute_daily_suggestion(chart)

        return templates.TemplateResponse(
            "daily.html",
            {
                "request": request,
                "user": user,
                "client": client,
                "chart": chart_data,
                "suggestion": suggestion,
            },
        )

    @app.get("/client/{client_id}/navamsha", response_class=HTMLResponse)
    async def navamsha_page(request: Request, client_id: int) -> Response:
        """D9 Navamsha divisional chart page."""
        user = require_auth(request)
        client = get_client(client_id)
        if not client or client.user_id != user["id"]:
            return RedirectResponse(url="/dashboard", status_code=302)

        chart_data = json.loads(client.chart_json)
        ctx = build_chart_context(chart_data)

        from daivai_engine.compute.divisional import (
            compute_navamsha,
            get_vargottam_planets,
        )
        from daivai_engine.models.chart import ChartData

        chart = ChartData.model_validate(chart_data)
        d9_positions = compute_navamsha(chart)
        vargottam = get_vargottam_planets(chart)

        return templates.TemplateResponse(
            "navamsha.html",
            {
                "request": request,
                "user": user,
                "client": client,
                "chart": chart_data,
                "d9_positions": d9_positions,
                "vargottam": vargottam,
                **ctx,
            },
        )

    @app.get("/api/chart/{client_id}")
    async def api_chart(request: Request, client_id: int) -> dict[str, Any]:
        """JSON API for chart data."""
        user = require_auth(request)
        client = get_client(client_id)
        if not client or client.user_id != user["id"]:
            return {"error": "not found"}
        result: dict[str, Any] = json.loads(client.chart_json)
        return result
