"""Divisional chart computations — all 16 Shodashvarga charts."""

from __future__ import annotations


from jyotish.utils.constants import SIGNS, PLANETS
from jyotish.compute.chart import ChartData
from jyotish.domain.models.divisional import DivisionalPosition


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
    water_signs = {3, 7, 11}

    if sign_index in fire_signs:
        start = 0   # Aries
    elif sign_index in earth_signs:
        start = 9   # Capricorn
    elif sign_index in air_signs:
        start = 6   # Libra
    else:  # water
        start = 3   # Cancer

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
        results.append(DivisionalPosition(
            planet=planet_name,
            d1_sign_index=p.sign_index,
            divisional_sign_index=d9_sign,
            divisional_sign=SIGNS[d9_sign],
            is_vargottam=(p.sign_index == d9_sign),
        ))
    return results


def compute_dasamsha(chart: ChartData) -> list[DivisionalPosition]:
    """Compute D10 Dasamsha for all planets in a chart."""
    results = []
    for planet_name in PLANETS:
        p = chart.planets[planet_name]
        d10_sign = compute_dasamsha_sign(p.longitude)
        results.append(DivisionalPosition(
            planet=planet_name,
            d1_sign_index=p.sign_index,
            divisional_sign_index=d10_sign,
            divisional_sign=SIGNS[d10_sign],
            is_vargottam=(p.sign_index == d10_sign),
        ))
    return results


def compute_saptamsha(chart: ChartData) -> list[DivisionalPosition]:
    """Compute D7 for all planets."""
    results = []
    for planet_name in PLANETS:
        p = chart.planets[planet_name]
        d7_sign = compute_saptamsha_sign(p.longitude)
        results.append(DivisionalPosition(
            planet=planet_name,
            d1_sign_index=p.sign_index,
            divisional_sign_index=d7_sign,
            divisional_sign=SIGNS[d7_sign],
            is_vargottam=(p.sign_index == d7_sign),
        ))
    return results


def compute_dwadashamsha(chart: ChartData) -> list[DivisionalPosition]:
    """Compute D12 for all planets."""
    results = []
    for planet_name in PLANETS:
        p = chart.planets[planet_name]
        d12_sign = compute_dwadashamsha_sign(p.longitude)
        results.append(DivisionalPosition(
            planet=planet_name,
            d1_sign_index=p.sign_index,
            divisional_sign_index=d12_sign,
            divisional_sign=SIGNS[d12_sign],
            is_vargottam=(p.sign_index == d12_sign),
        ))
    return results


def get_vargottam_planets(chart: ChartData) -> list[str]:
    """Return list of planets that are vargottam (same sign in D1 and D9)."""
    navamsha = compute_navamsha(chart)
    return [pos.planet for pos in navamsha if pos.is_vargottam]


# ── Additional Shodashvarga Charts ──────────────────────────────────────────


def compute_hora_sign(longitude: float) -> int:
    """Compute D2 (Hora) sign index.

    Each sign divided into 2 parts of 15° each.
    Odd signs: 1st hora = Sun (Leo/4), 2nd hora = Moon (Cancer/3)
    Even signs: 1st hora = Moon (Cancer/3), 2nd hora = Sun (Leo/4)
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    first_half = degree_in_sign < 15.0
    if sign_index % 2 == 0:  # Odd signs
        return 4 if first_half else 3  # Leo then Cancer
    else:  # Even signs
        return 3 if first_half else 4  # Cancer then Leo


def compute_drekkana_sign(longitude: float) -> int:
    """Compute D3 (Drekkana) sign index.

    Each sign divided into 3 parts of 10°.
    1st decanate: same sign
    2nd decanate: 5th from sign
    3rd decanate: 9th from sign
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / 10.0)
    if part > 2:
        part = 2
    offsets = [0, 4, 8]
    return (sign_index + offsets[part]) % 12


def compute_chaturthamsha_sign(longitude: float) -> int:
    """Compute D4 (Chaturthamsha) sign index.

    Each sign divided into 4 parts of 7.5°.
    Counts from same sign, 4th, 7th, 10th.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / 7.5)
    if part > 3:
        part = 3
    offsets = [0, 3, 6, 9]
    return (sign_index + offsets[part]) % 12


def compute_panchamsha_sign(longitude: float) -> int:
    """Compute D5 (Panchamsha) sign index.

    Each sign divided into 5 parts of 6°.
    Odd signs start from same sign, even signs start from opposite.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / 6.0)
    if part > 4:
        part = 4
    if sign_index % 2 == 0:
        start = sign_index
    else:
        start = (sign_index + 6) % 12
    return (start + part) % 12


