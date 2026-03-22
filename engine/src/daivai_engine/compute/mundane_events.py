"""Mundane Astrology — eclipse, Jupiter-Saturn cycle, and ingress chart analysis.

Implements:
- Eclipse effects on nations and regions (Brihat Samhita Ch.5)
- Jupiter-Saturn conjunction cycle analysis
- Mesha Sankranti / seasonal ingress charts

Sources: Brihat Samhita (Varahamihira), BPHS Ch.71-75,
         B.V. Raman's Mundane Astrology.
"""

from __future__ import annotations

from datetime import UTC, datetime

import swisseph as swe

from daivai_engine.compute.mundane_chart import (
    _MUNDANE_PLANETS,
    _get_nakshatra,
    _get_planet_longitude,
    _longitude_to_sign,
)
from daivai_engine.constants import FULL_CIRCLE_DEG, SIGN_ELEMENTS, SIGN_LORDS, SIGNS
from daivai_engine.knowledge.loader import load_mundane_rules
from daivai_engine.models.mundane import EclipseEffect, IngressChart, JupiterSaturnCycle


def _date_to_jd(date_str: str) -> float:
    """Convert ISO date string (YYYY-MM-DD) to Julian Day (noon UT)."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=UTC)
    return float(swe.julday(dt.year, dt.month, dt.day, 12.0))


def analyze_eclipse_effects(
    eclipse_date: str,
    eclipse_type: str,
    latitude: float = 23.5,
    longitude: float = 80.0,
) -> EclipseEffect:
    """Analyze effects of a solar or lunar eclipse on nations.

    Computes the eclipse longitude and nakshatra, then applies Brihat Samhita
    rules (Ch.5) to determine affected regions and predicted effects.

    Args:
        eclipse_date: ISO date of eclipse (YYYY-MM-DD).
        eclipse_type: "solar" or "lunar".
        latitude: Geographic latitude for local chart (default: central India).
        longitude: Geographic longitude (default: central India).

    Returns:
        EclipseEffect with affected regions and predictions.
    """
    rules = load_mundane_rules()
    eclipse_nak_effects: dict = rules.get("eclipse_nakshatra_effects", {})
    eclipse_sign_effects: dict = rules.get("eclipse_sign_effects", {})

    jd = _date_to_jd(eclipse_date)

    # For solar eclipse: use Sun's longitude; for lunar: use Moon's longitude
    if eclipse_type == "solar":
        eclipse_lon = _get_planet_longitude(jd, "Sun")
    else:
        eclipse_lon = _get_planet_longitude(jd, "Moon")

    sign_idx, sign_name = _longitude_to_sign(eclipse_lon)
    _nak_idx, nak_name, nak_lord = _get_nakshatra(eclipse_lon)

    # Look up nakshatra effects (normalize name with underscores)
    nak_key = nak_name.replace(" ", "_")
    nak_data: dict = eclipse_nak_effects.get(nak_key, {})

    affected_regions: list[str] = nak_data.get("regions", [f"Regions governed by {sign_name}"])
    nak_effects: list[str] = nak_data.get("effects", [])
    duration_months: int = nak_data.get("duration_months", 3)

    # Add sign-level effects
    sign_effect = eclipse_sign_effects.get(sign_name, "")
    predicted_effects = list(nak_effects)
    if sign_effect:
        predicted_effects.append(sign_effect)

    # Severity: solar eclipses more severe; total > annular > partial
    severity = "severe" if eclipse_type == "solar" else "moderate"

    return EclipseEffect(
        eclipse_type=eclipse_type,
        eclipse_date=eclipse_date,
        eclipse_longitude=eclipse_lon,
        eclipse_sign_index=sign_idx,
        eclipse_sign=sign_name,
        nakshatra=nak_name,
        nakshatra_lord=nak_lord,
        affected_regions=affected_regions,
        predicted_effects=predicted_effects,
        duration_months=duration_months,
        severity=severity,
    )


def analyze_jupiter_saturn_cycle(
    conjunction_date: str,
) -> JupiterSaturnCycle:
    """Analyze a Jupiter-Saturn conjunction for mundane predictions.

    Computes the longitude and sign of the conjunction, determines the element,
    and applies Brihat Samhita / classical cycle rules.

    Args:
        conjunction_date: ISO date of Jupiter-Saturn exact conjunction (YYYY-MM-DD).

    Returns:
        JupiterSaturnCycle with cycle type, themes, and predicted effects.
    """
    rules = load_mundane_rules()
    cycle_rules: dict = rules.get("jupiter_saturn_cycles", {})
    element_themes: dict = cycle_rules.get("element_themes", {})
    sign_themes: dict = cycle_rules.get("sign_themes", {})

    jd = _date_to_jd(conjunction_date)

    jupiter_lon = _get_planet_longitude(jd, "Jupiter")
    _get_planet_longitude(jd, "Saturn")  # computed for cycle context; use Jupiter as primary

    # Use midpoint of the two for conjunction longitude
    # (at exact conjunction they should be very close; use Jupiter as primary)
    conjunction_lon = jupiter_lon

    sign_idx, sign_name = _longitude_to_sign(conjunction_lon)
    element = SIGN_ELEMENTS[sign_idx]

    # Determine cycle type based on element
    # Grand mutation occurs when element shifts (every ~240 years)
    # Regular conjunctions every ~20 years in same element series
    cycle_type = "regular"
    # If conjunction is in first sign of a new element series, it's a grand mutation
    element_first_signs = {
        "Fire": 0,
        "Earth": 1,
        "Air": 2,
        "Water": 3,
    }  # Mesha, Vrish, Mithun, Karka
    if sign_idx in element_first_signs.values():
        cycle_type = "grand_mutation"

    predicted_themes: list[str] = element_themes.get(element, [])
    sign_theme = sign_themes.get(sign_name, "")

    geopolitical_effects: list[str] = []
    economic_effects: list[str] = []
    social_effects: list[str] = []

    # Classify themes by domain
    for theme in predicted_themes:
        tl = theme.lower()
        if any(k in tl for k in ["war", "military", "ideolog", "nationalism", "conflict"]):
            geopolitical_effects.append(theme)
        elif any(
            k in tl
            for k in ["econom", "financial", "real estate", "trade", "resource", "industrial"]
        ):
            economic_effects.append(theme)
        else:
            social_effects.append(theme)

    if sign_theme:
        social_effects.append(f"Sign theme ({sign_name}): {sign_theme}")

    period_years = int(cycle_rules.get("conjunction_period_years", 20))

    return JupiterSaturnCycle(
        conjunction_date=conjunction_date,
        conjunction_longitude=conjunction_lon,
        conjunction_sign_index=sign_idx,
        conjunction_sign=sign_name,
        conjunction_element=element,
        cycle_type=cycle_type,
        cycle_years=period_years,
        predicted_themes=predicted_themes,
        geopolitical_effects=geopolitical_effects,
        economic_effects=economic_effects,
        social_effects=social_effects,
    )


def compute_ingress_chart(
    ingress_date: str,
    ingress_type: str = "mesha_sankranti",
    latitude: float = 28.6,
    longitude: float = 77.2,
    tz_name: str = "Asia/Kolkata",
) -> IngressChart:
    """Compute a Mesha Sankranti or seasonal ingress chart.

    The ingress chart is cast for the exact moment the Sun enters a cardinal
    sign. Mesha Sankranti (Sun enters Aries/Mesha) is the most important for
    annual world predictions.

    Args:
        ingress_date: ISO date of the ingress (YYYY-MM-DD).
        ingress_type: "mesha_sankranti" | "cancer_ingress" | "libra_ingress" | "capricorn_ingress".
        latitude: Latitude for the local ingress chart.
        longitude: Longitude for the local ingress chart.
        tz_name: Timezone name.

    Returns:
        IngressChart with lagna, ruling planet, and planetary positions.
    """
    rules = load_mundane_rules()
    ingress_planet_rules: dict = rules.get("ingress_ruling_planets", {})

    jd = _date_to_jd(ingress_date)

    # Find exact moment Sun enters the target sign
    target_sign_map = {
        "mesha_sankranti": 0,  # Aries/Mesha
        "cancer_ingress": 3,  # Cancer/Karka
        "libra_ingress": 6,  # Libra/Tula
        "capricorn_ingress": 9,  # Capricorn/Makara
    }
    target_sign_idx = target_sign_map.get(ingress_type, 0)
    target_longitude = float(target_sign_idx * 30)

    # Binary search for exact ingress moment (within ±3 days of given date)
    jd_start = jd - 3.0
    jd_end = jd + 3.0
    ingress_jd = _find_sun_ingress(target_longitude, jd_start, jd_end)

    # Get planetary positions at ingress
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa(ingress_jd)

    planetary_positions: dict[str, int] = {}
    for planet_name in _MUNDANE_PLANETS:
        lon = _get_planet_longitude(ingress_jd, planet_name)
        sign_idx, _ = _longitude_to_sign(lon)
        planetary_positions[planet_name] = sign_idx

    # Compute lagna at ingress moment
    _cusps, ascmc = swe.houses_ex(ingress_jd, latitude, longitude, b"W")
    lagna_tropical = ascmc[0]
    lagna_sid = (lagna_tropical - ayanamsha) % FULL_CIRCLE_DEG
    lagna_sign_idx = int(lagna_sid / 30) % 12
    lagna_sign = SIGNS[lagna_sign_idx]
    lagna_lord = SIGN_LORDS[lagna_sign_idx]

    # Sun position at ingress
    sun_sign_idx = planetary_positions["Sun"]
    moon_sign_idx = planetary_positions["Moon"]

    # Day of week at ingress → ruling planet
    ingress_dt = datetime.fromtimestamp((ingress_jd - 2440587.5) * 86400, tz=UTC)
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_name = day_names[ingress_dt.weekday()]
    ruling_planet: str = ingress_planet_rules.get(day_name, "Sun")

    return IngressChart(
        ingress_type=ingress_type,
        ingress_date=ingress_date,
        ingress_longitude=target_longitude,
        lagna_sign_index=lagna_sign_idx,
        lagna_sign=lagna_sign,
        lagna_lord=lagna_lord,
        sun_sign_index=sun_sign_idx,
        sun_sign=SIGNS[sun_sign_idx],
        moon_sign_index=moon_sign_idx,
        moon_sign=SIGNS[moon_sign_idx],
        ruling_planet=ruling_planet,
        planetary_positions=planetary_positions,
    )


def _find_sun_ingress(
    target_longitude: float,
    jd_start: float,
    jd_end: float,
    tolerance: float = 1e-6,
) -> float:
    """Binary search for exact Julian Day when Sun reaches target sidereal longitude."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    max_iterations = 50

    for _ in range(max_iterations):
        jd_mid = (jd_start + jd_end) / 2.0
        if jd_end - jd_start < tolerance:
            return jd_mid

        sun_lon = _get_planet_longitude(jd_mid, "Sun")

        # Handle wraparound at 0°/360°
        diff = (sun_lon - target_longitude + 180) % 360 - 180
        if diff < 0:
            jd_start = jd_mid
        else:
            jd_end = jd_mid

    return (jd_start + jd_end) / 2.0
