"""Shadbala — six-fold planetary strength computation.

Re-exports all public and private symbols so that existing imports from
``daivai_engine.compute.strength`` continue to work unchanged.
"""

from __future__ import annotations

from daivai_engine.compute.strength.cheshta_bala import (
    _BENEFICS,
    _DIG_BEST,
    _MALEFICS,
    SHADBALA_PLANETS,
    _get_aspect_strength,
    compute_cheshta_bala,
    compute_dig_bala,
    compute_drik_bala,
    compute_yuddha_bala_adjustments,
)
from daivai_engine.compute.strength.cheshta_bala import (
    aspects_house as _aspects_house,
)
from daivai_engine.compute.strength.composite import (
    NAISARGIKA,
    REQUIRED_SHADBALA,
    compute_planet_strengths,
    compute_shadbala,
    get_strongest_planet,
    get_weakest_planet,
)
from daivai_engine.compute.strength.kala_bala import compute_kala_bala
from daivai_engine.compute.strength.kala_bala_helpers import (
    _CHALDEAN_ORDER,
    _abda_masa_cache,
    _compute_abda_masa_lords,
    _compute_hora_lord,
    _find_solar_ingress,
    _jd_to_day_planet,
    _tribhaga_bala,
)
from daivai_engine.compute.strength.sthana_bala import (
    _APOKLIMA,
    _PANAPARA,
    _SAPTVARGAJA_DIGNITY_PTS,
    _drekkana_bala,
    _kendradi_bala,
    _ojhayugma_bala,
    _saptvargaja_bala,
    _sign_dignity,
    _sign_dignity_full,
    _uchcha_bala,
    compute_sthana_bala,
)


# Backward-compat aliases for private names used in tests
_sthana_bala = compute_sthana_bala
_dig_bala = compute_dig_bala
_kala_bala = compute_kala_bala
_cheshta_bala = compute_cheshta_bala
_drik_bala = compute_drik_bala
_aspects_house = _aspects_house
_yuddha_bala_adjustments = compute_yuddha_bala_adjustments
_naisargika_bala = lambda planet_name: NAISARGIKA.get(planet_name, 0.0)  # noqa: E731

__all__ = [
    "NAISARGIKA",
    "REQUIRED_SHADBALA",
    "SHADBALA_PLANETS",
    "_APOKLIMA",
    "_BENEFICS",
    "_CHALDEAN_ORDER",
    "_DIG_BEST",
    "_MALEFICS",
    "_PANAPARA",
    "_SAPTVARGAJA_DIGNITY_PTS",
    "_abda_masa_cache",
    "_aspects_house",
    "_cheshta_bala",
    "_compute_abda_masa_lords",
    "_compute_hora_lord",
    "_dig_bala",
    "_drekkana_bala",
    "_drik_bala",
    "_find_solar_ingress",
    "_get_aspect_strength",
    "_jd_to_day_planet",
    "_kala_bala",
    "_kendradi_bala",
    "_naisargika_bala",
    "_ojhayugma_bala",
    "_saptvargaja_bala",
    "_sign_dignity",
    "_sign_dignity_full",
    "_sthana_bala",
    "_tribhaga_bala",
    "_uchcha_bala",
    "_yuddha_bala_adjustments",
    "compute_cheshta_bala",
    "compute_dig_bala",
    "compute_drik_bala",
    "compute_kala_bala",
    "compute_planet_strengths",
    "compute_shadbala",
    "compute_sthana_bala",
    "compute_yuddha_bala_adjustments",
    "get_strongest_planet",
    "get_weakest_planet",
]
