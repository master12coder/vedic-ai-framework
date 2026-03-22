"""Models for Rasi (sign-based) Dasha systems: Sthira, Shoola, Mandooka."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RasiDashaPeriod(BaseModel):
    """A single Mahadasha period in any Rasi (sign-based) dasha system.

    Used by Sthira, Shoola, and Mandooka dashas where each period is ruled
    by a zodiac sign rather than a planet.
    """

    model_config = ConfigDict(frozen=True)

    sign: str  # Vedic sign name (e.g. "Mithuna")
    sign_index: int  # 0-indexed sign position (0=Mesha … 11=Meena)
    years: int  # Full canonical duration for this sign in the system
    start: datetime
    end: datetime
    antardasha: list[RasiAntardasha] = []


class RasiAntardasha(BaseModel):
    """A sub-period (Antardasha) within a Rasi Dasha Mahadasha.

    Each Mahadasha's duration is divided proportionally among all 12 signs.
    """

    model_config = ConfigDict(frozen=True)

    sign: str  # Sub-period ruling sign
    sign_index: int
    start: datetime
    end: datetime


# Required for forward reference resolution in RasiDashaPeriod
RasiDashaPeriod.model_rebuild()
