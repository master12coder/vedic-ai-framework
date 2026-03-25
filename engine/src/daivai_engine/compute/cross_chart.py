"""Cross-chart (synastry) planetary interaction analysis.

Computes planet-on-planet overlays between two birth charts to identify
emotional influence (Moon contacts), relationship dynamics (axis contacts),
karmic bonds (Saturn/Rahu contacts), and general synastry interactions.

Source: Parashari synastry principles adapted for computational analysis.
"""

from __future__ import annotations

from daivai_engine.compute.chart import get_house_lord
from daivai_engine.constants.misc import FULL_CIRCLE_DEG, HALF_CIRCLE_DEG
from daivai_engine.constants.signs import SIGN_LORDS, SIGNS
from daivai_engine.models.chart import ChartData
from daivai_engine.models.cross_chart import CrossChartResult, PlanetOverlay


_ALL_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
_KARMIC_PLANETS = {"Saturn", "Rahu", "Ketu"}

# Aspect orbs (degrees)
_ORB_CONJUNCTION = 10.0
_ORB_OPPOSITION = 10.0
_ORB_TRINE = 8.0
_ORB_SQUARE = 7.0
_ORB_SEXTILE = 6.0

# Aspect definitions: (target_degrees, name, orb)
_ASPECTS: list[tuple[float, str, float]] = [
    (0.0, "conjunction", _ORB_CONJUNCTION),
    (180.0, "opposition", _ORB_OPPOSITION),
    (120.0, "trine", _ORB_TRINE),
    (240.0, "trine", _ORB_TRINE),
    (90.0, "square", _ORB_SQUARE),
    (270.0, "square", _ORB_SQUARE),
    (60.0, "sextile", _ORB_SEXTILE),
    (300.0, "sextile", _ORB_SEXTILE),
]


def compute_cross_chart_interactions(
    chart_a: ChartData,
    chart_b: ChartData,
    orb: float = _ORB_CONJUNCTION,
) -> CrossChartResult:
    """Find where Person A's planets overlay Person B's chart.

    Analyses all planet pairs across two charts and categorises them into:
    - overlays: all significant aspects between charts
    - moon_contacts: any planet of A on B's Moon (or vice versa)
    - axis_contacts: Lagnesh-on-Moon, 7th-lord-on-Lagna cross-references
    - karmic_links: Saturn or Rahu/Ketu contacts indicating deep karmic bonds

    Args:
        chart_a: First person's birth chart.
        chart_b: Second person's birth chart.
        orb: Default orb for conjunction detection (degrees).

    Returns:
        CrossChartResult with categorised overlays and a bond strength score.
    """
    overlays: list[PlanetOverlay] = []
    moon_contacts: list[PlanetOverlay] = []
    axis_contacts: list[PlanetOverlay] = []
    karmic_links: list[PlanetOverlay] = []

    # Compute all inter-chart aspects
    for pa_name in _ALL_PLANETS:
        pa = chart_a.planets[pa_name]
        for pb_name in _ALL_PLANETS:
            pb = chart_b.planets[pb_name]
            aspect = _find_aspect(pa.longitude, pb.longitude)
            if aspect is None:
                continue

            aspect_type, orb_deg = aspect
            effect = _classify_effect(aspect_type, pa_name, pb_name)
            sign = SIGNS[pa.sign_index]

            overlay = PlanetOverlay(
                person_a_name=chart_a.name,
                person_b_name=chart_b.name,
                planet_a=pa_name,
                planet_b=pb_name,
                sign=sign,
                orb_degrees=round(orb_deg, 2),
                interaction_type=aspect_type,
                effect=effect,
                description=_describe(
                    chart_a.name, pa_name, chart_b.name, pb_name, aspect_type, effect
                ),
            )
            overlays.append(overlay)

            # Categorise
            if pb_name == "Moon" or pa_name == "Moon":
                moon_contacts.append(overlay)
            if pa_name in _KARMIC_PLANETS or pb_name in _KARMIC_PLANETS:
                karmic_links.append(overlay)

    # Axis contacts: Lagnesh-on-Moon, 7L-on-Lagna
    axis_contacts = _find_axis_contacts(chart_a, chart_b, overlays)

    bond_strength = _compute_bond_strength(overlays, moon_contacts, axis_contacts, karmic_links)

    summary = _build_summary(chart_a.name, chart_b.name, overlays, moon_contacts, karmic_links)

    return CrossChartResult(
        person_a=chart_a.name,
        person_b=chart_b.name,
        overlays=overlays,
        moon_contacts=moon_contacts,
        axis_contacts=axis_contacts,
        karmic_links=karmic_links,
        bond_strength=round(bond_strength, 1),
        summary=summary,
    )


