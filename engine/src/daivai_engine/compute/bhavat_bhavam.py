"""Bhavat Bhavam — house from house derived analysis.

The Bhavat Bhavam principle: the Nth house counted from the Nth house
serves as a secondary indicator for Nth house matters. For example,
for marriage (7th house), the 7th from 7th = 1st house is the derived
indicator.

Additionally, the position of the natural karaka (significator) for each
house provides a third perspective.

Source: BPHS Ch.5, Phaladeepika Ch.1.
"""

from __future__ import annotations

from daivai_engine.constants import (
    NATURAL_ENEMIES,
    NATURAL_FRIENDS,
    SIGN_LORDS,
    SIGNS_EN,
)
from daivai_engine.models.bhavat_bhavam import BhavatBhavamResult, HousePerspective
from daivai_engine.models.chart import ChartData


# Human-readable labels for each house (BPHS Ch.5)
_HOUSE_LABELS: dict[int, str] = {
    1: "Self/Personality",
    2: "Wealth/Family",
    3: "Courage/Siblings",
    4: "Home/Mother",
    5: "Children/Education",
    6: "Enemies/Health",
    7: "Marriage/Partnerships",
    8: "Longevity/Transformation",
    9: "Fortune/Father",
    10: "Career/Status",
    11: "Gains/Aspirations",
    12: "Losses/Spirituality",
}

# Natural karakas per house (BPHS Ch.20)
# When multiple karakas exist, the first is primary.
_HOUSE_KARAKAS: dict[int, list[str]] = {
    1: ["Sun"],
    2: ["Jupiter"],
    3: ["Mars"],
    4: ["Moon", "Mercury"],
    5: ["Jupiter"],
    6: ["Saturn", "Mars"],
    7: ["Venus"],
    8: ["Saturn"],
    9: ["Jupiter", "Sun"],
    10: ["Mercury", "Jupiter", "Sun"],
    11: ["Jupiter"],
    12: ["Saturn", "Ketu"],
}


def _derived_house(query_house: int) -> int:
    """Compute the Bhavat Bhavam (Nth from Nth) derived house.

    Formula: ((query_house - 1) * 2) % 12 + 1

    Args:
        query_house: The query house number (1-12).

    Returns:
        Derived house number (1-12).
    """
    return ((query_house - 1) * 2) % 12 + 1


def _house_sign_index(lagna_sign_index: int, house_num: int) -> int:
    """Compute the sign index for a house (whole-sign).

    Args:
        lagna_sign_index: Lagna sign index (0-11).
        house_num: House number (1-12).

    Returns:
        Sign index (0-11).
    """
    return (lagna_sign_index + house_num - 1) % 12


def _planets_in_house(chart: ChartData, house_num: int) -> list[str]:
    """Return sorted planet names in a given house.

    Args:
        chart: Computed birth chart.
        house_num: House number (1-12).

    Returns:
        Sorted list of planet names.
    """
    return sorted(name for name, p in chart.planets.items() if p.house == house_num)


def _build_house_perspective(chart: ChartData, house_num: int) -> HousePerspective:
    """Build a HousePerspective for a given house.

    Args:
        chart: Computed birth chart.
        house_num: House number (1-12).

    Returns:
        HousePerspective with sign, lord, and planet details.
    """
    sign_idx = _house_sign_index(chart.lagna_sign_index, house_num)
    lord = SIGN_LORDS[sign_idx]
    lord_data = chart.planets.get(lord)
    lord_house = lord_data.house if lord_data else house_num
    lord_dignity = lord_data.dignity if lord_data else "neutral"
    planets = _planets_in_house(chart, house_num)

    return HousePerspective(
        house_number=house_num,
        sign_index=sign_idx,
        sign=SIGNS_EN[sign_idx],
        lord=lord,
        lord_house=lord_house,
        lord_dignity=lord_dignity,
        planets_in_house=planets,
    )


def _are_friends(planet_a: str, planet_b: str) -> bool:
    """Check if two planets are natural friends.

    Args:
        planet_a: First planet name.
        planet_b: Second planet name.

    Returns:
        True if they are natural friends.
    """
    if planet_a == planet_b:
        return True
    friends_a = NATURAL_FRIENDS.get(planet_a, [])
    friends_b = NATURAL_FRIENDS.get(planet_b, [])
    return planet_b in friends_a or planet_a in friends_b