def compute_shashthamsha_sign(longitude: float) -> int:
    """Compute D6 (Shashthamsha) sign index.

    Each sign divided into 6 parts of 5°.
    Odd signs start from same sign, even signs start from 7th.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / 5.0)
    if part > 5:
        part = 5
    if sign_index % 2 == 0:
        start = sign_index
    else:
        start = (sign_index + 6) % 12
    return (start + part) % 12


def compute_shodashamsha_sign(longitude: float) -> int:
    """Compute D16 (Shodashamsha) sign index.

    Each sign divided into 16 parts of 1.875°.
    Movable signs start from Aries, fixed from Leo, dual from Sagittarius.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / (30.0 / 16.0))
    if part > 15:
        part = 15
    modality = sign_index % 3  # 0=movable, 1=fixed, 2=dual
    start_map = {0: 0, 1: 4, 2: 8}
    return (start_map[modality] + part) % 12


def compute_vimshamsha_sign(longitude: float) -> int:
    """Compute D20 (Vimshamsha) sign index.

    Each sign divided into 20 parts of 1.5°.
    Movable from Aries, fixed from Sagittarius, dual from Leo.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / 1.5)
    if part > 19:
        part = 19
    modality = sign_index % 3
    start_map = {0: 0, 1: 8, 2: 4}
    return (start_map[modality] + part) % 12


def compute_chaturvimshamsha_sign(longitude: float) -> int:
    """Compute D24 (Chaturvimshamsha/Siddhamsha) sign index.

    Each sign divided into 24 parts of 1.25°.
    Odd signs from Leo, even signs from Cancer.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / 1.25)
    if part > 23:
        part = 23
    start = 4 if sign_index % 2 == 0 else 3
    return (start + part) % 12


def compute_saptavimshamsha_sign(longitude: float) -> int:
    """Compute D27 (Saptavimshamsha/Nakshatramsha) sign index.

    Each sign divided into 27 parts of ~1.111°.
    Fire signs from Aries, earth from Cancer, air from Libra, water from Capricorn.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / (30.0 / 27.0))
    if part > 26:
        part = 26
    element = sign_index % 4
    start_map = {0: 0, 1: 3, 2: 6, 3: 9}
    return (start_map[element] + part) % 12


def compute_trimshamsha_sign(longitude: float) -> int:
    """Compute D30 (Trimshamsha) sign index.

    Non-uniform division. For odd signs:
    0-5° Mars, 5-10° Saturn, 10-18° Jupiter, 18-25° Mercury, 25-30° Venus
    Even signs reverse order.
    Returns the sign owned by the ruling planet.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0

    if sign_index % 2 == 0:  # Odd sign
        if degree_in_sign < 5:
            ruler = 0   # Mars -> Aries
        elif degree_in_sign < 10:
            ruler = 10  # Saturn -> Aquarius
        elif degree_in_sign < 18:
            ruler = 8   # Jupiter -> Sagittarius
        elif degree_in_sign < 25:
            ruler = 2   # Mercury -> Gemini
        else:
            ruler = 6   # Venus -> Libra
    else:  # Even sign
        if degree_in_sign < 5:
            ruler = 1   # Venus -> Taurus
        elif degree_in_sign < 12:
            ruler = 5   # Mercury -> Virgo
        elif degree_in_sign < 20:
            ruler = 11  # Jupiter -> Pisces
        elif degree_in_sign < 25:
            ruler = 9   # Saturn -> Capricorn
        else:
            ruler = 7   # Mars -> Scorpio
    return ruler


def compute_khavedamsha_sign(longitude: float) -> int:
    """Compute D40 (Khavedamsha) sign index.

    Each sign divided into 40 parts of 0.75°.
    Odd signs from Aries, even signs from Libra.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / 0.75)
    if part > 39:
        part = 39
    start = 0 if sign_index % 2 == 0 else 6
    return (start + part) % 12


def compute_akshavedamsha_sign(longitude: float) -> int:
    """Compute D45 (Akshavedamsha) sign index.

    Each sign divided into 45 parts of 0.6667°.
    Movable from Aries, fixed from Leo, dual from Sagittarius.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / (30.0 / 45.0))
    if part > 44:
        part = 44
    modality = sign_index % 3
    start_map = {0: 0, 1: 4, 2: 8}
    return (start_map[modality] + part) % 12


def compute_shashtyamsha_sign(longitude: float) -> int:
    """Compute D60 (Shashtyamsha) sign index.

    Each sign divided into 60 parts of 0.5°.
    Always counts from same sign.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / 0.5)
    if part > 59:
        part = 59
    return (sign_index + part) % 12


# ── Generic Varga Computation ───────────────────────────────────────────────

VARGA_FUNCTIONS: dict[str, callable] = {
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
        results.append(DivisionalPosition(
            planet=planet_name,
            d1_sign_index=p.sign_index,
            divisional_sign_index=div_sign,
            divisional_sign=SIGNS[div_sign],
            is_vargottam=(p.sign_index == div_sign),
        ))
    return results
