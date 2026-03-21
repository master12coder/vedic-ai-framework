"""Vastu Purusha Mandala computations — zone strengths, room recommendations,
and Ayadi Shadvarga entry door analysis.

All zone data, room rules, and field classifications are loaded from
engine/knowledge/vastu_rules.yaml. No Vastu knowledge is hardcoded here.
"""

from __future__ import annotations

from typing import Any

from daivai_engine.constants import DUSTHANAS, KENDRAS, SIGN_LORDS, TRIKONAS
from daivai_engine.knowledge.loader import load_vastu_rules
from daivai_engine.models.chart import ChartData, PlanetData
from daivai_engine.models.vastu import (
    AyadiField,
    DoorAnalysis,
    RoomRecommendation,
    VastuZone,
)


# -- Dignity score lookup (mirrors vastu.py -- both files are self-contained) -

_DIGNITY_SCORES: dict[str, float] = {
    "exalted": 100.0,
    "mooltrikona": 82.0,
    "own": 75.0,
    "neutral": 50.0,
    "debilitated": 15.0,
}

_KENDRA = set(KENDRAS)
_TRIKONA = set(TRIKONAS)
_DUSTHANA = set(DUSTHANAS)


def _planet_score(planet: PlanetData) -> float:
    """Compute 0-100 strength for a planet (used for zone and room scoring).

    Args:
        planet: PlanetData from the natal chart.

    Returns:
        Float in [0.0, 100.0].
    """
    base = _DIGNITY_SCORES.get(planet.dignity, 50.0)

    if planet.house in _KENDRA:
        base = min(100.0, base * 1.20)
    elif planet.house in _TRIKONA:
        base = min(100.0, base * 1.15)
    elif planet.house in _DUSTHANA:
        base = max(0.0, base * 0.60)

    if planet.is_retrograde:
        base = min(100.0, base * 1.05)
    if planet.is_combust:
        base = max(0.0, base * 0.70)

    return round(base, 2)


# ── Mandala zones ─────────────────────────────────────────────────────────────


def compute_mandala_zones(chart: ChartData) -> list[VastuZone]:
    """Compute Vastu Purusha Mandala zone strengths from the natal chart.

    The Mandala has 8 directional zones (N, NE, E, SE, S, SW, W, NW) plus
    the Center (Brahmasthana). Each zone's strength equals its ruling
    planet's natal chart strength score. The Center defaults to 50.

    Args:
        chart: Computed birth chart data.

    Returns:
        List of VastuZone objects for all 9 zones.
    """
    rules: dict[str, Any] = load_vastu_rules()
    zone_data: dict[str, Any] = rules.get("mandala_zones", {})

    zones: list[VastuZone] = []
    for direction, info in zone_data.items():
        planet_name: str | None = info.get("planet")

        score = 50.0  # Brahmasthana has no planet — neutral default
        if planet_name and planet_name in chart.planets:
            score = _planet_score(chart.planets[planet_name])

        zones.append(
            VastuZone(
                direction=direction,
                direction_hi=info.get("direction_hi", direction),
                planet=planet_name if planet_name else "Brahma",
                element=info.get("element", "Space"),
                element_hi=info.get("element_hi", "आकाश"),
                deity=info.get("deity", ""),
                color=info.get("color", ""),
                significance=info.get("significance", ""),
                zone_strength=score,
            )
        )

    return zones


# ── Room recommendations ──────────────────────────────────────────────────────


