"""Ashtamangala Prashna utility functions — classify, aroodha, number prashna."""

from __future__ import annotations

from daivai_engine.compute.upagraha import compute_gulika_longitude
from daivai_engine.constants import KENDRAS, SIGN_LORDS, SIGNS, TRIKONAS
from daivai_engine.models.ashtamangala import AroodhaResult, PrashnaClassification
from daivai_engine.models.chart import ChartData


# Houses where planets are considered strong
_STRENGTH_HOUSES: frozenset[int] = frozenset(KENDRAS + TRIKONAS[1:])  # 1,4,5,7,9,10

# Query type → (primary house, natural karaka, deva category)
_QUERY_MAP: dict[str, tuple[int, str, str]] = {
    "general": (1, "Moon", "dharma"),
    "health": (1, "Sun", "moksha"),
    "wealth": (2, "Jupiter", "artha"),
    "siblings": (3, "Mars", "kama"),
    "property": (4, "Moon", "moksha"),
    "mother": (4, "Moon", "dharma"),
    "education": (5, "Jupiter", "dharma"),
    "children": (5, "Jupiter", "kama"),
    "enemies": (6, "Mars", "artha"),
    "disease": (6, "Mars", "moksha"),
    "marriage": (7, "Venus", "kama"),
    "partnership": (7, "Mercury", "artha"),
    "longevity": (8, "Saturn", "moksha"),
    "inheritance": (8, "Saturn", "artha"),
    "fortune": (9, "Jupiter", "dharma"),
    "father": (9, "Sun", "dharma"),
    "career": (10, "Sun", "artha"),
    "status": (10, "Sun", "artha"),
    "gains": (11, "Jupiter", "artha"),
    "income": (11, "Jupiter", "artha"),
    "loss": (12, "Saturn", "moksha"),
    "travel": (12, "Moon", "kama"),
    "spirituality": (12, "Jupiter", "moksha"),
}

_DEVA_NATURE: dict[str, str] = {
    "dharma": "sattvik",
    "artha": "rajasik",
    "kama": "rajasik",
    "moksha": "tamasik",
}

_DEVA_DESC: dict[str, str] = {
    "dharma": "Dharmic query — Jupiter and Sun are primary karakas.",
    "artha": "Artha (material) query — Mercury, Venus, Jupiter govern.",
    "kama": "Kama (desire/relationship) query — Moon, Venus, Mars govern.",
    "moksha": "Moksha (liberation/hidden) query — Saturn, Ketu, Jupiter govern.",
}


def classify_query(query_type: str) -> PrashnaClassification:
    """Map query type to its Deva Prashna classification.

    Args:
        query_type: Category of question (e.g., "marriage", "career").

    Returns:
        PrashnaClassification with primary house, karaka, and Deva category.
    """
    house, karaka, deva = _QUERY_MAP.get(query_type, (1, "Moon", "dharma"))
    return PrashnaClassification(
        query_type=query_type,
        primary_house=house,
        karaka=karaka,
        deva_category=deva,
        nature=_DEVA_NATURE[deva],
        description=_DEVA_DESC[deva],
    )


def compute_aroodha(prashna_chart: ChartData, query_house: int) -> AroodhaResult:
    """Compute the Aroodha Pada (significator) for the query house.

    Algorithm per Jaimini Upadesha Sutras / Prashna Marga Ch.2:
      1. Find sign of the query house (lagna_sign + house - 1).
      2. Find its lord and the lord's sign.
      3. Count N signs from house to lord; project N more from lord.
      4. Exception: if Aroodha = house sign or 7th from it → use 10th.

    Args:
        prashna_chart: Computed chart for the question moment.
        query_house: House number (1-12) pertaining to the query.

    Returns:
        AroodhaResult with Aroodha sign and lord placement details.
    """
    house_sign = (prashna_chart.lagna_sign_index + query_house - 1) % 12
    lord_name = SIGN_LORDS[house_sign]
    lord_sign = prashna_chart.planets[lord_name].sign_index

    dist = ((lord_sign - house_sign) % 12) + 1
    aroodha = (lord_sign + dist - 1) % 12

    seventh = (house_sign + 6) % 12
    if aroodha in (house_sign, seventh):
        aroodha = (house_sign + 9) % 12

    lord_planet = prashna_chart.planets.get(SIGN_LORDS[aroodha])
    lord_house = lord_planet.house if lord_planet else 1
    is_strong = lord_house in _STRENGTH_HOUSES

    reasoning = (
        f"House {query_house} is {SIGNS[house_sign]}; lord {lord_name} in "
        f"{SIGNS[lord_sign]}. Aroodha → {SIGNS[aroodha]}. "
        f"Aroodha lord {SIGN_LORDS[aroodha]} is "
        f"{'strong' if is_strong else 'weak'} in house {lord_house}."
    )
    return AroodhaResult(
        house=query_house,
        aroodha_sign_index=aroodha,
        aroodha_sign=SIGNS[aroodha],
        aroodha_lord=SIGN_LORDS[aroodha],
        lord_house=lord_house,
        is_strong=is_strong,
        reasoning=reasoning,
    )


def _get_gulika_longitude(chart: ChartData) -> float:
    """Get Gulika longitude; falls back to Saturn + 30° on error."""
    try:
        return compute_gulika_longitude(chart)
    except Exception:
        saturn = chart.planets.get("Saturn")
        return (saturn.longitude + 30.0) % 360.0 if saturn else 0.0


def number_prashna(number: int) -> dict:
    """Interpret a number (1-108) via the Kerala Number Prashna framework.

    The querist offers a number spontaneously; it maps to one of 108
    rashi-navamsha divisions. The rashi lord and navamsha lord together
    indicate the energy governing the query.

    Args:
        number: Integer from 1 to 108 given by the querist.

    Returns:
        Dict with rashi_index, navamsha_position, rashi_sign, and notes.
    """
    n = max(1, min(108, number))
    rashi_index = (n - 1) // 9
    navamsha_pos = (n - 1) % 9 + 1
    rashi_lord = SIGN_LORDS[rashi_index]
    navamsha_favorable = navamsha_pos in (1, 4, 5, 7, 9, 10)  # kendra/trikona
    return {
        "number": n,
        "rashi_index": rashi_index,
        "rashi_sign": SIGNS[rashi_index],
        "rashi_lord": rashi_lord,
        "navamsha_position": navamsha_pos,
        "navamsha_favorable": navamsha_favorable,
        "note": (
            f"Number {n} → {SIGNS[rashi_index]} rashi, navamsha {navamsha_pos}. "
            f"Rashi lord {rashi_lord}. "
            + (
                "Navamsha is in kendra/trikona — favorable signal."
                if navamsha_favorable
                else "Navamsha in dusthana or neutral position."
            )
        ),
    }
