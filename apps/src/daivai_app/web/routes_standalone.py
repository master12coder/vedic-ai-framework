"""Standalone web routes — match and muhurta pages (no saved client needed).

These routes do NOT require a client in the database; they compute
on-the-fly from form input. Still require authentication.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import Response

from daivai_app.web.auth import require_auth


logger = logging.getLogger(__name__)

# Hindi labels for muhurta purposes
_PURPOSE_HINDI: dict[str, str] = {
    "marriage": "विवाह",
    "property": "गृह प्रवेश",
    "business": "व्यापार",
    "travel": "यात्रा",
}


def register_standalone_routes(app: FastAPI, templates: Jinja2Templates) -> None:
    """Register match and muhurta routes on the FastAPI app."""

    # ── Compatibility Matching ─────────────────────────────────────────

    @app.get("/match", response_class=HTMLResponse)
    async def match_form(request: Request) -> Response:
        """Show the two-person compatibility form."""
        user = require_auth(request)
        return templates.TemplateResponse(
            request,
            "match_form.html",
            context={
                "user": user,
            },
        )

    @app.post("/match/result", response_class=HTMLResponse)
    async def match_result(
        request: Request,
        name1: str = Form(...),
        dob1: str = Form(...),
        tob1: str = Form(...),
        lat1: float = Form(25.3176),
        lon1: float = Form(83.0067),
        gender1: str = Form("Male"),
        name2: str = Form(...),
        dob2: str = Form(...),
        tob2: str = Form(...),
        lat2: float = Form(25.3176),
        lon2: float = Form(83.0067),
        gender2: str = Form("Female"),
    ) -> Response:
        """Compute both charts and run ashtakoot matching."""
        user = require_auth(request)

        from daivai_engine.compute.chart import compute_chart
        from daivai_engine.compute.matching import compute_ashtakoot

        chart1 = compute_chart(
            name=name1,
            dob=dob1,
            tob=tob1,
            lat=lat1,
            lon=lon1,
            gender=gender1,
        )
        chart2 = compute_chart(
            name=name2,
            dob=dob2,
            tob=tob2,
            lat=lat2,
            lon=lon2,
            gender=gender2,
        )

        moon1 = chart1.planets["Moon"]
        moon2 = chart2.planets["Moon"]

        result = compute_ashtakoot(
            person1_nakshatra_index=moon1.nakshatra_index,
            person1_moon_sign=moon1.sign_index,
            person2_nakshatra_index=moon2.nakshatra_index,
            person2_moon_sign=moon2.sign_index,
        )

        return templates.TemplateResponse(
            request,
            "match_result.html",
            context={
                "user": user,
                "name1": name1,
                "name2": name2,
                "result": result,
            },
        )

    # ── Muhurta ────────────────────────────────────────────────────────

    @app.get("/muhurta", response_class=HTMLResponse)
    async def muhurta_form(request: Request) -> Response:
        """Show the muhurta search form."""
        user = require_auth(request)
        return templates.TemplateResponse(
            request,
            "muhurta_form.html",
            context={
                "user": user,
            },
        )

    @app.post("/muhurta/result", response_class=HTMLResponse)
    async def muhurta_result(
        request: Request,
        purpose: str = Form(...),
        from_date: str = Form(...),
        to_date: str = Form(...),
        lat: float = Form(25.3176),
        lon: float = Form(83.0067),
    ) -> Response:
        """Find auspicious dates for the given purpose and date range."""
        user = require_auth(request)

        from daivai_engine.compute.datetime_utils import parse_birth_datetime
        from daivai_engine.compute.muhurta import find_muhurta

        tz_name = "Asia/Kolkata"
        start = parse_birth_datetime(from_date, "00:00", tz_name)
        end = parse_birth_datetime(to_date, "23:59", tz_name)

        results = find_muhurta(
            purpose=purpose,
            lat=lat,
            lon=lon,
            tz_name=tz_name,
            start_date=start,
            end_date=end,
        )

        purpose_hi = _PURPOSE_HINDI.get(purpose, purpose)

        return templates.TemplateResponse(
            request,
            "muhurta_result.html",
            context={
                "user": user,
                "results": results,
                "purpose_hi": purpose_hi,
            },
        )