def _are_enemies(planet_a: str, planet_b: str) -> bool:
    """Check if two planets are natural enemies.

    Args:
        planet_a: First planet name.
        planet_b: Second planet name.

    Returns:
        True if they are natural enemies.
    """
    if planet_a == planet_b:
        return False
    enemies_a = NATURAL_ENEMIES.get(planet_a, [])
    enemies_b = NATURAL_ENEMIES.get(planet_b, [])
    return planet_b in enemies_a or planet_a in enemies_b


def _build_summary(
    query_house: int,
    label: str,
    primary: HousePerspective,
    derived: HousePerspective,
    karaka: str,
    reinforcing: bool,
    conflicting: bool,
) -> str:
    """Build a human-readable summary for the Bhavat Bhavam analysis.

    Args:
        query_house: Query house number.
        label: House label.
        primary: Primary house perspective.
        derived: Derived house perspective.
        karaka: Natural karaka name.
        reinforcing: Lords are friends.
        conflicting: Lords are enemies.

    Returns:
        Summary string.
    """
    derived_num = derived.house_number
    relation = (
        "reinforce" if reinforcing else ("conflict with" if conflicting else "are neutral to")
    )

    return (
        f"House {query_house} ({label}): primary lord {primary.lord} "
        f"and derived {derived_num}th-house lord {derived.lord} "
        f"{relation} each other. "
        f"Natural karaka: {karaka}."
    )


def compute_bhavat_bhavam(chart: ChartData, query_house: int) -> BhavatBhavamResult:
    """Compute Bhavat Bhavam analysis for a single query house.

    Analyzes the primary house, its derived (Nth from Nth) house, and the
    natural karaka's perspective. Checks whether the primary and derived
    lords reinforce or conflict with each other.

    Source: BPHS Ch.5, Phaladeepika Ch.1.

    Args:
        chart: A fully computed birth chart with all planetary positions.
        query_house: House number to analyze (1-12).

    Returns:
        BhavatBhavamResult with primary, derived, and karaka perspectives.

    Raises:
        ValueError: If query_house is not in 1-12.
    """
    if not 1 <= query_house <= 12:
        msg = f"query_house must be 1-12, got {query_house}"
        raise ValueError(msg)

    label = _HOUSE_LABELS[query_house]
    derived_house_num = _derived_house(query_house)

    primary = _build_house_perspective(chart, query_house)
    derived = _build_house_perspective(chart, derived_house_num)

    # Natural karaka
    karaka_list = _HOUSE_KARAKAS[query_house]
    karaka = karaka_list[0]
    karaka_data = chart.planets.get(karaka)
    karaka_house = karaka_data.house if karaka_data else 1
    karaka_dignity = karaka_data.dignity if karaka_data else "neutral"

    # Karaka perspective: house where karaka sits, then count query_house from there
    karaka_perspective: HousePerspective | None = None
    if karaka_data:
        # The derived-from-karaka house: query_house-th from karaka's house
        karaka_derived = ((karaka_house - 1 + query_house - 1) % 12) + 1
        karaka_perspective = _build_house_perspective(chart, karaka_derived)

    # Check friendship/enmity between primary and derived lords
    reinforcing = _are_friends(primary.lord, derived.lord)
    conflicting = _are_enemies(primary.lord, derived.lord)

    summary = _build_summary(
        query_house,
        label,
        primary,
        derived,
        karaka,
        reinforcing,
        conflicting,
    )

    return BhavatBhavamResult(
        query_house=query_house,
        query_label=label,
        primary=primary,
        derived=derived,
        karaka_perspective=karaka_perspective,
        natural_karaka=karaka,
        karaka_house=karaka_house,
        karaka_dignity=karaka_dignity,
        reinforcing=reinforcing,
        conflicting=conflicting,
        summary=summary,
    )


def compute_all_bhavat_bhavam(chart: ChartData) -> list[BhavatBhavamResult]:
    """Compute Bhavat Bhavam for all 12 houses.

    Source: BPHS Ch.5, Phaladeepika Ch.1.

    Args:
        chart: A fully computed birth chart with all planetary positions.

    Returns:
        List of 12 BhavatBhavamResult, one per house (1-12).
    """
    return [compute_bhavat_bhavam(chart, h) for h in range(1, 13)]
