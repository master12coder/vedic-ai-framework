"""Sthana Bala (positional strength) — component of Shadbala.

Covers: Uchcha Bala, Saptvargaja Bala, Ojhayugma Bala, Kendradi Bala,
Drekkana Bala. Source: BPHS Chapter 23.
"""

from __future__ import annotations

from daivai_engine.compute.divisional import (
    compute_drekkana_sign,
    compute_dwadashamsha_sign,
    compute_hora_sign,
    compute_navamsha_sign,
    compute_saptamsha_sign,
    compute_trimshamsha_sign,
)
from daivai_engine.constants import (
    DEBILITATION,
    EXALTATION,
    EXALTATION_DEGREE,
    KENDRAS,
    MOOLTRIKONA,
    NATURAL_ENEMIES,
    NATURAL_FRIENDS,
    OWN_SIGNS,
    SIGN_LORDS,
)
from daivai_engine.models.chart import ChartData


# Panapara and Apoklima houses for Kendradi Bala
_PANAPARA = {2, 5, 8, 11}
_APOKLIMA = {3, 6, 9, 12}

# Dignity point table for Saptvargaja Bala (per BPHS Ch.23)
_SAPTVARGAJA_DIGNITY_PTS: dict[str, float] = {
    "exalted": 45.0,
    "own": 30.0,
    "mooltrikona": 22.5,
    "friendly": 15.0,
    "neutral": 7.5,
    "enemy": 3.75,
    "debilitated": 1.875,
}


def _sign_dignity(planet_name: str, sign_index: int, deg_in_sign: float) -> str:
    """Determine planet dignity in a sign (replicates chart.py logic)."""
    if planet_name in EXALTATION and EXALTATION[planet_name] == sign_index:
        return "exalted"
    if planet_name in DEBILITATION and DEBILITATION[planet_name] == sign_index:
        return "debilitated"
    if planet_name in MOOLTRIKONA:
        mt_sign, mt_start, mt_end = MOOLTRIKONA[planet_name]
        if sign_index == mt_sign and mt_start <= deg_in_sign <= mt_end:
            return "mooltrikona"
    if planet_name in OWN_SIGNS and sign_index in OWN_SIGNS[planet_name]:
        return "own"
    return "neutral"


def _sign_dignity_full(planet_name: str, sign_index: int, deg_in_sign: float) -> str:
    """Extended dignity: exalted/debilitated/mooltrikona/own/friendly/neutral/enemy.

    Falls back to sign lord friendship when the planet has no special dignity.
    """
    basic = _sign_dignity(planet_name, sign_index, deg_in_sign)
    if basic != "neutral":
        return basic
    sign_lord = SIGN_LORDS.get(sign_index)
    if sign_lord is None:
        return "neutral"
    if sign_lord in NATURAL_FRIENDS.get(planet_name, []):
        return "friendly"
    if sign_lord in NATURAL_ENEMIES.get(planet_name, []):
        return "enemy"
    return "neutral"


def _uchcha_bala(planet_name: str, longitude: float) -> float:
    """Exaltation strength: max 60 at exact exaltation degree, 0 at debilitation."""
    if planet_name not in EXALTATION or planet_name not in EXALTATION_DEGREE:
        return 30.0  # Neutral for Rahu/Ketu if called

    exalt_sign = EXALTATION[planet_name]
    exalt_deg_in_sign = EXALTATION_DEGREE[planet_name]
    exalt_lon = exalt_sign * 30.0 + exalt_deg_in_sign

    diff = abs(longitude - exalt_lon)
    if diff > 180.0:
        diff = 360.0 - diff

    return (180.0 - diff) / 3.0


