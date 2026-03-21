"""Longevity (Ayurdaya) — three classical lifespan estimation methods.

Used internally for dasha impact analysis, NOT shown as a prediction.
All three methods classify into Alpayu/Madhyayu/Poornayu.

Methods implemented (BPHS Chapters 40-42):
  1. Pindayu    — sign/dignity-based contributions
  2. Amshayu    — navamsha-sign-based contributions (max 150 years)
  3. Naisargika — natural planetary strength (retrograde bonus, combust penalty)

The composite is the weighted average:  Pindayu*0.5 + Amshayu*0.3 + Naisargika*0.2

Source: BPHS Chapters 40-42.
"""

from __future__ import annotations

from pydantic import BaseModel

from daivai_engine.compute.divisional import compute_navamsha_sign
from daivai_engine.constants import DEBILITATION, EXALTATION, OWN_SIGNS
from daivai_engine.models.chart import ChartData


# Pindayu base contributions per planet — BPHS Ch.40
_PINDAYU_YEARS: dict[str, float] = {
    "Sun": 19.0,
    "Moon": 25.0,
    "Mars": 15.0,
    "Mercury": 12.0,
    "Jupiter": 15.0,
    "Venus": 21.0,
    "Saturn": 20.0,
}
_PINDAYU_MAX = 120.0
_AMSHAYU_MAX = 150.0  # Navamsha method has higher ceiling — BPHS Ch.41

# Longevity categories — BPHS Ch.41
_ALPAYU_MAX = 32.0
_MADHYAYU_MAX = 70.0


class LongevityResult(BaseModel):
    """Combined longevity estimation from all three classical methods."""

    # Pindayu (sign-based) — BPHS Ch.40
    pindayu_years: float
    # Amshayu (navamsha-based) — BPHS Ch.41
    amshayu_years: float
    # Naisargika (natural strength) — BPHS Ch.42
    naisargika_years: float
    # Composite weighted average
    composite_years: float
    category: str  # alpayu / madhyayu / poornayu
    category_hi: str  # अल्पायु / मध्यायु / पूर्णायु
    confidence: str  # high / medium / low
    breakdown: dict[str, float]  # Pindayu per-planet contribution
    amshayu_breakdown: dict[str, float]  # Amshayu per-planet contribution
    method_agreement: str  # all_agree / two_agree / disagree


def compute_longevity(chart: ChartData) -> LongevityResult:
    """Compute all three longevity methods and return composite result.

    CRITICAL: This is NEVER shown to end users as a prediction.
    Used internally for Pandit Ji analysis only.

    Source: BPHS Chapters 40-42.
    """
    pindayu, pindayu_breakdown = _compute_pindayu(chart)
    amshayu, amshayu_breakdown = _compute_amshayu(chart)
    naisargika = _compute_naisargika(chart)

    # Weighted composite: Pindayu 50%, Amshayu 30%, Naisargika 20%
    # Normalize Amshayu from 150-year scale to 120-year scale for weighting
    amshayu_normalized = min(amshayu * (_PINDAYU_MAX / _AMSHAYU_MAX), _PINDAYU_MAX)
    composite = (pindayu * 0.5) + (amshayu_normalized * 0.3) + (naisargika * 0.2)
    composite = round(min(composite, _PINDAYU_MAX), 1)

    # Classify each method
    def _categorize(years: float) -> str:
        if years <= _ALPAYU_MAX:
            return "alpayu"
        if years <= _MADHYAYU_MAX:
            return "madhyayu"
        return "poornayu"

    cats = [_categorize(pindayu), _categorize(amshayu), _categorize(composite)]
    if len(set(cats)) == 1:
        agreement = "all_agree"
        confidence = "high"
        final_cat = cats[0]
    elif len(set(cats)) == 2:
        agreement = "two_agree"
        confidence = "medium"
        # Majority rules
        final_cat = max(set(cats), key=cats.count)
    else:
        agreement = "disagree"
        confidence = "low"
        final_cat = _categorize(composite)

    hi_map = {"alpayu": "अल्पायु", "madhyayu": "मध्यायु", "poornayu": "पूर्णायु"}

    return LongevityResult(
        pindayu_years=pindayu,
        amshayu_years=amshayu,
        naisargika_years=naisargika,
        composite_years=composite,
        category=final_cat,
        category_hi=hi_map[final_cat],
        confidence=confidence,
        breakdown=pindayu_breakdown,
        amshayu_breakdown=amshayu_breakdown,
        method_agreement=agreement,
    )