def compute_room_recommendations(chart: ChartData) -> list[RoomRecommendation]:
    """Generate personalised room placement recommendations from the natal chart.

    Each room type has a classically ideal Vastu direction. Whether that
    direction is auspicious for this native depends on the ruling planet's
    strength in the natal chart. Rooms marked ``lagna_lord`` in the YAML
    are resolved dynamically to the actual lagna lord planet and direction.

    Args:
        chart: Computed birth chart data.

    Returns:
        List of RoomRecommendation objects for all standard room types.
    """
    rules: dict[str, Any] = load_vastu_rules()
    room_rules: dict[str, Any] = rules.get("room_rules", {})
    planet_dirs: dict[str, str] = rules.get("planet_directions", {})
    direction_hi: dict[str, str] = rules.get("direction_hi", {})

    lagna_lord = SIGN_LORDS[chart.lagna_sign_index]
    lagna_lord_dir = planet_dirs.get(lagna_lord, "North")

    recommendations: list[RoomRecommendation] = []

    for room_key, info in room_rules.items():
        ideal_dir: str = info.get("ideal_direction", "North")
        alt_dir: str = info.get("alternate_direction", "North")
        planet_name: str = info.get("planet", "Mercury")

        # Resolve dynamic lagna_lord placeholder
        if ideal_dir == "lagna_lord":
            ideal_dir = lagna_lord_dir
        if planet_name == "lagna_lord":
            planet_name = lagna_lord

        planet = chart.planets.get(planet_name)
        score = _planet_score(planet) if planet is not None else 50.0

        recommendations.append(
            RoomRecommendation(
                room=room_key.replace("_", " "),
                ideal_direction=ideal_dir,
                ideal_direction_hi=info.get("direction_hi", direction_hi.get(ideal_dir, ideal_dir)),
                alternate_direction=alt_dir,
                planet=planet_name,
                planet_strength=score,
                is_favorable=score >= 50.0,
                reason=info.get("reason", ""),
            )
        )

    return recommendations


# ── Ayadi Shadvarga door analysis ─────────────────────────────────────────────


def analyze_entry_door(chart: ChartData) -> DoorAnalysis:
    """Recommend a main entrance direction using Ayadi Shadvarga principles.

    The Ayadi Shadvarga defines 32 energy fields around the building's
    perimeter. Fields classified as Devta (auspicious) in the lagna lord's
    direction are ideal. If none exist there, the algorithm falls back to
    any Devta field in the North (Kubera's direction), then to field 1.

    Args:
        chart: Computed birth chart data.

    Returns:
        DoorAnalysis with the recommended field, direction, and guidance text.
    """
    rules: dict[str, Any] = load_vastu_rules()
    ayadi_fields: list[dict[str, Any]] = rules.get("ayadi_fields", [])
    planet_dirs: dict[str, str] = rules.get("planet_directions", {})
    direction_hi: dict[str, str] = rules.get("direction_hi", {})

    lagna_lord = SIGN_LORDS[chart.lagna_sign_index]
    lagna_direction = planet_dirs.get(lagna_lord, "North")

    # Priority 1: Devta field in lagna lord's direction
    preferred: dict[str, Any] | None = next(
        (
            f
            for f in ayadi_fields
            if f.get("direction") == lagna_direction and f.get("classification") == "Devta"
        ),
        None,
    )

    # Priority 2: Devta field in North (Kubera — universally auspicious)
    if preferred is None:
        preferred = next(
            (
                f
                for f in ayadi_fields
                if f.get("direction") == "North" and f.get("classification") == "Devta"
            ),
            None,
        )

    # Fallback: first field in the list
    if preferred is None and ayadi_fields:
        preferred = ayadi_fields[0]

    if preferred is None:
        preferred = {
            "field": 1,
            "direction": "North",
            "classification": "Devta",
            "deity": "Kubera",
            "quality": "Auspicious",
        }

    recommended_dir: str = preferred.get("direction", "North")
    alignment = "Excellent" if recommended_dir == lagna_direction else "Good"

    ayadi = AyadiField(
        field_number=preferred.get("field", 1),
        direction=recommended_dir,
        classification=preferred.get("classification", "Devta"),
        deity=preferred.get("deity", "Kubera"),
        quality=preferred.get("quality", "Auspicious"),
    )

    dir_hi = direction_hi.get(recommended_dir, recommended_dir)
    return DoorAnalysis(
        recommended_direction=recommended_dir,
        recommended_direction_hi=dir_hi,
        ayadi_field=ayadi,
        classification=ayadi.classification,
        lagna_alignment=alignment,
        recommendation=(
            f"Main entrance in {recommended_dir} ({ayadi.deity} field — "
            f"{ayadi.quality}). {alignment} alignment with {lagna_lord} "
            f"(lagna lord). {dir_hi} disha."
        ),
    )
