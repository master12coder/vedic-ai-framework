"""Computation-only daily suggestion engine — no LLM needed.

Generates personalized daily advice from transits, hora, panchang,
and ashtakavarga bindus. Works fully offline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

import yaml
from pathlib import Path

from jyotish.compute.chart import ChartData
from jyotish.compute.transit import compute_transits
from jyotish.compute.panchang import compute_panchang
from jyotish.compute.ashtakavarga import compute_ashtakavarga
from jyotish.domain.constants.signs import SIGNS
from jyotish.domain.constants.astro import MAX_DAY_RATING
from jyotish.utils.logging_config import get_logger

logger = get_logger(__name__)

_WEEKLY_YAML = Path(__file__).parent.parent / "knowledge" / "weekly_routine.yaml"

VARA_PLANETS = {
    "Sunday": "Sun", "Monday": "Moon", "Tuesday": "Mars",
    "Wednesday": "Mercury", "Thursday": "Jupiter",
    "Friday": "Venus", "Saturday": "Saturn",
}

PLANET_COLORS = {
    "Sun": "Red/Saffron", "Moon": "White/Cream", "Mars": "Red/Orange",
    "Mercury": "Green", "Jupiter": "Yellow", "Venus": "White/Pink",
    "Saturn": "Blue/Black", "Rahu": "Grey/Smoky", "Ketu": "Brown/Grey",
}


@dataclass
class TransitImpact:
    """Impact of a single transiting planet on the natal chart."""
    planet: str
    transit_sign: str
    natal_house: int
    bindus: int
    is_favorable: bool
    description: str


@dataclass
class DailySuggestion:
    """Complete daily suggestion computed without LLM."""
    date: str
    vara: str
    vara_planet: str
    recommended_color: str
    recommended_mantra: str
    good_for: list[str]
    avoid: list[str]
    transit_impacts: list[TransitImpact]
    health_focus: str
    day_rating: int  # 1-MAX_DAY_RATING
    rahu_kaal: str
    nakshatra: str
    tithi: str


def _load_weekly_routine() -> dict[str, Any]:
    """Load weekly routine from YAML."""
    if _WEEKLY_YAML.exists():
        with open(_WEEKLY_YAML) as f:
            return yaml.safe_load(f) or {}
    return {}


def _get_day_name(target: date) -> str:
    """Get English day name from date."""
    return target.strftime("%A")


def _compute_day_rating(transit_impacts: list[TransitImpact]) -> int:
    """Rate the day 1-10 based on transit bindus."""
    if not transit_impacts:
        return 5
    total_bindus = sum(t.bindus for t in transit_impacts)
    avg = total_bindus / len(transit_impacts)
    # Scale: 0-1 bindus avg = 1, 4+ = MAX_DAY_RATING
    return min(MAX_DAY_RATING, max(1, int(avg * 2.5)))


def compute_daily_suggestion(
    chart: ChartData,
    target_date: date | None = None,
) -> DailySuggestion:
    """Compute a daily suggestion for a chart without LLM.

    Args:
        chart: Natal chart data.
        target_date: Date to compute for (default: today).

    Returns:
        DailySuggestion with all daily advice fields.
    """
    if target_date is None:
        target_date = date.today()

    day_name = _get_day_name(target_date)
    vara_planet = VARA_PLANETS.get(day_name, "Sun")

    # Load weekly routine for activity suggestions
    routine = _load_weekly_routine()
    day_key = day_name.lower()
    day_routine = routine.get(day_key, {})

    # Compute transits
    transit_data = compute_transits(chart)

    # Compute ashtakavarga for bindu ratings
    try:
        avarga = compute_ashtakavarga(chart)
    except Exception:
        avarga = None

    transit_impacts: list[TransitImpact] = []
    for t in transit_data.transits:
        sign_idx = SIGNS.index(t.sign) if t.sign in SIGNS else 0
        bindus = 4  # default
        if avarga and t.name in avarga.bhinna:
            bindus = avarga.bhinna[t.name][sign_idx]

        is_favorable = bindus >= 4
        desc = (
            f"{t.name} in {t.sign} (house {t.natal_house_activated}): "
            f"{bindus} bindus — {'favorable' if is_favorable else 'challenging'}"
        )
        transit_impacts.append(TransitImpact(
            planet=t.name, transit_sign=t.sign,
            natal_house=t.natal_house_activated,
            bindus=bindus, is_favorable=is_favorable,
            description=desc,
        ))

    # Build good_for / avoid lists from day routine
    good_for = []
    avoid = []
    if day_routine:
        activity = day_routine.get("activity", "")
        if activity:
            good_for.append(activity)
        avoid_str = day_routine.get("avoid", "")
        if avoid_str:
            avoid.append(avoid_str)

    # Add transit-based advice
    for t in transit_impacts:
        if t.natal_house == 10 and t.is_favorable:
            good_for.append(f"Career actions ({t.planet} transit in 10th)")
        elif t.natal_house == 8 and not t.is_favorable:
            avoid.append(f"Risky ventures ({t.planet} in 8th house)")

    # Mantra for the day
    mantra = day_routine.get("mantra", f"Om {vara_planet}aya Namaha")

    # Panchang for nakshatra/tithi
    try:
        panchang = compute_panchang(
            target_date.strftime("%d/%m/%Y"),
            chart.latitude, chart.longitude,
            chart.timezone_name, chart.place,
        )
        nakshatra = panchang.nakshatra_name
        tithi = f"{panchang.tithi_name} ({panchang.paksha})"
        rahu_kaal = panchang.rahu_kaal
    except Exception:
        nakshatra = "Unknown"
        tithi = "Unknown"
        rahu_kaal = "Unknown"

    # Health focus based on vara planet
    health_map = {
        "Sun": "Heart, eyes, bones — stay hydrated",
        "Moon": "Mind, sleep — practice calm breathing",
        "Mars": "Blood, muscles — moderate exercise",
        "Mercury": "Nervous system, skin — reduce screen time",
        "Jupiter": "Liver, digestion — eat light",
        "Venus": "Kidneys, throat — stay warm",
        "Saturn": "Joints, teeth — gentle stretching",
    }
    health_focus = health_map.get(vara_planet, "General wellness")

    rating = _compute_day_rating(transit_impacts)

    return DailySuggestion(
        date=target_date.strftime("%d/%m/%Y"),
        vara=day_name,
        vara_planet=vara_planet,
        recommended_color=PLANET_COLORS.get(vara_planet, "White"),
        recommended_mantra=mantra,
        good_for=good_for or ["Routine activities"],
        avoid=avoid or ["Nothing specific to avoid"],
        transit_impacts=transit_impacts,
        health_focus=health_focus,
        day_rating=rating,
        rahu_kaal=rahu_kaal,
        nakshatra=nakshatra,
        tithi=tithi,
    )
