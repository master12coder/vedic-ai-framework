"""Divisional chart computations — all 16 Shodashvarga charts."""

from __future__ import annotations

from typing import Any

from daivai_engine.compute.chart import ChartData
from daivai_engine.constants import PLANETS, SIGNS
from daivai_engine.models.divisional import DivisionalPosition


def compute_navamsha_sign(longitude: float) -> int:
    """Compute D9 (Navamsha) sign index from sidereal longitude.

    Each sign (30°) is divided into 9 parts of 3.3333° each.
    - Fire signs (Aries/0, Leo/4, Sagittarius/8) start from Aries
    - Earth signs (Taurus/1, Virgo/5, Capricorn/9) start from Capricorn
    - Air signs (Gemini/2, Libra/6, Aquarius/10) start from Libra
    - Water signs (Cancer/3, Scorpio/7, Pisces/11) start from Cancer
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    navamsha_part = int(degree_in_sign / (30.0 / 9.0))
    if navamsha_part > 8:
        navamsha_part = 8

    # Starting sign based on element
    fire_signs = {0, 4, 8}
    earth_signs = {1, 5, 9}
    air_signs = {2, 6, 10}
    _water_signs = {3, 7, 11}

    if sign_index in fire_signs:
        start = 0  # Aries
    elif sign_index in earth_signs:
        start = 9  # Capricorn
    elif sign_index in air_signs:
        start = 6  # Libra
    else:  # water
        start = 3  # Cancer

    return (start + navamsha_part) % 12


def compute_dasamsha_sign(longitude: float) -> int:
    """Compute D10 (Dasamsha) sign index from sidereal longitude.

    Each sign (30°) is divided into 10 parts of 3° each.
    - Odd signs count from the same sign
    - Even signs count from the 9th sign
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / 3.0)
    if part > 9:
        part = 9

    if sign_index % 2 == 0:  # Odd signs (1st, 3rd, etc. — 0-indexed even)
        start = sign_index
    else:  # Even signs
        start = (sign_index + 8) % 12  # 9th from current

    return (start + part) % 12


def compute_saptamsha_sign(longitude: float) -> int:
    """Compute D7 sign index.

    Each sign divided into 7 parts of ~4.2857°.
    Odd signs count from same sign, even signs count from 7th sign.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / (30.0 / 7.0))
    if part > 6:
        part = 6

    if sign_index % 2 == 0:  # Odd signs
        start = sign_index
    else:  # Even signs
        start = (sign_index + 6) % 12

    return (start + part) % 12


def compute_dwadashamsha_sign(longitude: float) -> int:
    """Compute D12 sign index.

    Each sign divided into 12 parts of 2.5° each.
    Always counts from the same sign.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / 2.5)
    if part > 11:
        part = 11

    return (sign_index + part) % 12


def compute_navamsha(chart: ChartData) -> list[DivisionalPosition]:
    """Compute D9 Navamsha for all planets in a chart."""
    results = []
    for planet_name in PLANETS:
        p = chart.planets[planet_name]
        d9_sign = compute_navamsha_sign(p.longitude)
        results.append(
            DivisionalPosition(
                planet=planet_name,
                d1_sign_index=p.sign_index,
                divisional_sign_index=d9_sign,
                divisional_sign=SIGNS[d9_sign],
                is_vargottam=(p.sign_index == d9_sign),
            )
        )
    return results


def compute_dasamsha(chart: ChartData) -> list[DivisionalPosition]:
    """Compute D10 Dasamsha for all planets in a chart."""
    results = []
    for planet_name in PLANETS:
        p = chart.planets[planet_name]
        d10_sign = compute_dasamsha_sign(p.longitude)
        results.append(
            DivisionalPosition(
                planet=planet_name,
                d1_sign_index=p.sign_index,
                divisional_sign_index=d10_sign,
                divisional_sign=SIGNS[d10_sign],
                is_vargottam=(p.sign_index == d10_sign),
            )
        )
    return results


