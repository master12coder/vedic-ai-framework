"""Ashtakavarga point system — BPHS chapters 66-72.

Computes Bhinnashtakavarga (individual planet bindu tables) and
Sarvashtakavarga (aggregate) for all 7 planets (Sun through Saturn).
Each planet receives bindus from 8 sources (7 planets + Lagna).

The total of all Sarvashtakavarga values is always 337.

Also provides:
  - Prastara Ashtakavarga: 12x8 contributor matrix per planet (BPHS Ch.68)
  - Kaksha computation: 8 sub-divisions per sign with their lords (BPHS Ch.69)
"""

from __future__ import annotations

from daivai_engine.constants import SIGNS, SIGNS_EN
from daivai_engine.models.ashtakavarga import (
    AshtakavargaResult,
    KakshaResult,
    PrastaraResult,
)
from daivai_engine.models.chart import ChartData


# The 7 planets used in Ashtakavarga (Rahu/Ketu excluded per BPHS).
_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# The 8 sources that contribute bindus: 7 planets + Lagna.
_SOURCES = [*_PLANETS, "Lagna"]

# ---------------------------------------------------------------------------
# BPHS Bhinnashtakavarga bindu contribution tables.
# For each target planet, each source contributes a bindu when it is at
# certain house distances from the target planet's position.
# Houses are 1-based (1 = same sign as source).
# ---------------------------------------------------------------------------

