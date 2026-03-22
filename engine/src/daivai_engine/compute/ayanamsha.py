"""Multi-ayanamsha support — compute sidereal ayanamsha values for any major system.

Swiss Ephemeris supports 50+ ayanamsha systems via swe.set_sid_mode(). This module
exposes the six most critical systems for Vedic and Western sidereal astrology:

  - Lahiri         : Indian government standard (90% of Indian astrologers)
  - Krishnamurti   : KP system (critical precision for 249 sub-divisions)
  - Raman          : B.V. Raman tradition (~1°27' different from Lahiri)
  - True Chitrapaksha: Dynamically tracks Spica's actual ecliptic position
  - Yukteshwar     : Sri Yukteshwar Giri's system (The Holy Science, 1894)
  - Fagan-Bradley  : Western sidereal standard (Aldebaran at 15° Taurus)

All known values for verification:
  Lahiri at J2000.0     ≈ 23°51' (23.85°)
  KP at J2000.0         ≈ 23°45' (~6' less than Lahiri)
  Raman at J2000.0      ≈ 22°25' (~1°26' less than Lahiri)
  Fagan-Bradley J2000.0 ≈ 24°44' (~53' ahead of Lahiri)

Thread safety note: swe.set_sid_mode() is a global C-library call. This module
restores Lahiri mode after computing non-Lahiri values, but is not safe for
concurrent multi-threaded chart computation without an external lock.

Source: Swiss Ephemeris documentation; ayanamsha_reference.yaml
"""

from __future__ import annotations

import swisseph as swe

from daivai_engine.models.ayanamsha import AyanamshaInfo, AyanamshaType, AyanamshaValue


# ── Swiss Ephemeris sidereal mode integer codes ───────────────────────────────
# Using getattr with integer fallbacks ensures compatibility across pyswisseph
# versions. Integer values are stable SE constants (unchanged since SE 1.x).
_SIDM: dict[AyanamshaType, int] = {
    AyanamshaType.LAHIRI: swe.SIDM_LAHIRI,  # 1
    AyanamshaType.KRISHNAMURTI: getattr(swe, "SIDM_KRISHNAMURTI", 5),  # 5
    AyanamshaType.RAMAN: getattr(swe, "SIDM_RAMAN", 3),  # 3
    AyanamshaType.TRUE_CHITRAPAKSHA: getattr(swe, "SIDM_TRUE_CITRA", 27),  # 27
    AyanamshaType.YUKTESHWAR: getattr(swe, "SIDM_YUKTESHWAR", 7),  # 7
    AyanamshaType.FAGAN_BRADLEY: getattr(swe, "SIDM_FAGAN_BRADLEY", 0),  # 0
}

