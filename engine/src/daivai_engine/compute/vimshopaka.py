"""Vimshopaka Bala — planet strength across divisional charts.

Evaluates planet dignity in 6, 7, 10, or 16 vargas with BPHS-prescribed
weights. Higher score = planet consistently strong across multiple charts.

Source: BPHS Chapters 16-17.
"""

from __future__ import annotations

from daivai_engine.compute.divisional import (
    compute_akshavedamsha_sign,
    compute_chaturthamsha_sign,
    compute_chaturvimshamsha_sign,
    compute_dasamsha_sign,
    compute_drekkana_sign,
    compute_dwadashamsha_sign,
    compute_hora_sign,
    compute_khavedamsha_sign,
    compute_navamsha_sign,
    compute_saptamsha_sign,
    compute_saptavimshamsha_sign,
    compute_shashtyamsha_sign,
    compute_shodashamsha_sign,
    compute_trimshamsha_sign,
    compute_vimshamsha_sign,
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


# ── Varga weight schemes (BPHS Ch.16-17) ────────────────────────────────────

# Shadvarga (6 vargas) — total weight: 10.0
_SHADVARGA: dict[str, float] = {
    "D1": 3.5,
    "D2": 1.0,
    "D3": 1.0,
    "D9": 3.0,
    "D12": 0.5,
    "D30": 1.0,
}

# Saptvarga (7 vargas) — total weight: 20.0
_SAPTVARGA: dict[str, float] = {
    "D1": 5.0,
    "D2": 2.0,
    "D3": 3.0,
    "D7": 4.5,
    "D9": 2.5,
    "D12": 2.0,
    "D30": 1.0,
}

# Dashavarga (10 vargas) — total weight: 20.0
_DASHAVARGA: dict[str, float] = {
    "D1": 3.0,
    "D2": 1.5,
    "D3": 1.5,
    "D7": 1.5,
    "D9": 1.5,
    "D10": 1.5,
    "D12": 1.5,
    "D16": 1.5,
    "D30": 1.5,
    "D60": 5.0,
}

# Shodashavarga (16 vargas) — total weight: 20.0
_SHODASHAVARGA: dict[str, float] = {
    "D1": 3.5,
    "D2": 1.0,
    "D3": 1.0,
    "D4": 0.5,
    "D7": 0.5,
    "D9": 3.0,
    "D10": 0.5,
    "D12": 0.5,
    "D16": 2.0,
    "D20": 0.5,
    "D24": 0.5,
    "D27": 0.5,
    "D30": 1.0,
    "D40": 0.5,
    "D45": 0.5,
    "D60": 4.0,
}

_SHADVARGA_MAX = sum(_SHADVARGA.values())  # 10.0
_SHODASHA_MAX = 20.0  # Standard BPHS max for Saptvarga, Dashavarga, Shodashavarga

# Dignity points (normalized to 20-point scale)
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


def _scheme_score(dignity_map: dict[str, str], scheme: dict[str, float]) -> float:
    """Compute weighted dignity score for a varga scheme, scaled to 20.

    Args:
        dignity_map: Varga name → dignity string for one planet.
        scheme: Varga name → weight for the desired scheme.

    Returns:
        Weighted score scaled so that maximum possible = 20.0.
    """
    raw = sum(w * (_DIGNITY_POINTS.get(dignity_map[v], 8.0) / 20.0) for v, w in scheme.items())
    total_w = sum(scheme.values())
    return (raw / total_w) * _SHODASHA_MAX if total_w else 0.0


def compute_vimshopaka_bala(chart: ChartData) -> list[VimshopakaBala]:
    """Compute Vimshopaka Bala for the 7 classical planets (all 4 schemes).

    Args:
        chart: Computed birth chart.

    Returns:
        List of VimshopakaBala, one per planet, sorted by shodashavarga score.
    """
    results: list[VimshopakaBala] = []
    for name in _PLANETS_7:
        p = chart.planets[name]
        lon = p.longitude

        # Sign index in each varga (D1 uses natal position)
        varga_signs: dict[str, int] = {
            "D1": p.sign_index,
            "D2": compute_hora_sign(lon),
            "D3": compute_drekkana_sign(lon),
            "D4": compute_chaturthamsha_sign(lon),
            "D7": compute_saptamsha_sign(lon),
            "D9": compute_navamsha_sign(lon),
            "D10": compute_dasamsha_sign(lon),
            "D12": compute_dwadashamsha_sign(lon),
            "D16": compute_shodashamsha_sign(lon),
            "D20": compute_vimshamsha_sign(lon),
            "D24": compute_chaturvimshamsha_sign(lon),
            "D27": compute_saptavimshamsha_sign(lon),
            "D30": compute_trimshamsha_sign(lon),
            "D40": compute_khavedamsha_sign(lon),
            "D45": compute_akshavedamsha_sign(lon),
            "D60": compute_shashtyamsha_sign(lon),
        }

        # Dignity in each varga (D1 uses actual degree; others use mid-sign)
        dignity_map: dict[str, str] = {}
        for varga, vsign in varga_signs.items():
            deg = p.degree_in_sign if varga == "D1" else 15.0
            dignity_map[varga] = _dignity_in_sign(name, vsign, deg)

        # Shadvarga on its native 10-point scale (raw weighted sum, no normalisation)
        shadvarga_raw = sum(
            w * (_DIGNITY_POINTS.get(dignity_map[v], 8.0) / 20.0) for v, w in _SHADVARGA.items()
        )
        sapt_score = _scheme_score(dignity_map, _SAPTVARGA)
        dash_score = _scheme_score(dignity_map, _DASHAVARGA)
        shodasha_score = _scheme_score(dignity_map, _SHODASHAVARGA)

        results.append(
            VimshopakaBala(
                planet=name,
                shadvarga_score=round(shadvarga_raw, 2),
                saptvarga_score=round(sapt_score, 2),
                dashavarga_score=round(dash_score, 2),
                shodashavarga_score=round(shodasha_score, 2),
                max_score=_SHODASHA_MAX,
                percentage=round((shodasha_score / _SHODASHA_MAX) * 100, 1),
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
