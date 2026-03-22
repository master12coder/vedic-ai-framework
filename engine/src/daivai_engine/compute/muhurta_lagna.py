"""Muhurta Lagna Shuddhi (ascendant purity) computation.

Computes the rising sign at the muhurta moment and checks:
  - Lagna type matches event type (fixed/movable/dual)
  - No malefic in 8th from lagna
  - Lagna lord is in kendra or trikona from lagna

Source: Muhurta Chintamani Ch.2.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    pass


# Lagna type required per event type
_EVENT_LAGNA_TYPE: dict[str, str | None] = {
    "vivah": "fixed",  # Fixed lagna for permanent bond
    "griha_pravesh": "fixed",  # Fixed lagna for stable home
    "vyapara": "dual",  # Dual lagna for business (communicative)
    "yatra": "movable",  # Movable lagna for journeys
    "vidya": "dual",  # Dual lagna for education
    "aushadhi": "movable",  # Movable for medicine intake
    "general": None,  # No specific requirement
}

# Sign modalities (0-indexed)
_MOVABLE_SIGNS: frozenset[int] = frozenset({0, 3, 6, 9})  # Aries, Cancer, Libra, Capricorn
_FIXED_SIGNS: frozenset[int] = frozenset({1, 4, 7, 10})  # Taurus, Leo, Scorpio, Aquarius
_DUAL_SIGNS: frozenset[int] = frozenset({2, 5, 8, 11})  # Gemini, Virgo, Sagittarius, Pisces

_MALEFICS: frozenset[str] = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
_KENDRAS_SET: frozenset[int] = frozenset({1, 4, 7, 10})
_TRIKONAS_SET: frozenset[int] = frozenset({1, 5, 9})

_SIGN_NAMES: list[str] = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


def compute_lagna_shuddhi(
    dt: datetime,
    lat: float,
    lon: float,
    tz_name: str,
    event_type: str,
    lagna_shuddhi_class: type,
) -> Any | None:
    """Compute Lagna Shuddhi for the event moment.

    Computes the rising sign at the given moment and checks:
    1. Lagna type matches event type (fixed/movable/dual)
    2. No malefic in 8th from lagna
    3. Lagna lord is in kendra or trikona from lagna

    Args:
        dt: The datetime to evaluate.
        lat: Latitude of event location.
        lon: Longitude of event location.
        tz_name: Timezone name (unused, ephemeris uses JD).
        event_type: Event type (vivah/yatra/etc.)
        lagna_shuddhi_class: LagnaShuddhi class (passed to avoid circular import).

    Source: Muhurta Chintamani Ch.2.
    """
    try:
        import swisseph as swe

        from daivai_engine.constants import SIGN_LORDS

        # Get Julian Day for this datetime
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        # Get lagna (ascendant) using Swiss Ephemeris
        flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
        _cusps, ascs = swe.houses_ex(jd, lat, lon, b"P", flags)  # type: ignore[arg-type]
        lagna_lon: float = ascs[0]  # type: ignore[index]
        lagna_sign = int(lagna_lon / 30.0) % 12

        # Get all planet positions at this moment
        planet_swe_ids = {
            "Sun": swe.SUN,
            "Moon": swe.MOON,
            "Mars": swe.MARS,
            "Saturn": swe.SATURN,
            "Rahu": swe.MEAN_NODE,
            "Ketu": swe.MEAN_NODE,
        }
        planet_signs: dict[str, int] = {}
        for pname, swe_id in planet_swe_ids.items():
            res = swe.calc_ut(jd, swe_id, flags)
            plon: float = res[0][0]  # type: ignore[index]
            planet_signs[pname] = int(plon / 30.0) % 12

        # Ketu = opposite node
        if "Rahu" in planet_signs:
            planet_signs["Ketu"] = (planet_signs["Rahu"] + 6) % 12

        # Determine lagna type
        if lagna_sign in _MOVABLE_SIGNS:
            lagna_type = "movable"
        elif lagna_sign in _FIXED_SIGNS:
            lagna_type = "fixed"
        else:
            lagna_type = "dual"

        # Check if lagna type matches event requirement
        required_type = _EVENT_LAGNA_TYPE.get(event_type)
        matches = required_type is None or lagna_type == required_type

        # Check for malefic in 8th from lagna
        eighth_sign = (lagna_sign + 7) % 12
        malefic_in_8th = any(planet_signs.get(m) == eighth_sign for m in _MALEFICS)

        # Check lagna lord strength
        lagna_lord = SIGN_LORDS[lagna_sign]
        lagna_lord_planet_swe = {
            "Sun": swe.SUN,
            "Moon": swe.MOON,
            "Mars": swe.MARS,
            "Mercury": swe.MERCURY,
            "Jupiter": swe.JUPITER,
            "Venus": swe.VENUS,
            "Saturn": swe.SATURN,
        }
        ll_swe_id = lagna_lord_planet_swe.get(lagna_lord)
        lagna_lord_strong = False
        if ll_swe_id:
            ll_res = swe.calc_ut(jd, ll_swe_id, flags)
            ll_lon: float = ll_res[0][0]  # type: ignore[index]
            ll_sign = int(ll_lon / 30.0) % 12
            ll_house_from_lagna = ((ll_sign - lagna_sign) % 12) + 1
            lagna_lord_strong = ll_house_from_lagna in _KENDRAS_SET | _TRIKONAS_SET

        is_shuddha = matches and not malefic_in_8th and lagna_lord_strong

        notes: list[str] = []
        if not matches:
            notes.append(f"Lagna is {lagna_type} but {event_type} requires {required_type}")
        if malefic_in_8th:
            notes.append("Malefic in 8th from lagna (strongly inauspicious)")
        if not lagna_lord_strong:
            notes.append(f"Lagna lord {lagna_lord} is not in kendra/trikona")

        return lagna_shuddhi_class(
            lagna_sign_index=lagna_sign,
            lagna_sign=_SIGN_NAMES[lagna_sign],
            lagna_type=lagna_type,
            matches_event_type=matches,
            malefic_in_8th=malefic_in_8th,
            lagna_lord_strong=lagna_lord_strong,
            is_shuddha=is_shuddha,
            note=" | ".join(notes) if notes else "Lagna is pure for this event",
        )
    except Exception:
        return None


def nak_index(nakshatra: str) -> int:
    """Get nakshatra index from name."""
    from daivai_engine.constants import NAKSHATRAS

    try:
        return NAKSHATRAS.index(nakshatra)
    except ValueError:
        return 0