def _find_aspect(lon_a: float, lon_b: float) -> tuple[str, float] | None:
    """Check if two longitudes form a significant aspect."""
    diff = (lon_b - lon_a) % FULL_CIRCLE_DEG
    for target, name, max_orb in _ASPECTS:
        orb_deg = abs(diff - target)
        if orb_deg > HALF_CIRCLE_DEG:
            orb_deg = FULL_CIRCLE_DEG - orb_deg
        if orb_deg <= max_orb:
            return name, orb_deg
    return None


def _classify_effect(aspect_type: str, planet_a: str, planet_b: str) -> str:
    """Classify the qualitative effect of an aspect."""
    if aspect_type in ("trine", "sextile"):
        return "supportive"
    if aspect_type in ("square", "opposition"):
        if planet_a in _KARMIC_PLANETS or planet_b in _KARMIC_PLANETS:
            return "karmic"
        return "challenging"
    # Conjunction
    if planet_a in _KARMIC_PLANETS or planet_b in _KARMIC_PLANETS:
        return "karmic"
    return "neutral"


def _find_axis_contacts(
    chart_a: ChartData,
    chart_b: ChartData,
    overlays: list[PlanetOverlay],
) -> list[PlanetOverlay]:
    """Find Lagnesh-on-Moon and 7L-on-Lagna cross-references."""
    axis: list[PlanetOverlay] = []
    lagnesh_a = SIGN_LORDS[chart_a.lagna_sign_index]
    lagnesh_b = SIGN_LORDS[chart_b.lagna_sign_index]
    seventh_lord_a = get_house_lord(chart_a, 7)
    seventh_lord_b = get_house_lord(chart_b, 7)

    axis_pairs = {
        (lagnesh_a, "Moon"),  # A's identity on B's emotions
        ("Moon", lagnesh_b),  # B's identity on A's emotions
        (seventh_lord_a, lagnesh_b),  # A's 7L on B's Lagna
        (seventh_lord_b, lagnesh_a),  # B's 7L on A's Lagna
    }

    for ov in overlays:
        if (ov.planet_a, ov.planet_b) in axis_pairs:
            axis.append(ov)
    return axis


def _compute_bond_strength(
    overlays: list[PlanetOverlay],
    moon_contacts: list[PlanetOverlay],
    axis_contacts: list[PlanetOverlay],
    karmic_links: list[PlanetOverlay],
) -> float:
    """Compute a 0-100 bond strength score."""
    score = 0.0
    # Each overlay contributes based on type
    weights = {"conjunction": 4.0, "trine": 3.0, "sextile": 2.0, "opposition": 2.5, "square": 1.5}
    for ov in overlays:
        score += weights.get(ov.interaction_type, 1.0)
    # Moon contacts are emotionally significant
    score += len(moon_contacts) * 3.0
    # Axis contacts indicate deep relationship dynamics
    score += len(axis_contacts) * 5.0
    # Karmic links indicate lasting bond
    score += len(karmic_links) * 2.0
    return min(score, 100.0)


def _describe(
    name_a: str, planet_a: str, name_b: str, planet_b: str, aspect: str, effect: str
) -> str:
    """Build a human-readable description of an overlay."""
    return f"{name_a}'s {planet_a} {aspect} {name_b}'s {planet_b} — {effect} influence."


def _build_summary(
    name_a: str,
    name_b: str,
    overlays: list[PlanetOverlay],
    moon_contacts: list[PlanetOverlay],
    karmic_links: list[PlanetOverlay],
) -> str:
    """Build a one-paragraph summary of the cross-chart analysis."""
    parts = [f"{name_a} x {name_b}: {len(overlays)} cross-chart aspects found."]
    if moon_contacts:
        parts.append(f"{len(moon_contacts)} Moon contacts (emotional bond).")
    if karmic_links:
        parts.append(f"{len(karmic_links)} karmic links (Saturn/Rahu/Ketu).")
    return " ".join(parts)
