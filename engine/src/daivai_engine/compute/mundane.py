"""Mundane Astrology (Medini Jyotish) — country and world predictions.

Coordinator module. Computation is split across:
  mundane_chart.py  — country/foundation chart analysis, disaster yogas
  mundane_events.py — eclipse effects, Jupiter-Saturn cycles, ingress charts

Sources:
  Brihat Samhita (Varahamihira), BPHS Ch.71-75,
  Mantreswara's Phaladeepika, B.V. Raman's Mundane Astrology.
"""

from __future__ import annotations

# Re-export all public and private symbols for backward compatibility.
# Tests import private helpers (_get_nakshatra, _house_from_lagna, _longitude_to_sign)
# directly from this module.
from daivai_engine.compute.mundane_chart import (
    _BENEFICS,
    _DUSTHANAS,
    _MALEFICS,
    _MUNDANE_PLANETS,
    _get_nakshatra,
    _get_planet_longitude,
    _house_from_lagna,
    _longitude_to_sign,
    analyze_mundane_chart,
)
from daivai_engine.compute.mundane_events import (
    _date_to_jd,
    _find_sun_ingress,
    analyze_eclipse_effects,
    analyze_jupiter_saturn_cycle,
    compute_ingress_chart,
)


__all__ = [
    "_BENEFICS",
    "_DUSTHANAS",
    "_MALEFICS",
    "_MUNDANE_PLANETS",
    "_date_to_jd",
    "_find_sun_ingress",
    "_get_nakshatra",
    "_get_planet_longitude",
    "_house_from_lagna",
    "_longitude_to_sign",
    "analyze_eclipse_effects",
    "analyze_jupiter_saturn_cycle",
    "analyze_mundane_chart",
    "compute_ingress_chart",
]
