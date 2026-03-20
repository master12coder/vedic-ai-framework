"""Pushkara Navamsha and Pushkara Bhaga computation — Phaladeepika.

Pushkara positions strengthen a planet's auspicious results:
  - Pushkara Navamsha: specific 3°20' ranges within each sign
  - Pushkara Bhaga: a single exact degree within each sign (peak auspiciousness)

A planet in Pushkara Navamsha gives enhanced benefic results.
A planet at Pushkara Bhaga (within 1°) is at peak strength for good results.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from daivai_engine.constants import PLANETS, SIGN_ELEMENTS, SIGNS, SIGNS_EN
from daivai_engine.models.chart import ChartData
from daivai_engine.models.pushkara import PushkaraResult


_DATA_FILE = Path(__file__).parent.parent / "knowledge" / "pushkara_data.yaml"
_PUSHKARA_BHAGA_ORB = 1.0  # degrees — within 1° of Pushkara Bhaga degree


def _load_data() -> dict:  # type: ignore[type-arg]
    """Load Pushkara data from YAML (cached at module level)."""
    with _DATA_FILE.open() as fh:
        data: dict = yaml.safe_load(fh)  # type: ignore[assignment]
        return data


_DATA = _load_data()
_BHAGA_DEGREES: list[int] = _DATA["pushkara_bhaga"]["degrees"]
_RANGES_BY_ELEMENT: dict[str, list[list[float]]] = _DATA["pushkara_navamsha"]["ranges_by_element"]


def _is_in_pushkara_navamsha(sign_index: int, degree_in_sign: float) -> bool:
    """Return True if *degree_in_sign* falls in a Pushkara Navamsha range."""
    element = SIGN_ELEMENTS[sign_index]
    return any(start <= degree_in_sign < end for start, end in _RANGES_BY_ELEMENT[element])


def _pushkara_type(in_navamsha: bool, in_bhaga: bool) -> str:
    """Classify Pushkara type from two boolean flags."""
    if in_navamsha and in_bhaga:
        return "both"
    if in_bhaga:
        return "bhaga"
    if in_navamsha:
        return "navamsha"
    return "none"


def _strength_modifier(pushkara_type: str) -> str:
    """Return a human-readable strength description."""
    match pushkara_type:
        case "both":
            return "Peak auspiciousness — Pushkara Bhaga within Pushkara Navamsha"
        case "bhaga":
            return "Highly auspicious — at Pushkara Bhaga degree"
        case "navamsha":
            return "Auspicious — in Pushkara Navamsha"
        case _:
            return "No Pushkara influence"


def check_pushkara(chart: ChartData) -> list[PushkaraResult]:
    """Check each planet for Pushkara Navamsha and Pushkara Bhaga positions.

    A planet in Pushkara Navamsha or at Pushkara Bhaga is strengthened and
    gives enhanced auspicious results per Phaladeepika and Jyotish Rahasya.

    Args:
        chart: A fully computed birth chart with planetary positions.

    Returns:
        List of PushkaraResult — one per planet (9 total, Sun through Ketu).
    """
    results: list[PushkaraResult] = []

    for planet in PLANETS:
        p = chart.planets[planet]
        in_navamsha = _is_in_pushkara_navamsha(p.sign_index, p.degree_in_sign)
        bhaga_deg = _BHAGA_DEGREES[p.sign_index]
        distance = abs(p.degree_in_sign - bhaga_deg)
        in_bhaga = distance <= _PUSHKARA_BHAGA_ORB
        ptype = _pushkara_type(in_navamsha, in_bhaga)

        results.append(
            PushkaraResult(
                planet=planet,
                sign_index=p.sign_index,
                sign=SIGNS[p.sign_index],
                sign_en=SIGNS_EN[p.sign_index],
                degree_in_sign=p.degree_in_sign,
                is_pushkara_navamsha=in_navamsha,
                is_pushkara_bhaga=in_bhaga,
                pushkara_bhaga_degree=bhaga_deg,
                pushkara_bhaga_distance=distance,
                pushkara_type=ptype,
                strength_modifier=_strength_modifier(ptype),
            )
        )

    return results


def get_pushkara_planets(chart: ChartData) -> list[PushkaraResult]:
    """Return only planets in a Pushkara position (navamsha or bhaga).

    Args:
        chart: A fully computed birth chart.

    Returns:
        Filtered list where pushkara_type != "none".
    """
    return [r for r in check_pushkara(chart) if r.pushkara_type != "none"]
