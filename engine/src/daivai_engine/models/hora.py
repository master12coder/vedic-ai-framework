"""Models for Hora (D2) chart analysis."""

from __future__ import annotations

from pydantic import BaseModel


class HoraPlanet(BaseModel):
    """Single planet's hora (D2) placement.

    hora_sign_index is always 3 (Cancer/Moon Hora) or 4 (Leo/Sun Hora).
    is_natural_hora is True when the planet is in its traditionally
    assigned hora (Sun/Mars/Jupiter → Sun Hora; Moon/Venus/Saturn → Moon Hora).
    """

    planet: str
    hora: str  # "Sun" or "Moon"
    hora_sign_index: int  # 3 = Cancer (Moon Hora), 4 = Leo (Sun Hora)
    is_natural_hora: bool
    d1_sign_index: int  # 0-11
    degree_in_sign: float


class HoraResult(BaseModel):
    """D2 Hora chart analysis result for a complete chart."""

    planets: list[HoraPlanet]
    sun_hora_planets: list[str]
    moon_hora_planets: list[str]
    dominant_hora: str  # "Sun" or "Moon" — whichever has more planets
    dominant_wealth_type: str
    lagna_lord_hora: str  # "Sun" or "Moon"
    second_lord_hora: str  # 2nd house lord's hora (dhana bhava)
    eleventh_lord_hora: str  # 11th house lord's hora (labha bhava)
    summary: str
