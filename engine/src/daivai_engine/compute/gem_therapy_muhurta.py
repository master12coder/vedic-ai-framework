"""Gem therapy wearing muhurta computation."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from daivai_engine.compute.panchang import compute_panchang
from daivai_engine.knowledge.loader import load_gem_therapy_rules, load_gemstone_logic
from daivai_engine.models.chart import ChartData
from daivai_engine.models.gem_therapy import WearingMuhurta


def compute_wearing_muhurta(
    gem_or_planet: str,
    birth_chart: ChartData,
    start_date: datetime,
    days_to_scan: int = 60,
    max_results: int = 5,
) -> list[WearingMuhurta]:
    """Find auspicious dates for wearing a specific gemstone.

    Scans panchang from start_date for days where:
    - Weekday matches the planet's auspicious day
    - Nakshatra is favorable for the planet
    - Tithi is auspicious (not 4th, 8th, 14th, Amavasya)

    Args:
        gem_or_planet: Stone name (e.g., "Emerald") or planet (e.g., "Mercury").
        birth_chart: Native's birth chart (provides location for panchang).
        start_date: Earliest date to consider.
        days_to_scan: How many days forward to scan (default 60).
        max_results: Maximum number of auspicious dates to return.

    Returns:
        List of WearingMuhurta sorted by score (most auspicious first).
    """
    rules = load_gem_therapy_rules()
    gem_logic = load_gemstone_logic()
    stone_to_planet = rules.get("stone_to_planet", {})
    planet_to_stone = rules.get("planet_to_stone", {})
    wearing_naks = rules.get("wearing_nakshatras", {})
    unfavorable_tithis = set(rules.get("unfavorable_tithis", {}).get("indices", [4, 8, 14, 15, 29]))
    gemstones = gem_logic.get("gemstones", {})

    # Resolve planet name
    if gem_or_planet in planet_to_stone:
        planet = gem_or_planet
        stone_name = planet_to_stone[planet]
    elif gem_or_planet in stone_to_planet:
        planet = stone_to_planet[gem_or_planet]
        stone_name = gem_or_planet
    else:
        planet = gem_or_planet
        stone_name = planet_to_stone.get(planet, gem_or_planet)

    gem_data = gemstones.get(planet, {})
    planet_day = gem_data.get("day", "")  # e.g., "Sunday"
    hora_str = gem_data.get("hora", "")

    nak_data = wearing_naks.get(planet, {})
    primary_naks: set[str] = set(nak_data.get("primary", []))
    secondary_naks: set[str] = set(nak_data.get("secondary", []))

    is_blue_sapphire = stone_name == "Blue Sapphire"

    lat = birth_chart.latitude
    lon = birth_chart.longitude
    tz = birth_chart.timezone_name

    candidates: list[WearingMuhurta] = []
    current = start_date.replace(hour=12, minute=0, second=0, microsecond=0)

    for _ in range(days_to_scan):
        date_str = current.strftime("%d/%m/%Y")
        try:
            panchang = compute_panchang(date_str, lat, lon, tz)
        except Exception:
            current += timedelta(days=1)
            continue

        score, reasons = _score_muhurta(
            panchang, planet_day, primary_naks, secondary_naks, unfavorable_tithis
        )

        if score > 0:
            candidates.append(
                WearingMuhurta(
                    date=date_str,
                    vara=panchang.vara,
                    nakshatra=panchang.nakshatra_name,
                    tithi_name=panchang.tithi_name,
                    paksha=panchang.paksha,
                    score=round(score, 2),
                    reasons=reasons,
                    hora_timing=hora_str or f"{planet} hora after sunrise on {planet_day}",
                    is_trial_date=is_blue_sapphire,
                )
            )

        current += timedelta(days=1)

    candidates.sort(key=lambda m: m.score, reverse=True)
    return candidates[:max_results]


def _score_muhurta(
    panchang: Any,
    planet_day: str,
    primary_naks: set[str],
    secondary_naks: set[str],
    unfavorable_tithis: set[int],
) -> tuple[float, list[str]]:
    """Score a panchang day for gem wearing auspiciousness.

    Returns (score, reasons). Score <= 0 means skip this day.
    """
    score = 0.0
    reasons: list[str] = []

    # Day match is mandatory for primary consideration
    if panchang.vara == planet_day:
        score += 3.0
        reasons.append(f"Auspicious day: {planet_day}")
    else:
        # Day mismatch — still score if nakshatra is exceptionally good
        score -= 1.0

    # Nakshatra scoring
    if panchang.nakshatra_name in primary_naks:
        score += 2.0
        reasons.append(f"Primary nakshatra: {panchang.nakshatra_name}")
    elif panchang.nakshatra_name in secondary_naks:
        score += 1.0
        reasons.append(f"Secondary nakshatra: {panchang.nakshatra_name}")

    # Tithi scoring (1-indexed; panchang tithi_index is 0-indexed)
    tithi_1indexed = panchang.tithi_index + 1
    if tithi_1indexed in unfavorable_tithis:
        score -= 2.5
        reasons.append(f"Unfavorable tithi: {panchang.tithi_name}")
    else:
        score += 0.5
        reasons.append(f"Acceptable tithi: {panchang.tithi_name}")

    # Paksha — Shukla (waxing) preferred
    if panchang.paksha == "Shukla":
        score += 0.5
        reasons.append("Shukla paksha (waxing moon) — auspicious")

    return score, reasons