# ── Reference metadata for each system ───────────────────────────────────────
_INFO: dict[AyanamshaType, AyanamshaInfo] = {
    AyanamshaType.LAHIRI: AyanamshaInfo(
        type=AyanamshaType.LAHIRI,
        name="Lahiri Chitrapaksha Ayanamsha",
        description=(
            "Indian government standard since 1956, recommended by the Calendar Reform "
            "Committee. Used by ~90% of Indian astrologers. Defined by a fixed epoch of "
            "23°15'00.658\" on 21 March 1956 0:00 ET with the IAU 1976 precession model. "
            "Reference star Spica (Chitra) placed at 0° Libra (180° ecliptic)."
        ),
        founder="N.C. Lahiri",
        reference_epoch="21 March 1956 0:00 ET",
        reference_value_j2000=23.85,
        zero_year_ce=285,
        usage="~90% of Indian astrologers; Indian government standard (CSIR, 1955)",
        notes=(
            "Does NOT dynamically track Spica. Uses fixed epoch + precession formula. "
            "Drifts from Spica's actual ecliptic position by 30-60 arcseconds over decades."
        ),
    ),
    AyanamshaType.KRISHNAMURTI: AyanamshaInfo(
        type=AyanamshaType.KRISHNAMURTI,
        name="Krishnamurti Paddhati (KP) Ayanamsha",
        description=(
            "Developed by K.S. Krishnamurti for the KP system. Differs from Lahiri by "
            "~6 arcminutes — small but critical: 6' equals 15% of the smallest KP sub-lord "
            "span across 249 stellar divisions. Using Lahiri for KP calculations produces "
            "systematically wrong sub-lords."
        ),
        founder="K.S. Krishnamurti",
        reference_epoch="J2000.0",
        reference_value_j2000=23.75,
        zero_year_ce=291,
        usage="All KP (Krishnamurti Paddhati) system practitioners",
        notes=(
            "Must not be substituted with Lahiri for KP calculations. "
            "6 arcminutes = 360 arcseconds; smallest KP sub-lord span ≈ 2400 arcseconds."
        ),
    ),
    AyanamshaType.RAMAN: AyanamshaInfo(
        type=AyanamshaType.RAMAN,
        name="B.V. Raman Ayanamsha",
        description=(
            "Developed by Dr. B.V. Raman (1912-1998), editor of The Astrological Magazine. "
            "Uses a zero year of 397 CE versus Lahiri's 285 CE, producing a ~1°27' gap. "
            "This is large enough that ~1 in 30 charts will have at least one planet in a "
            "different sign compared to Lahiri. Nakshatra pada changes are very common."
        ),
        founder="Dr. B.V. Raman",
        reference_epoch="J2000.0",
        reference_value_j2000=22.41,
        zero_year_ce=397,
        usage="South Indian astrologers and followers of the B.V. Raman tradition",
        notes=(
            "~1.44° gap from Lahiri means significant sign and pada differences. "
            "Precession rate: 50.333 arcseconds/year."
        ),
    ),
    AyanamshaType.TRUE_CHITRAPAKSHA: AyanamshaInfo(
        type=AyanamshaType.TRUE_CHITRAPAKSHA,
        name="True Chitrapaksha Ayanamsha",
        description=(
            "Dynamically tracks Spica's (Alpha Virginis / Chitra) actual ecliptic longitude "
            "in real time. Astronomically precise and self-correcting, unlike Lahiri which "
            "uses a fixed epoch. Differs from Lahiri by only 30-60 arcseconds (varies). "
            "Spica's ecliptic latitude is -2.06 degrees, requiring projection onto the ecliptic."
        ),
        founder=None,
        reference_epoch="Dynamic - recomputed from Spica's actual position each time",
        reference_value_j2000=23.85,
        zero_year_ce=None,
        usage="Astronomically rigorous practitioners and researchers",
        notes=(
            "Spica is 2.06° south of the ecliptic. Rectangular projection used. "
            "Lahiri uses this star but with a fixed 1956 epoch value, not dynamic tracking."
        ),
    ),
    AyanamshaType.YUKTESHWAR: AyanamshaInfo(
        type=AyanamshaType.YUKTESHWAR,
        name="Sri Yukteshwar Ayanamsha",
        description=(
            "Based on Sri Yukteshwar Giri's 'The Holy Science' (1894). Uses a dual-cycle "
            "24,000-year precessional model centred on a companion star. Significantly "
            "different from Lahiri (~1.5-2 degree range). More common among Western Vedic "
            "astrologers influenced by Paramahansa Yogananda's lineage."
        ),
        founder="Sri Yukteshwar Giri",
        reference_epoch="J2000.0",
        reference_value_j2000=22.47,
        zero_year_ce=None,
        usage="Western Vedic astrologers following Yukteshwar's precessional model",
        notes=(
            "Based on The Holy Science (1894). Not widely used in India. "
            "Uses a non-standard dual-cycle precession model."
        ),
    ),
    AyanamshaType.FAGAN_BRADLEY: AyanamshaInfo(
        type=AyanamshaType.FAGAN_BRADLEY,
        name="Fagan-Bradley Ayanamsha",
        description=(
            "Western sidereal zodiac standard developed by Cyril Fagan and Donald Bradley "
            "in the 1950s. Places Aldebaran (Alpha Tauri) at exactly 15° Taurus and "
            "Antares at 15° Scorpio. Approximately 0.88° ahead of Lahiri at J2000.0. "
            "Not used in Vedic/Jyotish tradition; included for cross-system comparison."
        ),
        founder="Cyril Fagan and Donald Bradley",
        reference_epoch="J2000.0",
        reference_value_j2000=24.73,
        zero_year_ce=None,
        usage="Western sidereal astrologers (not Vedic/Jyotish)",
        notes=(
            "NOT part of Vedic tradition. Included for rectification and cross-system work. "
            "Delta from Lahiri: approximately +0.88° (Fagan-Bradley is ahead of Lahiri)."
        ),
    ),
}