def compute_saptamsha(chart: ChartData) -> list[DivisionalPosition]:
    """Compute D7 for all planets."""
    results = []
    for planet_name in PLANETS:
        p = chart.planets[planet_name]
        d7_sign = compute_saptamsha_sign(p.longitude)
        results.append(
            DivisionalPosition(
                planet=planet_name,
                d1_sign_index=p.sign_index,
                divisional_sign_index=d7_sign,
                divisional_sign=SIGNS[d7_sign],
                is_vargottam=(p.sign_index == d7_sign),
            )
        )
    return results


def compute_dwadashamsha(chart: ChartData) -> list[DivisionalPosition]:
    """Compute D12 for all planets."""
    results = []
    for planet_name in PLANETS:
        p = chart.planets[planet_name]
        d12_sign = compute_dwadashamsha_sign(p.longitude)
        results.append(
            DivisionalPosition(
                planet=planet_name,
                d1_sign_index=p.sign_index,
                divisional_sign_index=d12_sign,
                divisional_sign=SIGNS[d12_sign],
                is_vargottam=(p.sign_index == d12_sign),
            )
        )
    return results


def get_vargottam_planets(chart: ChartData) -> list[str]:
    """Return list of planets that are vargottam (same sign in D1 and D9)."""
    navamsha = compute_navamsha(chart)
    return [pos.planet for pos in navamsha if pos.is_vargottam]


# ── Re-export extended Shodashvarga functions for backward compatibility ─────
from daivai_engine.compute.divisional_extended import (  # noqa: E402
    compute_akshavedamsha_sign,
    compute_chaturthamsha_sign,
    compute_chaturvimshamsha_sign,
    compute_drekkana_sign,
    compute_hora_sign,
    compute_khavedamsha_sign,
    compute_panchamsha_sign,
    compute_saptavimshamsha_sign,
    compute_shashthamsha_sign,
    compute_shashtyamsha_sign,
    compute_shodashamsha_sign,
    compute_trimshamsha_sign,
    compute_vimshamsha_sign,
)


VARGA_FUNCTIONS: dict[str, Any] = {
    "D2": compute_hora_sign,
    "D3": compute_drekkana_sign,
    "D4": compute_chaturthamsha_sign,
    "D5": compute_panchamsha_sign,
    "D6": compute_shashthamsha_sign,
    "D7": compute_saptamsha_sign,
    "D9": compute_navamsha_sign,
    "D10": compute_dasamsha_sign,
    "D12": compute_dwadashamsha_sign,
    "D16": compute_shodashamsha_sign,
    "D20": compute_vimshamsha_sign,
    "D24": compute_chaturvimshamsha_sign,
    "D27": compute_saptavimshamsha_sign,
    "D30": compute_trimshamsha_sign,
    "D40": compute_khavedamsha_sign,
    "D45": compute_akshavedamsha_sign,
    "D60": compute_shashtyamsha_sign,
}


def compute_varga(chart: ChartData, varga: str) -> list[DivisionalPosition]:
    """Compute any varga chart for all planets.

    Args:
        chart: Computed birth chart
        varga: Varga name (D2, D3, D4, ..., D60)

    Returns:
        List of DivisionalPosition for all 9 planets.
    """
    func = VARGA_FUNCTIONS.get(varga)
    if func is None:
        raise ValueError(f"Unknown varga: {varga}. Available: {list(VARGA_FUNCTIONS.keys())}")

    results = []
    for planet_name in PLANETS:
        p = chart.planets[planet_name]
        div_sign = func(p.longitude)
        results.append(
            DivisionalPosition(
                planet=planet_name,
                d1_sign_index=p.sign_index,
                divisional_sign_index=div_sign,
                divisional_sign=SIGNS[div_sign],
                is_vargottam=(p.sign_index == div_sign),
            )
        )
    return results
