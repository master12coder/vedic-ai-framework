"""Domain models for transit event finder — ingress, stations, exact aspects."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TransitEvent(BaseModel):
    """Base model for a single planetary transit event.

    Represents any notable transit moment: sign ingress, retrograde/direct
    station, or exact aspect to a natal position.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    event_type: str  # "ingress" / "station_retrograde" / "station_direct" / "exact_aspect"
    date: datetime
    julian_day: float
    longitude: float = Field(ge=0, lt=360)  # sidereal longitude at event
    sign_index: int = Field(ge=0, le=11)
    sign: str
    description: str


class IngressEvent(TransitEvent):
    """A planet entering a specific sign.

    Source: Surya Siddhanta — sign boundary crossings are computed via
    sidereal longitude reaching exact multiples of 30 degrees.
    """

    target_sign_index: int = Field(ge=0, le=11)
    target_sign: str


class StationEvent(TransitEvent):
    """A planet reaching a retrograde or direct station (speed = 0).

    Source: Surya Siddhanta — stations occur where the daily
    speed of a planet crosses zero.
    """

    speed_before: float  # deg/day before station
    speed_after: float  # deg/day after station (sign change indicates R/D)


class AspectEvent(TransitEvent):
    """A transiting planet forming an exact aspect to a natal longitude.

    Source: BPHS Ch.26 — aspects considered: conjunction (0 deg),
    opposition (180), trine (120), square (90), sextile (60).
    """

    natal_longitude: float = Field(ge=0, lt=360)
    aspect_type: str  # "conjunction" / "opposition" / "trine" / "square" / "sextile"
    orb: float  # degrees of separation at exact moment
