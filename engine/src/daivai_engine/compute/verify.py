"""Triple-layer chart accuracy verification.

Layer 1: Mathematical — sign/nakshatra/house consistency
Layer 2: Astronomical — Mercury/Venus max elongation, Moon speed, retrograde rules
Layer 3: Jyotish — dignity cross-check, dosha consistency

Run automatically after every chart computation.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel

from daivai_engine.constants import (
    CAZIMI_LIMIT,
    COMBUSTION_LIMITS,
    COMBUSTION_LIMITS_RETROGRADE,
    EXALTATION,
    NAKSHATRA_SPAN_DEG,
    NAKSHATRAS,
    NUM_NAKSHATRAS,
)
from daivai_engine.models.chart import ChartData


logger = logging.getLogger(__name__)


class VerificationReport(BaseModel):
    """Triple-layer verification result."""

    mathematical: list[str]  # Layer 1 issues
    astronomical: list[str]  # Layer 2 issues
    jyotish: list[str]  # Layer 3 issues
    is_clean: bool  # True if all layers empty

    @property
    def all_warnings(self) -> list[str]:
        """Flat list of all warnings."""
        return self.mathematical + self.astronomical + self.jyotish


def verify_chart_accuracy(chart: ChartData) -> list[str]:
    """Run all verification checks. Returns flat warning list.

    Backward-compatible wrapper around triple_verify().
    """
    report = triple_verify(chart)
    return report.all_warnings


def triple_verify(chart: ChartData) -> VerificationReport:
    """Run triple-layer verification on a computed chart.

    Args:
        chart: Computed birth chart.

    Returns:
        VerificationReport with issues categorized by layer.
    """
    math_w = _layer1_mathematical(chart)
    astro_w = _layer2_astronomical(chart)
    jyotish_w = _layer3_jyotish(chart)

    for w in math_w + astro_w + jyotish_w:
        logger.warning("Chart verification: %s", w)

    return VerificationReport(
        mathematical=math_w,
        astronomical=astro_w,
        jyotish=jyotish_w,
        # is_clean ignores informational alerts (SENSITIVE, SANDHI)
        is_clean=not (
            math_w
            or astro_w
            or [w for w in jyotish_w if "SENSITIVE" not in w and "SANDHI" not in w]
        ),
    )


# ── Layer 1: Mathematical Verification ───────────────────────────────────


def _layer1_mathematical(chart: ChartData) -> list[str]:
    """Check internal mathematical consistency."""
    w: list[str] = []

    # All longitudes 0-360
    for name, p in chart.planets.items():
        if not (0 <= p.longitude < 360):
            w.append(f"L1: {name} longitude {p.longitude} out of [0,360)")

    # Sign index matches longitude
    for name, p in chart.planets.items():
        expected = int(p.longitude / 30.0) % 12
        if expected != p.sign_index:
            w.append(f"L1: {name} sign mismatch: expected {expected}, got {p.sign_index}")

    # Degree in sign consistent
    for name, p in chart.planets.items():
        expected_deg = p.longitude - p.sign_index * 30.0
        if abs(expected_deg - p.degree_in_sign) > 0.001:
            w.append(f"L1: {name} degree_in_sign off by {abs(expected_deg - p.degree_in_sign):.4f}")

    # Nakshatra index matches longitude
    for name, p in chart.planets.items():
        expected_nak = min(int(p.longitude / NAKSHATRA_SPAN_DEG), NUM_NAKSHATRAS - 1)
        if expected_nak != p.nakshatra_index:
            w.append(
                f"L1: {name} nakshatra mismatch: expected {NAKSHATRAS[expected_nak]}, got {p.nakshatra}"
            )

    # House numbers 1-12
    for name, p in chart.planets.items():
        if not (1 <= p.house <= 12):
            w.append(f"L1: {name} invalid house {p.house}")

    # Rahu-Ketu 180° apart
    rahu = chart.planets.get("Rahu")
    ketu = chart.planets.get("Ketu")
    if rahu and ketu:
        diff = abs(rahu.longitude - ketu.longitude)
        if diff > 180:
            diff = 360 - diff
        if abs(diff - 180) > 0.01:
            w.append(f"L1: Rahu-Ketu not 180° apart: {diff:.4f}")

    # Ayanamsha 23-25° (Lahiri modern era)
    if not (23.0 < chart.ayanamsha < 25.0):
        w.append(f"L1: Ayanamsha {chart.ayanamsha:.4f} outside 23-25°")

    # Lagna sign matches lagna longitude
    expected_lagna = int(chart.lagna_longitude / 30.0) % 12
    if expected_lagna != chart.lagna_sign_index:
        w.append(
            f"L1: Lagna sign mismatch: expected {expected_lagna}, got {chart.lagna_sign_index}"
        )

    # No NaN/None in required fields
    for name, p in chart.planets.items():
        if p.longitude != p.longitude:  # NaN check
            w.append(f"L1: {name} longitude is NaN")

    return w


# ── Layer 2: Astronomical Cross-Check ────────────────────────────────────


def _layer2_astronomical(chart: ChartData) -> list[str]:
    """Verify astronomical constraints that must always hold."""
    w: list[str] = []
    sun_lon = chart.planets["Sun"].longitude

    # Mercury never more than 28° from Sun (astronomical fact — Surya Siddhanta)
    merc = chart.planets["Mercury"]
    merc_dist = _circular_dist(merc.longitude, sun_lon)
    if merc_dist > 28.0:
        w.append(f"L2: Mercury {merc_dist:.1f}° from Sun (max 28° — astronomical limit)")

    # Venus never more than 47° from Sun (astronomical fact)
    venus = chart.planets["Venus"]
    venus_dist = _circular_dist(venus.longitude, sun_lon)
    if venus_dist > 47.0:
        w.append(f"L2: Venus {venus_dist:.1f}° from Sun (max 47° — astronomical limit)")

    # Moon speed between 11.7°/day and 15.4°/day
    moon = chart.planets["Moon"]
    if not (11.5 <= abs(moon.speed) <= 15.5):
        w.append(f"L2: Moon speed {moon.speed:.2f}°/day outside normal range 11.5-15.5")

    # Sun is NEVER retrograde
    sun = chart.planets["Sun"]
    if sun.is_retrograde:
        w.append("L2: Sun marked retrograde — this is astronomically impossible")

    # Rahu/Ketu are ALWAYS retrograde
    for node in ("Rahu", "Ketu"):
        p = chart.planets.get(node)
        if p and not p.is_retrograde:
            w.append(f"L2: {node} not marked retrograde — nodes are always retrograde")

    # Combustion distances match planet-specific BPHS limits (Ch.25).
    # Cazimi (within 17') counts as is_cazimi=True, is_combust=False — not a mismatch.
    for name in ("Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        p = chart.planets[name]
        dist = _circular_dist(p.longitude, sun_lon)
        limit = COMBUSTION_LIMITS.get(name, 999)
        if p.is_retrograde and name in COMBUSTION_LIMITS_RETROGRADE:
            limit = COMBUSTION_LIMITS_RETROGRADE[name]
        is_cazimi = dist < CAZIMI_LIMIT
        computed_combust = (dist < limit) and not is_cazimi
        computed_cazimi = is_cazimi
        if p.is_combust != computed_combust:
            w.append(f"L2: {name} combustion mismatch: dist={dist:.2f}° limit={limit}°")
        if p.is_cazimi != computed_cazimi:
            w.append(
                f"L2: {name} cazimi mismatch: dist={dist:.2f}° cazimi_limit={CAZIMI_LIMIT:.4f}°"
            )

    # Retrograde matches negative speed (except nodes)
    for name, p in chart.planets.items():
        if name in ("Rahu", "Ketu"):
            continue
        if p.speed < 0 and not p.is_retrograde:
            w.append(f"L2: {name} speed={p.speed:.4f} but not retrograde")
        if p.speed > 0 and p.is_retrograde:
            w.append(f"L2: {name} speed={p.speed:.4f} but marked retrograde")

    return w


# ── Layer 3: Jyotish Consistency ─────────────────────────────────────────


def _layer3_jyotish(chart: ChartData) -> list[str]:
    """Verify Jyotish-specific consistency rules."""
    w: list[str] = []

    # Exaltation sign must match stored dignity
    for name, p in chart.planets.items():
        if name in ("Rahu", "Ketu"):
            continue  # Rahu/Ketu exaltation debated
        if p.dignity == "exalted" and EXALTATION.get(name) != p.sign_index:
            w.append(
                f"L3: {name} dignity='exalted' but sign {p.sign_index} "
                f"is not exaltation sign {EXALTATION.get(name)}"
            )
        if EXALTATION.get(name) == p.sign_index and p.dignity != "exalted":
            w.append(
                f"L3: {name} in exaltation sign {p.sign_index} "
                f"but dignity='{p.dignity}' (should be 'exalted')"
            )

    # No two planets (except Rahu/Ketu) at identical longitude
    lons: dict[str, float] = {}
    for name, p in chart.planets.items():
        for prev, prev_lon in lons.items():
            if abs(p.longitude - prev_lon) < 0.0001 and {name, prev} != {"Rahu", "Ketu"}:
                w.append(f"L3: {name} and {prev} at identical longitude {p.longitude:.4f}")
        lons[name] = p.longitude

    # Ayanamsha boundary sensitivity — flag planets where Lahiri vs Raman
    # would change sign/nakshatra/pada (delta ~1.5°)
    ayan_delta = 1.5  # Lahiri-Raman gap in degrees
    for name, p in chart.planets.items():
        sign_boundary = p.degree_in_sign
        nak_boundary = p.longitude % 13.3333
        if sign_boundary < ayan_delta or sign_boundary > (30.0 - ayan_delta):
            w.append(
                f"L3: AYANAMSHA SENSITIVE — {name} at {sign_boundary:.2f}° in sign, "
                f"would change SIGN under Raman ayanamsha"
            )
        if nak_boundary < ayan_delta or nak_boundary > (13.333 - ayan_delta):
            w.append(
                f"L3: AYANAMSHA SENSITIVE — {name} at nak boundary, "
                f"would change NAKSHATRA under Raman ayanamsha"
            )

    # Sandhi zone — planets in last 1° of sign are weakened (BPHS sign boundary doctrine)
    for name, p in chart.planets.items():
        if p.degree_in_sign > 29.0:
            w.append(
                f"L3: SANDHI — {name} at {p.degree_in_sign:.2f}° in sign "
                f"(last degree = transitional state)"
            )

    # Lagna Sandhi — birth time rectification critical if lagna near sign end
    if chart.lagna_degree > 28.0:
        w.append(
            f"L3: LAGNA SANDHI — Lagna at {chart.lagna_degree:.2f}° "
            f"(birth time error of 4 min could change lagna sign)"
        )

    return w


def _circular_dist(lon1: float, lon2: float) -> float:
    """Minimum angular distance between two longitudes."""
    diff = abs(lon1 - lon2) % 360.0
    return min(diff, 360.0 - diff)
