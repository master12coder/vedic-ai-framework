"""Web route handlers — all page endpoints for the DaivAI dashboard.

Each route gets data from the database or computes via products/ layer,
then passes it to a Jinja2 template. Zero computation in this file.

Sub-modules:
    routes_client — all /client/{id}/* page routes and /api/chart/{id}
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import Response

from daivai_app.web.auth import get_current_user, require_auth
from daivai_app.web.database import (
    create_client,
    get_clients_for_user,
)
from daivai_app.web.routes_client import register_client_routes


logger = logging.getLogger(__name__)


def register_routes(app: FastAPI, templates: Jinja2Templates) -> None:
    """Register all page routes on the FastAPI app."""

    # Register client-specific routes, passing the context builder
    register_client_routes(app, templates, _build_chart_context)

    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request) -> Response:
        """Login page or redirect to dashboard if authenticated."""
        user = get_current_user(request)
        if user:
            return RedirectResponse(url="/dashboard", status_code=302)
        error = request.query_params.get("error", "")
        return templates.TemplateResponse(
            request,
            "login.html",
            context={
                "error": error,
            },
        )

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard(request: Request) -> Response:
        """Client list for logged-in user."""
        user = require_auth(request)
        clients = get_clients_for_user(user["id"])
        client_data = []
        for c in clients:
            chart = json.loads(c.chart_json)
            client_data.append(
                {
                    "id": c.id,
                    "name": c.name,
                    "dob": c.dob,
                    "place": c.place,
                    "lagna": chart.get("lagna_sign", ""),
                    "lagna_hi": chart.get("lagna_sign_hi", ""),
                }
            )
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            context={
                "user": user,
                "clients": client_data,
            },
        )

    @app.get("/new", response_class=HTMLResponse)
    async def new_client_form(request: Request) -> Response:
        """Show the birth data input form."""
        user = require_auth(request)
        return templates.TemplateResponse(
            request,
            "input_form.html",
            context={
                "user": user,
            },
        )

    @app.post("/generate")
    async def generate_chart(
        request: Request,
        name: str = Form(...),
        dob: str = Form(...),
        tob: str = Form(...),
        place: str = Form(""),
        lat: float = Form(0),
        lon: float = Form(0),
        gender: str = Form("Male"),
    ) -> RedirectResponse:
        """Compute chart and save to database."""
        user = require_auth(request)

        from daivai_engine.compute.chart import compute_chart

        tz_name = "Asia/Kolkata"
        if lat == 0 and lon == 0:
            lat, lon = 28.6139, 77.2090  # Default Delhi

        chart = compute_chart(
            name=name,
            dob=dob,
            tob=tob,
            lat=lat,
            lon=lon,
            tz_name=tz_name,
            gender=gender,
        )
        chart_json = chart.model_dump_json()

        client = create_client(
            user_id=user["id"],
            name=name,
            dob=dob,
            tob=tob,
            place=place or "India",
            lat=lat,
            lon=lon,
            gender=gender,
            chart_json=chart_json,
        )

        return RedirectResponse(url=f"/client/{client.id}", status_code=302)


def _build_chart_context(chart_data: dict[str, Any]) -> dict[str, Any]:
    """Build template context from chart JSON — call products/ for computations."""
    from daivai_engine.compute.ashtakavarga import compute_ashtakavarga
    from daivai_engine.compute.dasha import compute_mahadashas, find_current_dasha
    from daivai_engine.compute.dosha import detect_all_doshas
    from daivai_engine.compute.strength import compute_shadbala
    from daivai_engine.compute.yoga import detect_all_yogas
    from daivai_engine.models.chart import ChartData
    from daivai_products.interpret.context import build_lordship_context

    chart = ChartData.model_validate(chart_data)
    lordship = build_lordship_context(chart.lagna_sign)

    benefics = {e["planet"] for e in lordship.get("functional_benefics", [])}
    malefics = {e["planet"] for e in lordship.get("functional_malefics", [])}
    yk = lordship.get("yogakaraka", {})
    yogakaraka = yk.get("planet", "") if isinstance(yk, dict) else ""

    mahadashas = compute_mahadashas(chart)
    md, ad, _pd = find_current_dasha(chart)
    yogas = [y for y in detect_all_yogas(chart) if y.is_present]
    doshas = detect_all_doshas(chart)
    shadbala = compute_shadbala(chart)
    avk = compute_ashtakavarga(chart)

    return {
        "lordship": lordship,
        "benefics": benefics,
        "malefics": malefics,
        "yogakaraka": yogakaraka,
        "mahadashas": mahadashas,
        "current_md": md,
        "current_ad": ad,
        "yogas": yogas,
        "doshas": doshas,
        "shadbala": shadbala,
        "ashtakavarga": avk,
        "recommended_stones": lordship.get("recommended_stones", []),
        "prohibited_stones": lordship.get("prohibited_stones", []),
    }
