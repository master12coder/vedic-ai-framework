"""Hora (D2) chart analysis — wealth type and planetary hora quality.

D2 divides each sign into two 15 degree halves (horas). Parashari method:
  Odd signs  (0-indexed even): 0-15 deg = Sun Hora (Leo/4), 15-30 deg = Moon Hora (Cancer/3)
  Even signs (0-indexed odd):  0-15 deg = Moon Hora (Cancer/3), 15-30 deg = Sun Hora (Leo/4)

Natural hora assignments (Phaladeepika):
  Sun Hora  — Sun, Mars, Jupiter (fire/authority energy)
  Moon Hora — Moon, Venus, Saturn (receptive/material energy)
  Mercury   — neutral (placement-dependent)

Wealth indicators: count planets per hora, check lagna lord,
2nd lord (dhana bhava), and 11th lord (labha bhava).

Source: BPHS Chapter 6; Phaladeepika Chapter 3.
"""

from __future__ import annotations

from daivai_engine.compute.divisional import compute_hora_sign
from daivai_engine.constants import PLANETS, SIGN_LORDS
from daivai_engine.models.chart import ChartData
from daivai_engine.models.hora import HoraPlanet, HoraResult


_SUN_HORA_NATURALS = frozenset({"Sun", "Mars", "Jupiter"})
_MOON_HORA_NATURALS = frozenset({"Moon", "Venus", "Saturn"})


def _hora_name(hora_sign_index: int) -> str:
    """Return 'Sun' (Leo=4) or 'Moon' (Cancer=3) for the hora sign index."""
    return "Sun" if hora_sign_index == 4 else "Moon"


def _is_natural_hora(planet: str, hora: str) -> bool:
    """True if planet is in its traditionally assigned hora."""
    if hora == "Sun":
        return planet in _SUN_HORA_NATURALS
    if hora == "Moon":
        return planet in _MOON_HORA_NATURALS
    return False


def analyze_hora(chart: ChartData) -> HoraResult:
    """Analyze the D2 Hora chart for wealth and material indicators.

    Maps each of the 9 planets to Sun or Moon Hora, identifies natural
    hora alignments, determines the dominant hora, and checks the key
    wealth lords (lagna lord, 2nd lord, 11th lord).

    Args:
        chart: A fully computed birth chart.

    Returns:
        HoraResult with hora placements and wealth interpretation.
    """
    hora_planets: list[HoraPlanet] = []
    sun_hora: list[str] = []
    moon_hora: list[str] = []

    for planet_name in PLANETS:
        p = chart.planets[planet_name]
        hora_sign = compute_hora_sign(p.longitude)
        hora = _hora_name(hora_sign)
        natural = _is_natural_hora(planet_name, hora)

        hora_planets.append(
            HoraPlanet(
                planet=planet_name,
                hora=hora,
                hora_sign_index=hora_sign,
                is_natural_hora=natural,
                d1_sign_index=p.sign_index,
                degree_in_sign=p.degree_in_sign,
            )
        )
        if hora == "Sun":
            sun_hora.append(planet_name)
        else:
            moon_hora.append(planet_name)

    dominant = "Sun" if len(sun_hora) >= len(moon_hora) else "Moon"

    # Wealth lords: lagna (self), 2nd (dhana), 11th (labha)
    planet_hora_map = {hp.planet: hp.hora for hp in hora_planets}
    lagna_lord = SIGN_LORDS[chart.lagna_sign_index]
    second_lord = SIGN_LORDS[(chart.lagna_sign_index + 1) % 12]
    eleventh_lord = SIGN_LORDS[(chart.lagna_sign_index + 10) % 12]

    lagna_hora = planet_hora_map.get(lagna_lord, "unknown")
    second_hora = planet_hora_map.get(second_lord, "unknown")
    eleventh_hora = planet_hora_map.get(eleventh_lord, "unknown")

    wealth_type = _wealth_type(dominant, second_hora)
    summary = _build_summary(dominant, sun_hora, moon_hora, second_hora, eleventh_hora)

    return HoraResult(
        planets=hora_planets,
        sun_hora_planets=sun_hora,
        moon_hora_planets=moon_hora,
        dominant_hora=dominant,
        dominant_wealth_type=wealth_type,
        lagna_lord_hora=lagna_hora,
        second_lord_hora=second_hora,
        eleventh_lord_hora=eleventh_hora,
        summary=summary,
    )


def _wealth_type(dominant: str, second_hora: str) -> str:
    """Describe dominant wealth-acquisition mode."""
    if dominant == "Sun":
        return "Self-earned wealth through authority, government, or independent action"
    if dominant == "Moon":
        return "Wealth through others, partnerships, family inheritance, or accumulated assets"
    return "Balanced wealth from both earned and inherited sources"


def _build_summary(
    dominant: str,
    sun_hora: list[str],
    moon_hora: list[str],
    second_hora: str,
    eleventh_hora: str,
) -> str:
    """Compose a compact summary string."""
    parts = [f"Dominant: {dominant} Hora"]
    if sun_hora:
        parts.append(f"Sun Hora: {', '.join(sun_hora)}")
    if moon_hora:
        parts.append(f"Moon Hora: {', '.join(moon_hora)}")
    parts.append(f"2nd lord → {second_hora} Hora; 11th lord → {eleventh_hora} Hora")
    return "; ".join(parts)
