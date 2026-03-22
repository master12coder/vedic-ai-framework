"""All 32 Nabhasa Yoga detection — BPHS Chapter 13. Orchestrator.

Nabhasa yogas are "sky patterns" based on how the 7 classical planets
(Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn) are distributed
across signs and houses. Rahu and Ketu are excluded per BPHS.

Categories
----------
Ashraya (3)  — sign modality: all in movable / fixed / dual signs
Dala (2)     — benefic or malefic planets exclusively in kendras
Akriti (20)  — geometric house-distribution patterns
Sankhya (7)  — based on number of distinct houses occupied

Precedence: Akriti yogas take precedence over Sankhya yogas.
Among Sankhya yogas, exactly one applies (mutually exclusive).

Source: BPHS Chapter 13.
"""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData
from daivai_engine.compute.nabhasa_akriti import _akriti_yogas
from daivai_engine.compute.nabhasa_ashraya_dala import (
    _CLASSICAL,
    _ashraya_yogas,
    _consec,
    _dala_yogas,
    _r,
)
from daivai_engine.compute.nabhasa_sankhya import _sankhya_yoga
from daivai_engine.models.yoga import YogaResult


__all__ = [
    "_consec",
    "_r",
    "_sankhya_yoga",
    "detect_nabhasa_yogas",
]


def detect_nabhasa_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect all 32 Nabhasa (sky pattern) yogas — BPHS Ch.13.

    Only the 7 classical planets are considered; Rahu/Ketu are excluded.
    Akriti yogas take precedence over Sankhya yogas when both conditions
    are satisfied.  Among Sankhya yogas, exactly one applies.

    Args:
        chart: Computed birth chart.

    Returns:
        List of detected Nabhasa YogaResults (all have is_present=True).
    """
    # Gather sign indices and house numbers for the 7 classical planets
    signs: list[int] = []
    houses: list[int] = []
    for name, p in chart.planets.items():
        if name in _CLASSICAL:
            signs.append(p.sign_index)
            houses.append(p.house)

    house_set = set(houses)
    n_houses = len(house_set)

    yogas: list[YogaResult] = []
    yogas.extend(_ashraya_yogas(signs))
    yogas.extend(_dala_yogas(chart))

    akriti = _akriti_yogas(chart, houses, house_set)
    yogas.extend(akriti)

    # Sankhya yogas only when no Akriti yoga applies
    if not akriti:
        sankhya = _sankhya_yoga(n_houses)
        if sankhya:
            yogas.append(sankhya)

    return yogas