# ── Pindayu ──────────────────────────────────────────────────────────────────


def _compute_pindayu(chart: ChartData) -> tuple[float, dict[str, float]]:
    """Pindayu: sign-dignity-based longevity — BPHS Ch.40.

    For each planet, base years modified by dignity:
    - Exalted: +1/3 (* 4/3)
    - Own/Mooltrikona: full years
    - Neutral/friend sign: 2/3
    - Debilitated: half years
    - Combust: * 0.75 reduction

    Source: BPHS Chapter 40.
    """
    breakdown: dict[str, float] = {}
    total = 0.0

    for name, base in _PINDAYU_YEARS.items():
        p = chart.planets[name]
        years = _pindayu_planet_years(name, base, p.sign_index, p.dignity)

        # Combustion reduces by 1/4 — BPHS Ch.40 v13
        if p.is_combust and name != "Sun":
            years *= 0.75

        breakdown[name] = round(years, 2)
        total += years

    return round(min(total, _PINDAYU_MAX), 1), breakdown


def _pindayu_planet_years(name: str, base: float, sign_index: int, dignity: str) -> float:
    """Apply Pindayu dignity modifications."""
    if EXALTATION.get(name) == sign_index:
        return base * (4.0 / 3.0)
    if dignity in ("own", "mooltrikona"):
        return base
    if DEBILITATION.get(name) == sign_index:
        return base * 0.5
    # Neutral or enemy sign
    return base * (2.0 / 3.0)


# ── Amshayu ───────────────────────────────────────────────────────────────────


def _compute_amshayu(chart: ChartData) -> tuple[float, dict[str, float]]:
    """Amshayu: navamsha-based longevity — BPHS Ch.41.

    Same formula as Pindayu but applied to the navamsha sign instead of
    the rashi sign. Planets in good navamsha positions give more years.
    Maximum: 150 years (higher ceiling than Pindayu).

    Source: BPHS Chapter 41.
    """
    breakdown: dict[str, float] = {}
    total = 0.0

    for name, base in _PINDAYU_YEARS.items():
        p = chart.planets[name]
        nav_sign = compute_navamsha_sign(p.longitude)
        years = _navamsha_years(name, base, nav_sign)

        # Combustion still reduces — BPHS
        if p.is_combust and name != "Sun":
            years *= 0.75

        breakdown[name] = round(years, 2)
        total += years

    return round(min(total, _AMSHAYU_MAX), 1), breakdown


def _navamsha_years(planet: str, base: float, nav_sign: int) -> float:
    """Apply Amshayu navamsha-dignity modifications."""
    if EXALTATION.get(planet) == nav_sign:
        return base * (4.0 / 3.0)
    if nav_sign in OWN_SIGNS.get(planet, []):
        return base
    if DEBILITATION.get(planet) == nav_sign:
        return base * 0.5
    return base * (2.0 / 3.0)


# ── Naisargika Ayu ────────────────────────────────────────────────────────────


def _compute_naisargika(chart: ChartData) -> float:
    """Naisargika Ayu: natural planetary-strength-based longevity — BPHS Ch.42.

    Uses the natural (naisargika) planetary years without sign-based modification.
    Retrograde planets gain 1/6 extra (they are stronger). Combust planets lose 1/4.

    This method shows the "default" lifespan based on how strong the planets are
    in their natural state regardless of sign placement.

    Source: BPHS Chapter 42.
    """
    total = 0.0
    for name, base in _PINDAYU_YEARS.items():
        p = chart.planets[name]
        years = base

        # Retrograde bonus: planets with retrograde motion gain strength — BPHS Ch.42
        if p.is_retrograde and name not in ("Sun", "Moon"):
            years += base / 6.0  # +1/6

        # Combustion penalty — reduces to 3/4
        if p.is_combust and name != "Sun":
            years *= 0.75

        total += years

    return round(min(total, _PINDAYU_MAX), 1)
