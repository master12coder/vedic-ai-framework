"""Domain models for Yoga activation timing analysis.

Maps detected yogas to their fructification dasha periods. A yoga is
a promise in the natal chart — it delivers results during the dasha
of the planets that form it.

Source: BPHS Ch.25, Phaladeepika Ch.20.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class YogaActivationPeriod(BaseModel):
    """A dasha period during which a yoga can activate.

    Activation strength depends on whether the forming planet is the
    MD lord (primary), AD lord (secondary), or both (dual = strongest).

    Source: BPHS Ch.25 — results fructify in dasha of yoga-forming planets.
    """

    model_config = ConfigDict(frozen=True)

    dasha_level: str  # "MD" / "AD" / "MD-AD"
    lord: str  # Dasha lord name (the planet activating)
    parent_lord: str | None = None  # MD lord (for AD-level periods)
    start: datetime
    end: datetime
    activation_strength: str  # "primary" / "secondary" / "dual"


class YogaTimingResult(BaseModel):
    """Timing analysis for a single yoga.

    Combines the natal yoga detection (planets, houses, effect, strength)
    with the full dasha timeline to identify WHEN the yoga will fructify.

    Source: Phaladeepika Ch.20 — yoga results manifest in dasha of
    forming planets.
    """

    model_config = ConfigDict(frozen=True)

    yoga_name: str
    planets_involved: list[str]
    houses_involved: list[int]
    effect: str  # "benefic" / "malefic" / "mixed"
    strength: str  # "full" / "partial" / "cancelled"

    # Activation windows across full dasha timeline
    activation_periods: list[YogaActivationPeriod]
    total_activation_years: float  # sum of all activation period durations

    # Current status
    is_currently_active: bool  # current MD or AD lord is a forming planet
    current_activation_strength: str | None  # "primary" / "secondary" / "dual" / None

    # Next activation
    next_activation: YogaActivationPeriod | None

    summary: str


class AllYogaTimings(BaseModel):
    """Timing analysis for all detected yogas in a chart.

    Aggregates individual yoga timing results and identifies which
    yogas are currently active, which are upcoming, and the single
    most significant upcoming activation.

    Source: BPHS Ch.25, Phaladeepika Ch.20.
    """

    model_config = ConfigDict(frozen=True)

    yogas: list[YogaTimingResult]
    currently_active_yogas: list[str]  # names of yogas active now
    upcoming_activations: list[tuple[str, str]]  # (yoga_name, period description)

    # Most significant upcoming activation
    most_significant: YogaTimingResult | None

    summary: str
