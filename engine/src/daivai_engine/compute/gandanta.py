"""Gandanta detection — water-fire sign junction check.

Gandanta zones are the last 3 deg 20 min of a water sign to the first
3 deg 20 min of a fire sign. Planets (especially Moon) in these zones
indicate karmic challenges.

Source: BPHS, widely used in South Indian tradition.
"""

from __future__ import annotations

from daivai_engine.models.chart import ChartData
from daivai_engine.models.special import GandantaResult


# Gandanta junctions: (water_sign_index, fire_sign_index, junction_name)
_JUNCTIONS = [
    (3, 4, "Ashlesha-Magha"),  # Cancer → Leo
    (7, 8, "Jyeshtha-Moola"),  # Scorpio → Sagittarius
    (11, 0, "Revati-Ashwini"),  # Pisces → Aries
]

# Gandanta zone = 3 deg 20 min = 3.3333 degrees from junction
_ZONE_DEG = 10.0 / 3.0  # 3.3333...
_SEVERE_DEG = 1.0  # Within 1 degree = severe


def check_gandanta(chart: ChartData) -> list[GandantaResult]:
    """Check all planets and lagna for gandanta positions.

    Args:
        chart: Computed birth chart.

    Returns:
        List of GandantaResult for every planet (is_gandanta may be False).
    """
    results: list[GandantaResult] = []
    for name, p in chart.planets.items():
        result = _check_one(name, p.sign_index, p.degree_in_sign)
        results.append(result)
    return results


def _check_one(planet: str, sign_idx: int, deg: float) -> GandantaResult:
    """Check if a single planet is in a gandanta zone."""
    for water_sign, fire_sign, junction in _JUNCTIONS:
        # End of water sign: deg > (30 - zone)
        if sign_idx == water_sign and deg > (30.0 - _ZONE_DEG):
            dist_from_edge = 30.0 - deg
            severity = "severe" if dist_from_edge < _SEVERE_DEG else "mild"
            return GandantaResult(
                planet=planet,
                is_gandanta=True,
                gandanta_type="rashi_gandanta",
                junction=junction,
                degree=deg,
                severity=severity,
                remedial_note=_remedial(planet, severity),
            )
        # Start of fire sign: deg < zone
        if sign_idx == fire_sign and deg < _ZONE_DEG:
            severity = "severe" if deg < _SEVERE_DEG else "mild"
            return GandantaResult(
                planet=planet,
                is_gandanta=True,
                gandanta_type="nakshatra_gandanta",
                junction=junction,
                degree=deg,
                severity=severity,
                remedial_note=_remedial(planet, severity),
            )
    return GandantaResult(planet=planet, is_gandanta=False)


def _remedial(planet: str, severity: str) -> str:
    """Generate remedial note based on planet and severity."""
    if planet == "Moon":
        base = "Moon gandanta indicates emotional turbulence and karmic lessons."
    elif planet == "Sun":
        base = "Sun gandanta indicates identity/health challenges."
    else:
        base = f"{planet} gandanta weakens its significations."
    if severity == "severe":
        return f"{base} Severe — remedial measures strongly recommended."
    return f"{base} Mild — awareness and mantra practice advised."
