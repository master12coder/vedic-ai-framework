"""Models for conditional nakshatra-based Dasha systems.

Covers: Dwisaptati Sama (72yr), Shatabdika (100yr), Chaturaseeti Sama (84yr),
Dwadashottari (112yr), Panchottari (105yr), Shashtihayani (60yr),
Shatrimsha Sama (36yr).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConditionalDashaPeriod(BaseModel):
    """A single Mahadasha period in a conditional nakshatra-based dasha system.

    All conditional systems share this structure — only the planet sequence
    and applicability condition differ between systems.
    """

    model_config = ConfigDict(frozen=True)

    planet: str  # Ruling planet name
    years: int  # Canonical full duration for this planet in the system
    start: datetime
    end: datetime
    antardasha: list[ConditionalAntardasha] = []


class ConditionalAntardasha(BaseModel):
    """A sub-period (Antardasha) within a conditional Mahadasha.

    Duration = MD_days x (AD_planet_years / total_system_years).
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    start: datetime
    end: datetime


# Required for forward reference resolution
ConditionalDashaPeriod.model_rebuild()
