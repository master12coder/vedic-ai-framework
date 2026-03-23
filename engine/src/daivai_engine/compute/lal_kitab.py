"""Lal Kitab analysis — planet assessment, Rin detection, and remedy matching.

Lal Kitab is a distinct astrological system by Pandit Roop Chand Joshi
(5 volumes, 1939-1952). It uses planet-in-house positions (ignoring signs)
with unique friendship rules, Pakka Ghar (permanent house) assignments,
and practical remedies.

Source: Lal Kitab (1939-1952).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from daivai_engine.constants import EXALTATION, PLANETS
from daivai_engine.models.chart import ChartData
from daivai_engine.models.lal_kitab import (
    LalKitabPlanetAssessment,
    LalKitabRemedy,
    LalKitabResult,
    LalKitabRin,
)


# ── Lal Kitab Constants ─────────────────────────────────────────────────────

# Pakka Ghar (permanent house) for each planet — fixed regardless of chart
PAKKA_GHAR: dict[str, int] = {
    "Sun": 1,
    "Moon": 4,
    "Mars": 3,
    "Mercury": 7,
    "Jupiter": 2,
    "Venus": 7,
    "Saturn": 8,
    "Rahu": 12,
    "Ketu": 6,
}

# Lal Kitab friendships (different from Parashari)
LK_FRIENDS: dict[str, list[str]] = {
    "Sun": ["Moon", "Mars", "Jupiter"],
    "Moon": ["Sun", "Mercury"],
    "Mars": ["Sun", "Moon", "Jupiter"],
    "Mercury": ["Venus", "Saturn", "Moon"],
    "Jupiter": ["Sun", "Moon", "Mars"],
    "Venus": ["Mercury", "Saturn"],
    "Saturn": ["Mercury", "Venus"],
    "Rahu": ["Mercury", "Venus", "Saturn"],
    "Ketu": ["Mars", "Jupiter"],
}

LK_ENEMIES: dict[str, list[str]] = {
    "Sun": ["Saturn", "Venus", "Rahu", "Ketu"],
    "Moon": ["Rahu", "Ketu"],
    "Mars": ["Mercury", "Ketu"],
    "Mercury": ["Moon"],
    "Jupiter": ["Mercury", "Venus", "Rahu"],
    "Venus": ["Sun", "Moon", "Rahu"],
    "Saturn": ["Sun", "Moon", "Mars"],
    "Rahu": ["Sun", "Moon", "Mars"],
    "Ketu": ["Mercury", "Venus"],
}

# Exalted house mapping (sign index → house number, 1-indexed)
# In Lal Kitab the exaltation sign index maps to a house
_EXALT_HOUSE: dict[str, int] = {p: idx + 1 for p, idx in EXALTATION.items()}

_REMEDIES_PATH = Path(__file__).resolve().parents[1] / "scriptures" / "lal_kitab" / "remedies.yaml"


def _load_remedies() -> dict:  # type: ignore[type-arg]
    """Load Lal Kitab remedies from YAML."""
    with _REMEDIES_PATH.open() as f:
        return yaml.safe_load(f)  # type: ignore[no-any-return]


def _planet_house(planet_name: str, chart: ChartData) -> int:
    """Return the house (1-12) of a planet in the chart."""
    return chart.planets[planet_name].house


def _planets_in_house(house: int, chart: ChartData) -> list[str]:
    """Return list of planet names occupying a given house."""
    return [p for p in PLANETS if chart.planets[p].house == house]


def _is_afflicted(planet: str, house: int, chart: ChartData) -> bool:
    """Check if a planet is afflicted — conjunct or aspected by enemies."""
    occupants = _planets_in_house(house, chart)
    enemies = LK_ENEMIES.get(planet, [])
    return any(occ in enemies for occ in occupants if occ != planet)


def _assess_planet(planet_name: str, chart: ChartData) -> LalKitabPlanetAssessment:
    """Assess a single planet's strength in the Lal Kitab system.

    Strength hierarchy:
    - In Pakka Ghar → very_strong
    - In exalted house → strong
    - Conjunct/aspected by friends → strong
    - Affected by Rahu/Ketu → dormant (soya hua)
    - In enemy house or debilitated → weak
    - Otherwise → moderate
    """
    house = _planet_house(planet_name, chart)
    pakka = PAKKA_GHAR[planet_name]
    is_in_pakka = house == pakka

    # Check Rahu/Ketu influence (conjunction in same house)
    occupants = _planets_in_house(house, chart)
    rahu_ketu_present = any(n in occupants for n in ("Rahu", "Ketu") if n != planet_name)

    # Friends and enemies in the chart who share the same house
    friends_list = LK_FRIENDS.get(planet_name, [])
    enemies_list = LK_ENEMIES.get(planet_name, [])
    friends_present = [p for p in occupants if p in friends_list and p != planet_name]
    enemies_present = [p for p in occupants if p in enemies_list and p != planet_name]

    exalt_house = _EXALT_HOUSE.get(planet_name, -1)

    # Determine strength
    if rahu_ketu_present and planet_name not in ("Rahu", "Ketu"):
        strength = "dormant"
    elif is_in_pakka:
        strength = "very_strong"
    elif house == exalt_house or friends_present:
        strength = "strong"
    elif enemies_present:
        strength = "weak"
    else:
        strength = "moderate"

    is_dormant = strength == "dormant"

    assessment = (
        f"{planet_name} in house {house} "
        f"({'Pakka Ghar' if is_in_pakka else 'not Pakka Ghar'}): "
        f"{strength}"
    )

    return LalKitabPlanetAssessment(
        planet=planet_name,
        house=house,
        pakka_ghar=pakka,
        is_in_pakka_ghar=is_in_pakka,
        strength=strength,
        is_dormant=is_dormant,
        friends_in_chart=friends_present,
        enemies_in_chart=enemies_present,
        assessment=assessment,
    )


def _detect_rins(chart: ChartData) -> list[LalKitabRin]:
    """Detect the three Lal Kitab debts (Rins).

    - Pitra Rin: Sun afflicted in 2nd, 5th, or 9th house
    - Matri Rin: Moon afflicted in 4th house
    - Stri Rin: Venus afflicted in 7th house
    """
    rins: list[LalKitabRin] = []
    sun_house = _planet_house("Sun", chart)
    if sun_house in (2, 5, 9) and _is_afflicted("Sun", sun_house, chart):
        severity = "severe" if sun_house == 9 else "moderate" if sun_house == 5 else "mild"
        rins.append(
            LalKitabRin(
                rin_type="pitra",
                rin_name_hi="पितृ ऋण",
                is_present=True,
                causing_planet="Sun",
                causing_house=sun_house,
                description=f"Sun afflicted in house {sun_house} indicates ancestral debt",
                severity=severity,
            )
        )

    moon_house = _planet_house("Moon", chart)
    if moon_house == 4 and _is_afflicted("Moon", moon_house, chart):
        rins.append(
            LalKitabRin(
                rin_type="matri",
                rin_name_hi="मातृ ऋण",
                is_present=True,
                causing_planet="Moon",
                causing_house=4,
                description="Moon afflicted in 4th house indicates mother's debt",
                severity="moderate",
            )
        )

    venus_house = _planet_house("Venus", chart)
    if venus_house == 7 and _is_afflicted("Venus", venus_house, chart):
        rins.append(
            LalKitabRin(
                rin_type="stri",
                rin_name_hi="स्त्री ऋण",
                is_present=True,
                causing_planet="Venus",
                causing_house=7,
                description="Venus afflicted in 7th house indicates wife's debt",
                severity="moderate",
            )
        )

    return rins


def _categorize_remedy(text: str) -> str:
    """Categorize a remedy text into daan/behavioral/ritual/object."""
    text_lower = text.lower()
    if any(w in text_lower for w in ("donate", "offer", "throw", "float", "distribute")):
        return "daan"
    if any(w in text_lower for w in ("avoid", "do not", "respect", "never", "marry")):
        return "behavioral"
    if any(w in text_lower for w in ("temple", "worship", "prayer", "tilak", "pooja")):
        return "ritual"
    return "object"


def _match_remedies(chart: ChartData, remedies_data: dict) -> list[LalKitabRemedy]:
    """Match applicable remedies based on planet-house positions.

    Reads the remedies YAML structure and finds entries whose planet+house
    match the natal chart placements.
    """
    matched: list[LalKitabRemedy] = []
    rules = remedies_data.get("rules", [])

    for rule in rules:
        planets_in_rule = rule.get("planets", [])
        houses_in_rule = rule.get("houses", [])
        text_en = rule.get("text_english", "")
        text_hi = rule.get("text_hindi")

        for planet_name in planets_in_rule:
            if planet_name not in chart.planets:
                continue
            natal_house = chart.planets[planet_name].house
            if natal_house in houses_in_rule:
                matched.append(
                    LalKitabRemedy(
                        planet=planet_name,
                        house=natal_house,
                        remedy_text=text_en,
                        remedy_text_hi=text_hi,
                        category=_categorize_remedy(text_en),
                    )
                )

    return matched


def compute_lal_kitab(chart: ChartData) -> LalKitabResult:
    """Compute full Lal Kitab analysis for a birth chart.

    Returns planet assessments, detected Rins (debts), applicable remedies,
    dormant planets, and identifies the strongest/weakest planet.

    Args:
        chart: A computed birth chart with planet positions.

    Returns:
        LalKitabResult with complete Lal Kitab analysis.
    """
    # Assess all planets
    assessments = [_assess_planet(p, chart) for p in PLANETS]

    # Detect debts
    rins = _detect_rins(chart)

    # Load and match remedies
    remedies_data = _load_remedies()
    remedies = _match_remedies(chart, remedies_data)

    # Identify dormant, strongest, weakest
    dormant = [a.planet for a in assessments if a.is_dormant]

    strength_order = {"very_strong": 4, "strong": 3, "moderate": 2, "weak": 1, "dormant": 0}
    sorted_by_strength = sorted(assessments, key=lambda a: strength_order.get(a.strength, 2))
    strongest = sorted_by_strength[-1].planet
    weakest = sorted_by_strength[0].planet

    # Build summary
    rin_names = [r.rin_name_hi for r in rins] if rins else ["कोई ऋण नहीं"]
    summary = (
        f"Strongest: {strongest}, Weakest: {weakest}. "
        f"Dormant: {', '.join(dormant) if dormant else 'None'}. "
        f"Debts: {', '.join(rin_names)}. "
        f"Remedies matched: {len(remedies)}."
    )

    return LalKitabResult(
        planet_assessments=assessments,
        rins=rins,
        applicable_remedies=remedies,
        dormant_planets=dormant,
        strongest_planet=strongest,
        weakest_planet=weakest,
        summary=summary,
    )
