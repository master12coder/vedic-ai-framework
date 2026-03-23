"""Badhaka Sthana computation — house and lord of obstruction.

The Badhaka house is the primary source of obstruction in a chart. Its lord
(Badhakesh) and that lord's condition determine the nature and severity of
the obstructions the native faces.

Rules:
- Movable (Chara) lagna → 11th house is Badhaka
- Fixed (Sthira) lagna → 9th house is Badhaka
- Dual (Dwiswabhava) lagna → 7th house is Badhaka

Source: BPHS Ch.44-45, Jaimini Sutras.
"""

from __future__ import annotations

from daivai_engine.constants import (
    DUSTHANAS,
    SIGN_LORDS,
    SIGNS_EN,
    SPECIAL_ASPECTS,
)
from daivai_engine.models.badhaka import BadhakaResult
from daivai_engine.models.chart import ChartData


# Modality mapping: sign_index % 3 → modality name
# Aries(0)=movable, Taurus(1)=fixed, Gemini(2)=dual, Cancer(3)=movable, etc.
_MODALITY_MAP: dict[int, str] = {0: "movable", 1: "fixed", 2: "dual"}

# Badhaka house for each modality
_BADHAKA_HOUSE: dict[str, int] = {"movable": 11, "fixed": 9, "dual": 7}

# House-to-domain mapping for obstruction analysis
_HOUSE_DOMAINS: dict[int, str] = {
    1: "self/health",
    2: "finances/family",
    3: "communication/siblings",
    4: "home/mother",
    5: "children/education",
    6: "enemies/litigation",
    7: "marriage/partnerships",
    8: "longevity/transformation",
    9: "fortune/father",
    10: "career/status",
    11: "gains/aspirations",
    12: "losses/spirituality",
}


def _get_modality(sign_index: int) -> str:
    """Return the modality of a sign.

    Args:
        sign_index: Sign index 0-11.

    Returns:
        "movable", "fixed", or "dual".
    """
    return _MODALITY_MAP[sign_index % 3]


def _house_sign_index(lagna_sign_index: int, house_num: int) -> int:
    """Compute the sign index for a given house number (whole-sign).

    Args:
        lagna_sign_index: Lagna sign index (0-11).
        house_num: House number (1-12).

    Returns:
        Sign index (0-11) for that house.
    """
    return (lagna_sign_index + house_num - 1) % 12


def _planets_in_house(chart: ChartData, house_num: int) -> list[str]:
    """Return planet names occupying a given house.

    Args:
        chart: Computed birth chart.
        house_num: House number (1-12).

    Returns:
        Sorted list of planet names in that house.
    """
    return sorted(name for name, p in chart.planets.items() if p.house == house_num)


def _planet_aspects_house(planet_name: str, planet_house: int, target_house: int) -> bool:
    """Check if a planet aspects a target house via standard + special aspects.

    All planets aspect the 7th house from their position. Mars, Jupiter,
    Saturn, Rahu, and Ketu have additional special aspects.

    Uses Vedic inclusive counting: "Nth from house X" counts X as 1.
    Formula: vedic_nth = ((target - planet) % 12) + 1.
    A planet cannot aspect its own house (vedic_nth = 1).

    Args:
        planet_name: Name of the aspecting planet.
        planet_house: House the planet occupies (1-12).
        target_house: House being aspected (1-12).

    Returns:
        True if the planet aspects the target house.
    """
    if planet_house == target_house:
        return False

    # Vedic inclusive distance: e.g., house 1 to house 7 = 7th from
    offset = (target_house - planet_house) % 12  # 0 excluded (same house check)
    vedic_nth = offset + 1  # inclusive: offset 6 → 7th, offset 3 → 4th

    # Standard 7th aspect for all planets
    if vedic_nth == 7:
        return True

    # Special aspects: SPECIAL_ASPECTS uses Vedic Nth-from values
    special = SPECIAL_ASPECTS.get(planet_name, [])
    return vedic_nth in special


def _determine_severity(
    badhakesh_house: int,
    rahu_conjunct: bool,
    ketu_conjunct: bool,
    rahu_in_badhaka: bool,
    ketu_in_badhaka: bool,
    badhakesh_aspects_lagna: bool,
) -> str:
    """Determine obstruction severity.

    Severe: badhakesh in dusthana AND nodes involved.
    Moderate: badhakesh afflicted (dusthana or node association) but not both.
    Mild: no major affliction.

    Args:
        badhakesh_house: House of the badhakesh.
        rahu_conjunct: Rahu conjunct badhakesh.
        ketu_conjunct: Ketu conjunct badhakesh.
        rahu_in_badhaka: Rahu in the badhaka house.
        ketu_in_badhaka: Ketu in the badhaka house.
        badhakesh_aspects_lagna: Badhakesh aspects the 1st house.

    Returns:
        "mild", "moderate", or "severe".
    """
    in_dusthana = badhakesh_house in DUSTHANAS
    nodes_involved = rahu_conjunct or ketu_conjunct or rahu_in_badhaka or ketu_in_badhaka

    if in_dusthana and nodes_involved:
        return "severe"
    if in_dusthana or nodes_involved or badhakesh_aspects_lagna:
        return "moderate"
    return "mild"