def _degrees_to_dms(degrees: float) -> str:
    """Convert decimal degrees to a DMS string (DD°MM'SS.SS\").

    Args:
        degrees: Angle in decimal degrees (non-negative for ayanamsha values).

    Returns:
        Formatted string, e.g. '23°42\'22.21"' for 23.70617°.
    """
    total_seconds = abs(degrees) * 3600.0
    d = int(total_seconds // 3600)
    remaining = total_seconds - d * 3600
    m = int(remaining // 60)
    s = remaining - m * 60
    sign = "-" if degrees < 0 else ""
    return f"{sign}{d}\u00b0{m:02d}'{s:05.2f}\""


def compute_ayanamsha(
    jd: float,
    ayanamsha_type: AyanamshaType = AyanamshaType.LAHIRI,
) -> float:
    """Compute the ayanamsha value in decimal degrees for a given Julian Day.

    Calls Swiss Ephemeris swe.set_sid_mode() then swe.get_ayanamsa(). For
    non-Lahiri systems, Lahiri mode is restored on exit to preserve the engine
    default for subsequent chart computations.

    Args:
        jd: Julian Day number (TT/TDB scale, as returned by to_jd()).
        ayanamsha_type: Which ayanamsha system to use. Defaults to Lahiri.

    Returns:
        Ayanamsha in decimal degrees (geocentric, true nutation included).
        Typical modern-era range: 22 to 25 degrees.

    Raises:
        ValueError: If ayanamsha_type is not in the supported set.
    """
    if ayanamsha_type not in _SIDM:
        raise ValueError(
            f"Unsupported ayanamsha type: {ayanamsha_type!r}. Choose from: {list(AyanamshaType)}"
        )
    swe.set_sid_mode(_SIDM[ayanamsha_type])
    try:
        return float(swe.get_ayanamsa(jd))
    finally:
        # Restore Lahiri mode (engine default) after any non-Lahiri computation
        if ayanamsha_type != AyanamshaType.LAHIRI:
            swe.set_sid_mode(swe.SIDM_LAHIRI)


def compute_ayanamsha_value(
    jd: float,
    ayanamsha_type: AyanamshaType = AyanamshaType.LAHIRI,
    include_delta: bool = True,
) -> AyanamshaValue:
    """Compute ayanamsha and return a rich AyanamshaValue object.

    Args:
        jd: Julian Day number (TT/TDB scale).
        ayanamsha_type: Which ayanamsha system to use.
        include_delta: When True, compute and include the signed difference
            from Lahiri (positive = this system is ahead of Lahiri).

    Returns:
        AyanamshaValue containing decimal degrees, DMS string, and optional
        delta from Lahiri.
    """
    value = compute_ayanamsha(jd, ayanamsha_type)
    dms = _degrees_to_dms(value)

    if ayanamsha_type == AyanamshaType.LAHIRI:
        delta: float | None = 0.0
    elif include_delta:
        lahiri_value = compute_ayanamsha(jd, AyanamshaType.LAHIRI)
        delta = value - lahiri_value
    else:
        delta = None

    return AyanamshaValue(
        julian_day=jd,
        type=ayanamsha_type,
        value_degrees=value,
        value_dms=dms,
        delta_from_lahiri=delta,
    )


def get_ayanamsha_info(ayanamsha_type: AyanamshaType) -> AyanamshaInfo:
    """Return scholarly metadata for an ayanamsha system.

    Args:
        ayanamsha_type: Which ayanamsha system to describe.

    Returns:
        AyanamshaInfo with name, description, founder, reference epoch,
        approximate J2000.0 value, zero year, usage notes, and caveats.

    Raises:
        KeyError: If ayanamsha_type has no registered metadata (should never
            happen for enum members — all six types have entries).
    """
    return _INFO[ayanamsha_type]


def compute_all_ayanamshas(jd: float) -> dict[AyanamshaType, AyanamshaValue]:
    """Compute all six supported ayanamshas for a given Julian Day.

    Useful for cross-system comparison, chart rectification research, and
    identifying planets near sign/nakshatra boundaries that are sensitive
    to ayanamsha choice.

    Args:
        jd: Julian Day number (TT/TDB scale).

    Returns:
        Dict mapping every AyanamshaType to its computed AyanamshaValue,
        with delta_from_lahiri populated for all entries.
    """
    return {t: compute_ayanamsha_value(jd, t, include_delta=True) for t in AyanamshaType}
