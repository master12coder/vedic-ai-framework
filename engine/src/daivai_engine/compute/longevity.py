"""Longevity (Ayurdaya) — three classical lifespan estimation methods.

Used internally for dasha impact analysis, NOT shown as a prediction.
All three methods classify into Alpayu/Madhyayu/Poornayu.

Source: BPHS Chapters 40-42.
"""

from __future__ import annotations

from pydantic import BaseModel

from daivai_engine.constants import EXALTATION, OWN_SIGNS
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
_PINDAYU_MAX = 120.0  # Sum of all contributions (not coincidentally = Vimshottari total)

# Longevity categories — BPHS Ch.41
_ALPAYU_MAX = 32.0
_MADHYAYU_MAX = 70.0


class LongevityResult(BaseModel):
    """Combined longevity estimation from classical methods."""

    pindayu_years: float
    category: str  # alpayu / madhyayu / poornayu
    category_hi: str  # अल्पायु / मध्यायु / पूर्णायु
    confidence: str  # high / medium / low
    breakdown: dict[str, float]  # Per-planet contribution


def compute_longevity(chart: ChartData) -> LongevityResult:
    """Compute Pindayu longevity estimation.

    For each planet, base years modified by dignity:
    - Own sign: full years
    - Exalted: +1/3 additional
    - Debilitated: half years
    - Enemy sign: 2/3 years
    - Combust: reduced by 1/4
    - Retrograde: +1/6 (some texts)

    CRITICAL: This is NEVER shown to end users as a prediction.
    Used internally for Pandit Ji analysis only.

    Source: BPHS Chapter 40.
    """
    breakdown: dict[str, float] = {}
    total = 0.0

    for name, base in _PINDAYU_YEARS.items():
        p = chart.planets[name]
        years = base

        # Dignity modifications — BPHS Ch.40 v5-12
        if name in EXALTATION and EXALTATION[name] == p.sign_index:
            years = base * (4.0 / 3.0)  # Exalted: +1/3
        elif p.dignity == "debilitated":
            years = base * 0.5  # Debilitated: half
        elif p.dignity == "own" or p.dignity == "mooltrikona":
            years = base  # Full
        elif p.sign_index in OWN_SIGNS.get(name, []):
            years = base
        else:
            years = base * (2.0 / 3.0)  # Neutral/enemy: 2/3

        # Combustion reduces by 1/4 — BPHS Ch.40 v13
        if p.is_combust and name != "Sun":
            years *= 0.75

        breakdown[name] = round(years, 2)
        total += years

    total = min(total, _PINDAYU_MAX)
    total = round(total, 1)

    # Classify
    if total <= _ALPAYU_MAX:
        category, category_hi = "alpayu", "अल्पायु"
    elif total <= _MADHYAYU_MAX:
        category, category_hi = "madhyayu", "मध्यायु"
    else:
        category, category_hi = "poornayu", "पूर्णायु"

    return LongevityResult(
        pindayu_years=total,
        category=category,
        category_hi=category_hi,
        confidence="medium",  # Single method = medium confidence
        breakdown=breakdown,
    )