_BINDU_TABLES: dict[str, dict[str, list[int]]] = {
    "Sun": {
        "Sun": [1, 2, 4, 7, 8, 9, 10, 11],
        "Moon": [3, 6, 10, 11],
        "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [5, 6, 9, 11],
        "Venus": [6, 7, 12],
        "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
        "Lagna": [3, 4, 6, 10, 11, 12],
    },
    "Moon": {
        "Sun": [3, 6, 7, 8, 10, 11],
        "Moon": [1, 3, 6, 7, 10, 11],
        "Mars": [2, 3, 5, 6, 9, 10, 11],
        "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
        "Jupiter": [1, 4, 7, 8, 10, 11, 12],
        "Venus": [3, 4, 5, 7, 9, 10, 11],
        "Saturn": [3, 5, 6, 11],
        "Lagna": [3, 6, 10, 11],
    },
    "Mars": {
        "Sun": [3, 5, 6, 10, 11],
        "Moon": [3, 6, 11],
        "Mars": [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [3, 5, 6, 11],
        "Jupiter": [6, 10, 11, 12],
        "Venus": [6, 8, 11, 12],
        "Saturn": [1, 4, 7, 8, 9, 10, 11],
        "Lagna": [1, 3, 6, 10, 11],
    },
    "Mercury": {
        "Sun": [5, 6, 9, 11, 12],
        "Moon": [2, 4, 6, 8, 10, 11],
        "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [6, 8, 11, 12],
        "Venus": [1, 2, 3, 4, 5, 8, 9, 11],
        "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
        "Lagna": [1, 2, 4, 6, 8, 10, 11],
    },
    "Jupiter": {
        "Sun": [1, 2, 3, 4, 7, 8, 9, 10, 11],
        "Moon": [2, 5, 7, 9, 11],
        "Mars": [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
        "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
        "Venus": [2, 5, 6, 9, 10, 11],
        "Saturn": [3, 5, 6, 12],
        "Lagna": [1, 2, 4, 5, 6, 7, 9, 10, 11],
    },
    "Venus": {
        "Sun": [8, 11, 12],
        "Moon": [1, 2, 3, 4, 5, 8, 9, 11, 12],
        "Mars": [3, 5, 6, 9, 11, 12],
        "Mercury": [3, 5, 6, 9, 11],
        "Jupiter": [5, 8, 9, 10, 11],
        "Venus": [1, 2, 3, 4, 5, 8, 9, 10, 11],
        "Saturn": [3, 4, 5, 8, 9, 10, 11],
        "Lagna": [1, 2, 3, 4, 5, 8, 9, 11],
    },
    "Saturn": {
        "Sun": [1, 2, 4, 7, 8, 10, 11],
        "Moon": [3, 6, 11],
        "Mars": [3, 5, 6, 10, 11, 12],
        "Mercury": [6, 8, 9, 10, 11, 12],
        "Jupiter": [5, 6, 11, 12],
        "Venus": [6, 11, 12],
        "Saturn": [3, 5, 6, 11],
        "Lagna": [1, 3, 4, 6, 10, 11],
    },
}


def _sign_index_of(chart: ChartData, source: str) -> int:
    """Return the sign index (0-11) for a source planet or Lagna."""
    if source == "Lagna":
        return chart.lagna_sign_index
    return chart.planets[source].sign_index


def _house_distance(from_sign: int, to_sign: int) -> int:
    """Return the 1-based house number of *to_sign* counted from *from_sign*.

    House 1 means same sign; house 2 means the next sign, etc.
    """
    return ((to_sign - from_sign) % 12) + 1


def _compute_bhinna(chart: ChartData, planet: str) -> list[int]:
    """Compute Bhinnashtakavarga for one planet across 12 signs.

    For each of the 12 signs, count how many of the 8 sources contribute
    a bindu (i.e. the sign is at a favourable house distance from the source).

    Returns:
        List of 12 integers, one per sign (index 0 = Aries).
    """
    table = _BINDU_TABLES[planet]
    _target_sign = _sign_index_of(chart, planet)
    result: list[int] = []

    for sign in range(12):
        bindus = 0
        for source in _SOURCES:
            source_sign = _sign_index_of(chart, source)
            house = _house_distance(source_sign, sign)
            if house in table[source]:
                bindus += 1
        result.append(bindus)

    return result


def compute_ashtakavarga(chart: ChartData) -> AshtakavargaResult:
    """Compute the full Ashtakavarga for a birth chart.

    Calculates Bhinnashtakavarga for each of the 7 planets (Sun through
    Saturn), then aggregates them into Sarvashtakavarga. The total of
    Sarvashtakavarga always equals 337.

    Args:
        chart: A computed birth chart with planetary positions.

    Returns:
        AshtakavargaResult with bhinna tables, sarva table, and total.
    """
    bhinna: dict[str, list[int]] = {}
    for planet in _PLANETS:
        bhinna[planet] = _compute_bhinna(chart, planet)

    # Sarvashtakavarga: sum of all 7 Bhinna tables per sign.
    sarva: list[int] = [0] * 12
    for sign in range(12):
        for planet in _PLANETS:
            sarva[sign] += bhinna[planet][sign]

    total = sum(sarva)

    return AshtakavargaResult(bhinna=bhinna, sarva=sarva, total=total)


# ---------------------------------------------------------------------------
# Prastara Ashtakavarga — contributor matrix (BPHS Ch.68)
# ---------------------------------------------------------------------------


def _compute_bhinna_prastara(chart: ChartData, planet: str) -> list[list[str]]:
    """Compute contributor lists for one planet's Prastara Ashtakavarga.

    For each of the 12 signs, returns the list of source names (from the 8
    contributors: 7 planets + Lagna) that gave a bindu point.

    Returns:
        List of 12 lists of contributor name strings.
    """
    table = _BINDU_TABLES[planet]
    contributors: list[list[str]] = []

    for sign in range(12):
        sign_contributors: list[str] = []
        for source in _SOURCES:
            source_sign = _sign_index_of(chart, source)
            house = _house_distance(source_sign, sign)
            if house in table[source]:
                sign_contributors.append(source)
        contributors.append(sign_contributors)

    return contributors


def compute_prastara(chart: ChartData) -> dict[str, PrastaraResult]:
    """Compute Prastara (expanded) Ashtakavarga for all 7 planets.

    The Prastara shows WHICH of the 8 contributors (7 planets + Lagna)
    gave each bindu point in the Bhinnashtakavarga, for every sign.
    This is the detailed form from which the standard BAV counts can be
    derived by taking len(contributors[sign_index]) for each sign.

    Args:
        chart: A fully computed birth chart with planetary positions.

    Returns:
        Dict mapping planet name → PrastaraResult, for Sun through Saturn.
    """
    result: dict[str, PrastaraResult] = {}
    for planet in _PLANETS:
        contributors = _compute_bhinna_prastara(chart, planet)
        result[planet] = PrastaraResult(planet=planet, contributors=contributors)
    return result


# ---------------------------------------------------------------------------
# Kaksha — 8 sub-divisions per sign (BPHS Ch.69)
# ---------------------------------------------------------------------------

# Kaksha lords in order within any sign (3°45' = 3.75° each)
_KAKSHA_LORDS = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Lagna"]
_KAKSHA_WIDTH = 30.0 / 8.0  # 3.75°


def compute_kaksha(longitude: float) -> KakshaResult:
    """Return the Kaksha details for a given sidereal longitude.

    Each sign (30°) is divided into 8 Kakshas of 3°45'. The lords cycle
    as: Saturn → Jupiter → Mars → Sun → Venus → Mercury → Moon → Lagna.
    When a transit planet occupies a Kaksha whose lord contributed a bindu
    in that sign's BAV, the transit gives auspicious results.

    Args:
        longitude: Sidereal longitude of the planet/point (0 ≤ lon < 360).

    Returns:
        KakshaResult with sign, Kaksha number (1-8), lord, and degree range.
    """
    longitude = longitude % 360.0
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0

    kaksha_idx = int(degree_in_sign / _KAKSHA_WIDTH)
    kaksha_idx = min(kaksha_idx, 7)  # guard against floating-point edge at 30°

    start = kaksha_idx * _KAKSHA_WIDTH
    end = (kaksha_idx + 1) * _KAKSHA_WIDTH

    return KakshaResult(
        longitude=longitude,
        sign_index=sign_index,
        sign=SIGNS[sign_index],
        sign_en=SIGNS_EN[sign_index],
        degree_in_sign=degree_in_sign,
        kaksha_number=kaksha_idx + 1,
        kaksha_lord=_KAKSHA_LORDS[kaksha_idx],
        kaksha_start=start,
        kaksha_end=end,
    )


def get_transit_strength(sarva: list[int], sign_index: int) -> str:
    """Evaluate transit strength of a sign based on Sarvashtakavarga bindus.

    Args:
        sarva: Sarvashtakavarga list (12 integers).
        sign_index: Sign index (0-11, where 0 = Aries).

    Returns:
        "strong" if 4+ bindus per planet average (28+),
        "moderate" if 3 per planet average (21-27),
        "weak" if below 3 per planet average (0-20).
    """
    value = sarva[sign_index]
    if value >= 28:
        return "strong"
    if value >= 21:
        return "moderate"
    return "weak"
