"""Domain models for Vedic dosha detection results."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DoshaResult(BaseModel):
    """Represents the result of detecting a specific dosha in a chart.

    Contains the dosha name, presence flag, severity level, involved planets
    and houses, a description of the finding, and any cancellation reasons
    that may mitigate the dosha's effects.

    For Mangal Dosha, lagna_dosha / moon_dosha / venus_dosha indicate which
    reference points triggered (BPHS Ch.77, Phaladeepika).
    """

    model_config = ConfigDict(frozen=True)

    name: str
    name_hindi: str
    is_present: bool
    severity: str  # "full", "partial", "cancelled", "none"
    planets_involved: list[str]
    houses_involved: list[int]
    description: str
    cancellation_reasons: list[str]
    # Mangal Dosha: which reference points triggered
    lagna_dosha: bool = False
    moon_dosha: bool = False
    venus_dosha: bool = False