def _saptvargaja_bala(planet_name: str, longitude: float, sign_index: int) -> float:
    """Saptvargaja Bala across all 7 divisional charts (D1, D2, D3, D7, D9, D12, D30).

    Sums dignity points from each varga per BPHS Ch.23:
      exalted=45, own=30, mooltrikona=22.5, friendly=15,
      neutral=7.5, enemy=3.75, debilitated=1.875
    """
    deg_in_sign = longitude - sign_index * 30.0
    # (sign_index, deg_within_sign) for each varga; use 15.0 (mid-sign) for sub-vargas
    vargas: list[tuple[int, float]] = [
        (sign_index, deg_in_sign),  # D1 — exact degree
        (compute_hora_sign(longitude), 15.0),  # D2
        (compute_drekkana_sign(longitude), 15.0),  # D3
        (compute_saptamsha_sign(longitude), 15.0),  # D7
        (compute_navamsha_sign(longitude), 15.0),  # D9
        (compute_dwadashamsha_sign(longitude), 15.0),  # D12
        (compute_trimshamsha_sign(longitude), 15.0),  # D30
    ]
    total = 0.0
    for varga_sign, varga_deg in vargas:
        dignity = _sign_dignity_full(planet_name, varga_sign, varga_deg)
        total += _SAPTVARGAJA_DIGNITY_PTS.get(dignity, 7.5)
    return total


def _ojhayugma_bala(planet_name: str, sign_index: int, longitude: float) -> float:
    """Odd/even Rashi and Navamsha strength (15 each, max 30).

    Female planets (Moon, Venus) prefer even signs (Taurus=1, Cancer=3 …);
    all others prefer odd signs (Aries=0, Gemini=2 …).
    Applies independently to both the Rashi (D1) and Navamsha (D9) positions.
    Source: BPHS Ch.23 Ojhayugmarasyamsa Bala.
    """
    female = {"Moon", "Venus"}
    score = 0.0

    # Rashi component
    is_odd_rashi = sign_index % 2 == 0  # 0-indexed: Aries=0 is odd
    if planet_name in female:
        score += 15.0 if not is_odd_rashi else 0.0
    else:
        score += 15.0 if is_odd_rashi else 0.0

    # Navamsha component
    d9_sign = compute_navamsha_sign(longitude)
    is_odd_navamsha = d9_sign % 2 == 0
    if planet_name in female:
        score += 15.0 if not is_odd_navamsha else 0.0
    else:
        score += 15.0 if is_odd_navamsha else 0.0

    return score


def _kendradi_bala(house: int) -> float:
    """Kendra/Panapara/Apoklima strength."""
    if house in KENDRAS:
        return 60.0
    if house in _PANAPARA:
        return 30.0
    if house in _APOKLIMA:
        return 15.0
    return 15.0


def _drekkana_bala(planet_name: str, longitude: float) -> float:
    """Drekkana Bala based on D3 position.

    Male planets (Sun, Mars, Jupiter) strong in 1st drekkana (0-10 deg),
    neutral planets (Mercury, Saturn) in 2nd drekkana (10-20 deg),
    female planets (Moon, Venus) in 3rd drekkana (20-30 deg).
    """
    sign_index = int(longitude / 30.0)
    deg_in_sign = longitude - sign_index * 30.0

    if deg_in_sign < 10.0:
        drekkana = 1
    elif deg_in_sign < 20.0:
        drekkana = 2
    else:
        drekkana = 3

    male = {"Sun", "Mars", "Jupiter"}
    female = {"Moon", "Venus"}

    if planet_name in male and drekkana == 1:
        return 15.0
    if planet_name in female and drekkana == 3:
        return 15.0
    if planet_name not in male and planet_name not in female and drekkana == 2:
        return 15.0
    return 0.0


def compute_sthana_bala(chart: ChartData, planet_name: str) -> float:
    """Total Sthana Bala = sum of sub-components."""
    p = chart.planets[planet_name]
    uchcha = _uchcha_bala(planet_name, p.longitude)
    saptvar = _saptvargaja_bala(planet_name, p.longitude, p.sign_index)
    ojha = _ojhayugma_bala(planet_name, p.sign_index, p.longitude)
    kendra = _kendradi_bala(p.house)
    drekk = _drekkana_bala(planet_name, p.longitude)
    return round(uchcha + saptvar + ojha + kendra + drekk, 2)
