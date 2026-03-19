"""Vimshopaka Bala — planet strength across divisional charts.

Evaluates planet dignity in 6 or 16 vargas with BPHS-prescribed weights.
Higher score = planet consistently strong across multiple divisional charts.

Source: BPHS Chapters 16-17.
"""

from __future__ import annotations

from daivai_engine.compute.divisional import (
    compute_chaturthamsha_sign,
    compute_dasamsha_sign,
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
    MOOLTRIKONA,
    NATURAL_ENEMIES,
    NATURAL_FRIENDS,
    OWN_SIGNS,
    SIGN_LORDS,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.strength import VimshopakaBala


# Shadbarga weights (6 vargas): D1=3.5, D2=1, D3=1, D9=3, D12=0.5, D30=1
_SHADVARGA = {"D1": 3.5, "D2": 1.0, "D3": 1.0, "D9": 3.0, "D12": 0.5, "D30": 1.0}

# Shodashavarga (16 vargas) — using available implementations
# We compute what we can; missing vargas get neutral score
_SHODASHAVARGA = {
    "D1": 3.5,
    "D2": 1.0,
    "D3": 1.0,
    "D4": 0.5,
    "D7": 0.5,
    "D9": 3.0,
    "D10": 0.5,
    "D12": 0.5,
    "D30": 1.0,
}

_SHADVARGA_MAX = sum(_SHADVARGA.values())  # 10.0
_SHODASHA_MAX = 20.0  # Standard BPHS max

# Dignity points per varga
_DIGNITY_POINTS: dict[str, float] = {
    "exalted": 20.0,
    "mooltrikona": 18.0,
    "own": 15.0,
    "friend": 10.0,
    "neutral": 8.0,
    "enemy": 5.0,
    "debilitated": 2.0,
}

_PLANETS_7 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


def compute_vimshopaka_bala(chart: ChartData) -> list[VimshopakaBala]:
    """Compute Vimshopaka Bala for the 7 classical planets.

    Args:
        chart: Computed birth chart.

    Returns:
        List of VimshopakaBala, one per planet, sorted by score descending.
    """
    results: list[VimshopakaBala] = []
    for name in _PLANETS_7:
        p = chart.planets[name]
        lon = p.longitude

        # Compute sign index in each varga
        varga_signs: dict[str, int] = {
            "D1": p.sign_index,
            "D2": compute_hora_sign(lon),
            "D3": compute_drekkana_sign(lon),
            "D4": compute_chaturthamsha_sign(lon),
            "D7": compute_saptamsha_sign(lon),
            "D9": compute_navamsha_sign(lon),
            "D10": compute_dasamsha_sign(lon),
            "D12": compute_dwadashamsha_sign(lon),
            "D30": compute_trimshamsha_sign(lon),
        }

        # Compute dignity in each varga
        # For D1, pass actual degree; for others, use mid-sign (15°) approximation
        dignity_map: dict[str, str] = {}
        for varga, varga_sign in varga_signs.items():
            deg = p.degree_in_sign if varga == "D1" else 15.0
            dignity_map[varga] = _dignity_in_sign(name, varga_sign, deg)

        # Shadvarga score
        shadvarga = 0.0
        for varga, weight in _SHADVARGA.items():
            dig = dignity_map.get(varga, "neutral")
            points = _DIGNITY_POINTS.get(dig, 8.0)
            shadvarga += weight * (points / 20.0)

        # Shodashavarga score (scaled to max 20)
        shodasha_raw = 0.0
        shodasha_weight_sum = 0.0
        for varga, weight in _SHODASHAVARGA.items():
            dig = dignity_map.get(varga, "neutral")
            points = _DIGNITY_POINTS.get(dig, 8.0)
            shodasha_raw += weight * (points / 20.0)
            shodasha_weight_sum += weight

        # Scale to 20-point max
        shodasha = (shodasha_raw / shodasha_weight_sum) * 20.0 if shodasha_weight_sum else 0.0

        results.append(
            VimshopakaBala(
                planet=name,
                shadvarga_score=round(shadvarga, 2),
                shodashavarga_score=round(shodasha, 2),
                max_score=_SHODASHA_MAX,
                percentage=round((shodasha / _SHODASHA_MAX) * 100, 1),
                dignity_in_each=dignity_map,
            )
        )

    results.sort(key=lambda x: x.shodashavarga_score, reverse=True)
    return results


def _dignity_in_sign(planet: str, sign_idx: int, deg_in_sign: float = 15.0) -> str:
    """Determine planet's dignity in a given sign.

    Args:
        planet: Planet name.
        sign_idx: Sign index (0-11).
        deg_in_sign: Degree within sign (0-30). Defaults to mid-sign.
            Needed for accurate mooltrikona range check.
    """
    if EXALTATION.get(planet) == sign_idx:
        return "exalted"
    if DEBILITATION.get(planet) == sign_idx:
        return "debilitated"

    # Check mooltrikona — MUST verify degree is within range (BPHS Ch.16)
    mt = MOOLTRIKONA.get(planet)
    if mt and mt[0] == sign_idx and mt[1] <= deg_in_sign <= mt[2]:
        return "mooltrikona"

    # Check own sign (including mooltrikona sign but outside MT degree range)
    if sign_idx in OWN_SIGNS.get(planet, []):
        return "own"

    # Friend/enemy based on sign lord
    sign_lord = SIGN_LORDS.get(sign_idx, "")
    if sign_lord == planet:
        return "own"

    if sign_lord in NATURAL_FRIENDS.get(planet, []):
        return "friend"
    if sign_lord in NATURAL_ENEMIES.get(planet, []):
        return "enemy"
    return "neutral"
