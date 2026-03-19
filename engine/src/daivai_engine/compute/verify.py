"""Chart accuracy verification — internal consistency checks.

Catches OUR bugs in Swiss Ephemeris usage, not Swiss Ephemeris bugs.
Run automatically after every chart computation.
"""

from __future__ import annotations

import logging

from daivai_engine.constants import (
    COMBUSTION_LIMITS,
    COMBUSTION_LIMITS_RETROGRADE,
    NAKSHATRA_SPAN_DEG,
    NAKSHATRAS,
    NUM_NAKSHATRAS,
)
from daivai_engine.models.chart import ChartData


logger = logging.getLogger(__name__)


def verify_chart_accuracy(chart: ChartData) -> list[str]:
    """Run internal consistency checks on a computed chart.

    Returns list of warning strings. Empty = all checks passed.

    Args:
        chart: Computed birth chart.

    Returns:
        List of warning/error strings. Empty if clean.
    """
    warnings: list[str] = []

    # CHECK 1: All longitudes in valid range
    for name, p in chart.planets.items():
        if not (0 <= p.longitude < 360):
            warnings.append(f"ERROR: {name} longitude {p.longitude} out of [0,360)")

    # CHECK 2: Sign index matches longitude
    for name, p in chart.planets.items():
        expected_sign = int(p.longitude / 30.0) % 12
        if expected_sign != p.sign_index:
            warnings.append(
                f"ERROR: {name} sign mismatch: longitude gives sign {expected_sign}, "
                f"stored sign_index={p.sign_index}"
            )

    # CHECK 3: Degree in sign consistent with longitude
    for name, p in chart.planets.items():
        expected_deg = p.longitude - p.sign_index * 30.0
        if abs(expected_deg - p.degree_in_sign) > 0.001:
            warnings.append(
                f"ERROR: {name} degree_in_sign mismatch: "
                f"expected {expected_deg:.4f}, got {p.degree_in_sign:.4f}"
            )

    # CHECK 4: Nakshatra index matches longitude
    for name, p in chart.planets.items():
        expected_nak = int(p.longitude / NAKSHATRA_SPAN_DEG)
        if expected_nak >= NUM_NAKSHATRAS:
            expected_nak = NUM_NAKSHATRAS - 1
        if expected_nak != p.nakshatra_index:
            warnings.append(
                f"WARNING: {name} nakshatra mismatch: expected index {expected_nak} "
                f"({NAKSHATRAS[expected_nak]}), got {p.nakshatra_index} ({p.nakshatra})"
            )

    # CHECK 5: House numbers all 1-12
    for name, p in chart.planets.items():
        if not (1 <= p.house <= 12):
            warnings.append(f"ERROR: {name} invalid house number {p.house}")

    # CHECK 6: Rahu and Ketu exactly 180 deg apart
    rahu = chart.planets.get("Rahu")
    ketu = chart.planets.get("Ketu")
    if rahu and ketu:
        diff = abs(rahu.longitude - ketu.longitude)
        if diff > 180:
            diff = 360 - diff
        if abs(diff - 180) > 0.01:
            warnings.append(f"ERROR: Rahu-Ketu not 180° apart: diff={diff:.4f}")

    # CHECK 7: Ayanamsha reasonable for modern era (23-25° Lahiri)
    if not (23.0 < chart.ayanamsha < 25.0):
        warnings.append(f"WARNING: Ayanamsha {chart.ayanamsha:.4f} outside expected 23-25° range")

    # CHECK 8: Lagna sign index matches lagna longitude
    expected_lagna_sign = int(chart.lagna_longitude / 30.0) % 12
    if expected_lagna_sign != chart.lagna_sign_index:
        warnings.append(
            f"ERROR: Lagna sign mismatch: longitude gives {expected_lagna_sign}, "
            f"stored {chart.lagna_sign_index}"
        )

    # CHECK 9: Combustion status consistent with Sun distance
    sun_lon = chart.planets["Sun"].longitude
    for name in ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        p = chart.planets[name]
        dist = abs(p.longitude - sun_lon)
        if dist > 180:
            dist = 360 - dist
        limit = COMBUSTION_LIMITS.get(name, 999)
        if p.is_retrograde and name in COMBUSTION_LIMITS_RETROGRADE:
            limit = COMBUSTION_LIMITS_RETROGRADE[name]
        computed_combust = dist < limit
        if p.is_combust != computed_combust:
            warnings.append(
                f"WARNING: {name} combustion mismatch: distance={dist:.2f}, "
                f"limit={limit}, stored={p.is_combust}, computed={computed_combust}"
            )

    # CHECK 10: Retrograde matches negative speed
    for name, p in chart.planets.items():
        if name in ("Rahu", "Ketu"):
            continue  # Always retrograde by convention
        if p.speed < 0 and not p.is_retrograde:
            warnings.append(
                f"WARNING: {name} has negative speed ({p.speed:.4f}) but is_retrograde=False"
            )
        if p.speed > 0 and p.is_retrograde:
            warnings.append(
                f"WARNING: {name} has positive speed ({p.speed:.4f}) but is_retrograde=True"
            )

    # CHECK 11: No two planets (except Rahu/Ketu) have identical longitude
    lons: dict[str, float] = {}
    for name, p in chart.planets.items():
        for prev_name, prev_lon in lons.items():
            if abs(p.longitude - prev_lon) < 0.0001 and {name, prev_name} != {"Rahu", "Ketu"}:
                warnings.append(
                    f"WARNING: {name} and {prev_name} have near-identical "
                    f"longitude ({p.longitude:.4f})"
                )
        lons[name] = p.longitude

    for w in warnings:
        logger.warning("Chart verification: %s", w)

    return warnings
