"""Helper functions for eclipse detection and impact classification.

Provides New Moon / Full Moon finders, orb computation, severity
classification, and planet signification lookups used by eclipse_natal.

Source: Surya Siddhanta — eclipse conditions and lunation computation.
"""

from __future__ import annotations

import swisseph as swe

from daivai_engine.constants import FULL_CIRCLE_DEG


# ── Constants ────────────────────────────────────────────────────────────────

ECLIPSE_NODE_ORB = 18.0  # Max degrees from Rahu/Ketu for eclipse to occur
SYNODIC_MONTH = 29.530588  # Average lunation in days
DEFAULT_IMPACT_ORB = 5.0  # Degrees within which eclipse affects natal point

# Planet significations for impact descriptions
SIGNIFICATIONS: dict[str, list[str]] = {
    "Sun": ["self", "father", "authority", "vitality", "career"],
    "Moon": ["mind", "mother", "emotions", "public image"],
    "Mars": ["energy", "siblings", "courage", "property"],
    "Mercury": ["intellect", "speech", "commerce", "education"],
    "Jupiter": ["wisdom", "children", "guru", "fortune"],
    "Venus": ["relationships", "spouse", "luxury", "arts"],
    "Saturn": ["longevity", "discipline", "karma", "delays"],
    "Rahu": ["obsession", "foreign", "unconventional", "ambition"],
    "Ketu": ["spirituality", "detachment", "past life", "liberation"],
    "Lagna": ["self", "body", "personality", "life direction"],
}


# ── Helpers ──────────────────────────────────────────────────────────────────


def sidereal_lon_by_id(jd: float, swe_id: int) -> float:
    """Compute sidereal longitude for a Swiss Ephemeris body.

    Args:
        jd: Julian Day (UT).
        swe_id: Swiss Ephemeris body constant.

    Returns:
        Sidereal longitude in degrees.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    result = swe.calc_ut(jd, swe_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)
    return float(result[0][0])


def orb_between(lon_a: float, lon_b: float) -> float:
    """Compute shortest-arc orb between two longitudes (always positive).

    Args:
        lon_a: First longitude in degrees.
        lon_b: Second longitude in degrees.

    Returns:
        Positive angular separation in degrees.
    """
    diff = abs(lon_a - lon_b)
    if diff > 180.0:
        diff = FULL_CIRCLE_DEG - diff
    return diff


def classify_severity(orb: float) -> str:
    """Classify impact severity by orb distance.

    Args:
        orb: Angular separation in degrees.

    Returns:
        "exact" (<1 deg), "strong" (1-3), "moderate" (3-5), "none" (>5).
    """
    if orb < 1.0:
        return "exact"
    if orb < 3.0:
        return "strong"
    if orb < 5.0:
        return "moderate"
    return "none"


def find_new_moons(start_jd: float, end_jd: float) -> list[float]:
    """Find Julian Days of New Moons (Sun-Moon conjunction) in the period.

    Uses daily stepping with binary search refinement.

    Args:
        start_jd: Start Julian Day.
        end_jd: End Julian Day.

    Returns:
        List of Julian Days for each New Moon.
    """
    new_moons: list[float] = []
    jd = start_jd
    while jd < end_jd:
        sun_lon = sidereal_lon_by_id(jd, swe.SUN)
        moon_lon = sidereal_lon_by_id(jd, swe.MOON)
        diff = orb_between(sun_lon, moon_lon)

        if diff < 15.0:
            # Refine with binary search
            lo, hi = jd - 1.0, jd + 1.0
            for _ in range(20):
                mid = (lo + hi) / 2.0
                s = sidereal_lon_by_id(mid, swe.SUN)
                m = sidereal_lon_by_id(mid, swe.MOON)
                d = (m - s) % FULL_CIRCLE_DEG
                if d > 180.0:
                    hi = mid
                else:
                    lo = mid
            nm_jd = (lo + hi) / 2.0
            # Avoid duplicates
            if start_jd <= nm_jd <= end_jd and (not new_moons or abs(nm_jd - new_moons[-1]) > 10):
                new_moons.append(nm_jd)
            jd = nm_jd + 20  # Skip ahead past this lunation
        else:
            jd += 1.0
    return new_moons


def find_full_moons(start_jd: float, end_jd: float) -> list[float]:
    """Find Julian Days of Full Moons (Sun-Moon opposition) in the period.

    Uses daily stepping with binary search refinement.

    Args:
        start_jd: Start Julian Day.
        end_jd: End Julian Day.

    Returns:
        List of Julian Days for each Full Moon.
    """
    full_moons: list[float] = []
    jd = start_jd
    while jd < end_jd:
        sun_lon = sidereal_lon_by_id(jd, swe.SUN)
        moon_lon = sidereal_lon_by_id(jd, swe.MOON)
        opp_diff = orb_between(sun_lon, (moon_lon + 180.0) % FULL_CIRCLE_DEG)

        if opp_diff < 15.0:
            # Binary search: Moon opposite Sun
            lo, hi = jd - 1.0, jd + 1.0
            for _ in range(20):
                mid = (lo + hi) / 2.0
                s = sidereal_lon_by_id(mid, swe.SUN)
                m = sidereal_lon_by_id(mid, swe.MOON)
                d = (m - s) % FULL_CIRCLE_DEG
                if d < 180.0:
                    lo = mid
                else:
                    hi = mid
            fm_jd = (lo + hi) / 2.0
            if start_jd <= fm_jd <= end_jd and (not full_moons or abs(fm_jd - full_moons[-1]) > 10):
                full_moons.append(fm_jd)
            jd = fm_jd + 20
        else:
            jd += 1.0
    return full_moons
