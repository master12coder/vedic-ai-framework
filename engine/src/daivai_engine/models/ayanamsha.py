"""Pydantic v2 models for ayanamsha (precession constant) computation.

Ayanamsha is the angular difference between the tropical and sidereal zodiacs,
driven by the precession of the equinoxes (~50.27 arcseconds/year). Every Vedic
chart computation depends on the correct ayanamsha system.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AyanamshaType(StrEnum):
    """Supported sidereal ayanamsha systems.

    Six systems covering all major Vedic and Western sidereal traditions.
    Inherits from StrEnum for JSON serialisation compatibility.
    """

    LAHIRI = "lahiri"
    KRISHNAMURTI = "krishnamurti"
    RAMAN = "raman"
    TRUE_CHITRAPAKSHA = "true_chitrapaksha"
    YUKTESHWAR = "yukteshwar"
    FAGAN_BRADLEY = "fagan_bradley"


class AyanamshaInfo(BaseModel):
    """Descriptive metadata for an ayanamsha system.

    Contains the human-readable name, scholarly description, founder,
    reference epoch, approximate value at J2000.0, and usage notes.
    Immutable — these are fixed reference data, not computed results.
    """

    model_config = ConfigDict(frozen=True)

    type: AyanamshaType
    name: str = Field(description="Full human-readable name of the system")
    description: str = Field(description="Scholarly description with key characteristics")
    founder: str | None = Field(default=None, description="Person who devised the system")
    reference_epoch: str = Field(description="Epoch at which the reference value is defined")
    reference_value_j2000: float = Field(
        description="Approximate ayanamsha in decimal degrees at J2000.0 (1 Jan 2000 12:00 TT)"
    )
    zero_year_ce: int | None = Field(
        default=None,
        description="Approximate year CE when tropical and sidereal zodiacs coincided",
    )
    usage: str = Field(description="Who uses this system and for what purpose")
    notes: str | None = Field(default=None, description="Additional caveats or technical notes")


class AyanamshaValue(BaseModel):
    """Computed ayanamsha result for a specific Julian Day and system.

    Holds the decimal-degree value, DMS-formatted string, and optionally
    the signed difference from the Lahiri system (positive = ahead of Lahiri).
    Immutable — a value object representing a point-in-time computation.
    """

    model_config = ConfigDict(frozen=True)

    julian_day: float = Field(description="Julian Day number (TT/TDB scale) used for computation")
    type: AyanamshaType = Field(description="Which ayanamsha system was used")
    value_degrees: float = Field(
        ge=0,
        lt=360,
        description="Ayanamsha value in decimal degrees (geocentric, true nutation included)",
    )
    value_dms: str = Field(
        description="Ayanamsha formatted as DD°MM'SS.SS\" (degrees, minutes, seconds)"
    )
    delta_from_lahiri: float | None = Field(
        default=None,
        description=(
            "Signed difference from Lahiri in decimal degrees. "
            "Positive = this system is ahead of Lahiri. "
            "Zero for LAHIRI itself. None when include_delta=False."
        ),
    )
