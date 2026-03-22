"""Shayanadi Avastha (12-fold) constants — sequence, results, and zone tables."""

from __future__ import annotations


# 12 avastha names in order for ODD signs — BPHS Ch.45 v21-35
_SHAYANADI_SEQUENCE: list[str] = [
    "shayana",  # 0-2.5°  — sleeping; planet gives very sluggish/delayed results
    "upavesha",  # 2.5-5°  — sitting; moderate and lazy results
    "netrapani",  # 5-7.5°  — tears; gives sorrowful results
    "prakasha",  # 7.5-10° — illumined; bright, good results
    "gamana",  # 10-12.5°— walking forward; progressive, improving results
    "agama",  # 12.5-15°— approaching; improving, somewhat delayed
    "sabha",  # 15-17.5°— assembly; dignified, public recognition
    "aagama",  # 17.5-20°— arrived; fulfilled, full results delivered
    "bhojana",  # 20-22.5°— eating; pleasure and enjoyment to native
    "nrityalipsya",  # 22.5-25°— wishing to dance; desires and artistic pleasures
    "kautuka",  # 25-27.5°— playful; light-hearted, curiosity
    "nidra",  # 27.5-30°— deep sleep; very sluggish, dormant results
]

_SHAYANADI_HI: list[str] = [
    "शयान",
    "उपवेश",
    "नेत्रपाणि",
    "प्रकाश",
    "गमन",
    "आगम",
    "सभा",
    "आगामी",
    "भोजन",
    "नृत्यलिप्सा",
    "कौतुक",
    "निद्रा",
]

# Positive states give good results; negative states give poor/delayed results
_SHAYANADI_POSITIVE: list[bool] = [
    False,  # shayana — negative
    False,  # upavesha — negative
    False,  # netrapani — negative
    True,  # prakasha — positive
    True,  # gamana — positive (mixed but generally positive)
    False,  # agama — negative (delay)
    True,  # sabha — positive
    True,  # aagama — positive
    True,  # bhojana — positive
    True,  # nrityalipsya — positive (desires fulfilled)
    True,  # kautuka — positive
    False,  # nidra — negative
]

# Classical result summaries from BPHS Ch.45
_SHAYANADI_RESULTS: list[str] = [
    "Planet in Shayana: delayed, sluggish results; native may lack energy from this planet",
    "Planet in Upavesha: moderate results, somewhat lazy or passive in its domain",
    "Planet in Netrapani: sorrowful results; emotional pain from this planet's significations",
    "Planet in Prakasha: bright and active; bestows good results in its domain",
    "Planet in Gamana: results improve over time; forward momentum in significations",
    "Planet in Agama: results approaching; some delay before fruits are enjoyed",
    "Planet in Sabha: dignified and respected; public recognition through this planet",
    "Planet in Aagama: results have arrived; full manifestation of significations",
    "Planet in Bhojana: pleasure and enjoyment; native savors the benefits",
    "Planet in Nrityalipsya: artistic pleasures and desires fulfilled",
    "Planet in Kautuka: light-hearted benefits; curiosity and exploration",
    "Planet in Nidra: dormant planet; results deeply delayed or suppressed",
]

# Strength fractions (for use in composite strength calculations)
_SHAYANADI_STRENGTH: list[float] = [
    0.25,
    0.40,
    0.20,
    0.85,
    0.70,
    0.45,
    0.80,
    0.90,
    0.85,
    0.75,
    0.70,
    0.15,
]

# Odd sign indices (Aries=0, Gemini=2, Leo=4, Libra=6, Sagittarius=8, Aquarius=10)
_ODD_SIGNS: frozenset[int] = frozenset({0, 2, 4, 6, 8, 10})

# Each zone spans 30°/12 = 2.5°
_ZONE_SPAN: float = 30.0 / 12.0