def _determine_domains(
    badhaka_house: int,
    badhakesh_house: int,
) -> list[str]:
    """Determine life domains affected by the obstruction.

    Considers both the badhaka house and the house where badhakesh sits.

    Args:
        badhaka_house: The badhaka house number.
        badhakesh_house: House where the badhakesh is placed.

    Returns:
        List of domain strings.
    """
    domains: list[str] = []
    for h in sorted({badhaka_house, badhakesh_house}):
        domain = _HOUSE_DOMAINS.get(h, "")
        if domain:
            domains.append(domain)
    return domains


def _build_summary(
    modality: str,
    badhaka_house: int,
    badhakesh: str,
    badhakesh_house: int,
    severity: str,
    domains: list[str],
) -> str:
    """Build a human-readable summary of the Badhaka analysis.

    Args:
        modality: Lagna modality.
        badhaka_house: Badhaka house number.
        badhakesh: Badhakesh planet name.
        badhakesh_house: House of badhakesh.
        severity: Severity level.
        domains: Affected domains.

    Returns:
        Summary string.
    """
    domain_str = ", ".join(domains) if domains else "general"
    return (
        f"{modality.capitalize()} lagna: {badhaka_house}th house is Badhaka. "
        f"Badhakesh {badhakesh} in house {badhakesh_house}. "
        f"Obstruction severity: {severity}. "
        f"Domains affected: {domain_str}."
    )


def compute_badhaka(chart: ChartData) -> BadhakaResult:
    """Compute the Badhaka Sthana and Badhakesh for a birth chart.

    Determines the house of obstruction based on lagna modality, identifies
    the Badhakesh and its condition, checks node associations, and assesses
    the severity and domains of obstruction.

    Source: BPHS Ch.44-45, Jaimini Sutras.

    Args:
        chart: A fully computed birth chart with all planetary positions.

    Returns:
        BadhakaResult with complete obstruction analysis.
    """
    lagna_idx = chart.lagna_sign_index
    modality = _get_modality(lagna_idx)
    badhaka_house = _BADHAKA_HOUSE[modality]

    # Find the sign of the badhaka house
    badhaka_sign_idx = _house_sign_index(lagna_idx, badhaka_house)
    badhaka_sign = SIGNS_EN[badhaka_sign_idx]

    # Badhakesh = lord of the badhaka sign
    badhakesh = SIGN_LORDS[badhaka_sign_idx]

    # Badhakesh natal details
    badhakesh_data = chart.planets[badhakesh]
    badhakesh_house = badhakesh_data.house
    badhakesh_sign_idx = badhakesh_data.sign_index
    badhakesh_dignity = badhakesh_data.dignity
    badhakesh_retro = badhakesh_data.is_retrograde

    # Node associations
    rahu_data = chart.planets["Rahu"]
    ketu_data = chart.planets["Ketu"]

    rahu_conjunct = rahu_data.house == badhakesh_house
    ketu_conjunct = ketu_data.house == badhakesh_house
    rahu_in_badhaka = rahu_data.house == badhaka_house
    ketu_in_badhaka = ketu_data.house == badhaka_house

    # Planets in badhaka house
    planets_there = _planets_in_house(chart, badhaka_house)

    # Badhakesh aspecting lagna (house 1)
    aspects_lagna = _planet_aspects_house(badhakesh, badhakesh_house, 1)

    severity = _determine_severity(
        badhakesh_house,
        rahu_conjunct,
        ketu_conjunct,
        rahu_in_badhaka,
        ketu_in_badhaka,
        aspects_lagna,
    )
    domains = _determine_domains(badhaka_house, badhakesh_house)

    summary = _build_summary(
        modality,
        badhaka_house,
        badhakesh,
        badhakesh_house,
        severity,
        domains,
    )

    return BadhakaResult(
        lagna_sign_index=lagna_idx,
        lagna_modality=modality,
        badhaka_house=badhaka_house,
        badhaka_sign_index=badhaka_sign_idx,
        badhaka_sign=badhaka_sign,
        badhakesh=badhakesh,
        badhakesh_house=badhakesh_house,
        badhakesh_sign_index=badhakesh_sign_idx,
        badhakesh_dignity=badhakesh_dignity,
        badhakesh_retrograde=badhakesh_retro,
        rahu_conjunct_badhakesh=rahu_conjunct,
        ketu_conjunct_badhakesh=ketu_conjunct,
        rahu_in_badhaka_house=rahu_in_badhaka,
        ketu_in_badhaka_house=ketu_in_badhaka,
        planets_in_badhaka_house=planets_there,
        badhakesh_aspects_lagna=aspects_lagna,
        obstruction_severity=severity,
        obstruction_domains=domains,
        summary=summary,
    )
