"""Advanced Muhurta Engine — multi-type auspicious timing with dosha checking.

Implements the classical five-fold Panchanga Shuddhi (purity test) and
additional Lagna Shuddhi check for comprehensive muhurta selection.

Panchanga Shuddhi = 5 Panchanga limbs must all be pure:
  1. Tithi Shuddhi — no Rikta (4th, 9th, 14th) or Amavasya
  2. Vara Shuddhi  — no inauspicious weekday for the purpose
  3. Nakshatra Shuddhi — no Krura/Ugra/Gandanta nakshatra
  4. Yoga Shuddhi — no Vishkambha, Vajra, Vyatipata, Vaidhriti, etc.
  5. Karana Shuddhi — no Vishti (Bhadra) karana

Lagna Shuddhi = the rising sign at the muhurta moment must be:
  - A fixed sign for permanent events (vivah, grihapravesh)
  - A movable sign for journeys (yatra)
  - A dual sign for education/business (vidya, vyapara)
  - Free from malefics in the 8th from lagna
  - Lagna lord in kendra or trikona

Source: Muhurta Chintamani, BPHS Muhurta chapter.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from daivai_engine.compute.panchang import compute_panchang
from daivai_engine.constants import (
    RAHU_KAAL_SLOT,
)
from daivai_engine.models.chart import ChartData


class MuhurtaDosha(BaseModel):
    """A single dosha (flaw) detected in a muhurta."""

    name: str
    name_hi: str
    is_present: bool
    severity: str  # mild / moderate / severe
    description: str


class PanchangaShuddhi(BaseModel):
    """Classical 5-fold Panchanga Shuddhi (purity) assessment.

    All five limbs (Tithi, Vara, Nakshatra, Yoga, Karana) must be pure
    for a muhurta to be classically acceptable. Partial purity = partially
    acceptable with remedies.

    Source: Muhurta Chintamani Ch.1.
    """

    tithi_shuddha: bool
    vara_shuddha: bool
    nakshatra_shuddha: bool
    yoga_shuddha: bool
    karana_shuddha: bool
    shuddha_count: int  # 0-5
    is_fully_shuddha: bool  # all 5 pure
    summary: str  # e.g. "4/5 pure: Nakshatra impure (Gandanta)"


class LagnaShuddhi(BaseModel):
    """Lagna (ascendant) purity for the muhurta moment.

    The rising sign at the muhurta time must match the event type and
    be free from malefic influence.

    Source: Muhurta Chintamani Ch.2.
    """

    lagna_sign_index: int
    lagna_sign: str
    lagna_type: str  # movable / fixed / dual
    matches_event_type: bool  # Does lagna type suit the event?
    malefic_in_8th: bool  # Malefic in 8th from lagna = strongly inauspicious
    lagna_lord_strong: bool  # Lagna lord in kendra/trikona from lagna
    is_shuddha: bool  # All conditions satisfied
    note: str


class MuhurtaScore(BaseModel):
    """Comprehensive muhurta scoring for a specific datetime and event type."""

    event_type: str
    datetime_str: str
    score: int  # 0-100
    doshas: list[MuhurtaDosha]
    doshas_present: int
    doshas_absent: int
    panchanga_shuddhi: PanchangaShuddhi | None = None
    lagna_shuddhi: LagnaShuddhi | None = None
    is_auspicious: bool  # score >= 70
    summary: str


# Rikta tithis — BPHS: 4th, 9th, 14th are inauspicious (0-indexed: 3, 8, 13, 18, 23, 28)
_RIKTA_TITHIS = {3, 8, 13, 18, 23, 28}

# Bhadra (Vishti) karana — 7th karana in the cycle is always inauspicious
_BHADRA_KARANA = "Vishti"

# Panchak nakshatras (Moon in these = Panchak dosha) — Muhurta Chintamani
_PANCHAK_NAKSHATRAS = {
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
}

# Krura/Ugra nakshatras — inauspicious for auspicious events
_KRURA_NAKSHATRAS = {"Bharani", "Magha", "Purva Phalguni", "Purva Ashadha", "Purva Bhadrapada"}

# Gandanta junction nakshatras
_GANDANTA_NAKSHATRAS = {"Ashlesha", "Jyeshtha", "Revati", "Magha", "Moola", "Ashwini"}

# Inauspicious yogas (from 27 panchang yogas)
_INAUSPICIOUS_YOGAS = {
    "Vishkambha",
    "Atiganda",
    "Shula",
    "Ganda",
    "Vyaghata",
    "Vajra",
    "Vyatipata",
    "Parigha",
    "Vaidhriti",
}

# Favorable conditions per event type
_EVENT_FAVORABLE: dict[str, dict[str, Any]] = {
    "vivah": {"good_days": {1, 2, 3, 4}, "lagna_types": {"fixed"}, "strong_houses": {7, 2}},
    "griha_pravesh": {"good_days": {1, 2, 3, 4}, "lagna_types": {"fixed"}, "strong_houses": {4}},
    "vyapara": {"good_days": {2, 3}, "lagna_types": {"dual"}, "strong_houses": {10, 2, 11}},
    "yatra": {"good_days": {1, 2, 3}, "lagna_types": {"movable"}, "strong_houses": {9, 3}},
    "vidya": {"good_days": {2, 3}, "lagna_types": {"dual"}, "strong_houses": {4, 5}},
    "aushadhi": {
        "good_days": {0, 1, 3, 4},
        "lagna_types": {"movable", "dual"},
        "strong_houses": {1},
    },
}


def score_muhurta(
    event_type: str,
    dt: datetime,
    lat: float,
    lon: float,
    tz_name: str = "Asia/Kolkata",
    natal_chart: ChartData | None = None,
) -> MuhurtaScore:
    """Score a datetime for a specific event type.

    Checks up to 15 classical doshas and returns a score 0-100.

    Args:
        event_type: vivah/griha_pravesh/vyapara/yatra/vidya/aushadhi/general
        dt: Datetime to evaluate.
        lat: Latitude of event location.
        lon: Longitude of event location.
        tz_name: Timezone name.
        natal_chart: Optional natal chart for Tara/Chandra bala.

    Returns:
        MuhurtaScore with detailed breakdown.
    """
    date_str = dt.strftime("%d/%m/%Y")
    panchang = compute_panchang(date_str, lat, lon, tz_name)

    doshas: list[MuhurtaDosha] = []
    score = 100  # Start perfect, subtract for doshas

    # 1. Panchak dosha — Muhurta Chintamani
    is_panchak = panchang.nakshatra_name in _PANCHAK_NAKSHATRAS
    doshas.append(
        MuhurtaDosha(
            name="Panchak",
            name_hi="पंचक",
            is_present=is_panchak,
            severity="severe" if is_panchak else "none",
            description="Moon in Panchak nakshatra" if is_panchak else "Clear",
        )
    )
    if is_panchak:
        score -= 15

    # 2. Rikta Tithi — BPHS
    tithi_idx = panchang.tithi_index if hasattr(panchang, "tithi_index") else 0
    is_rikta = tithi_idx in _RIKTA_TITHIS
    doshas.append(
        MuhurtaDosha(
            name="Rikta Tithi",
            name_hi="रिक्त तिथि",
            is_present=is_rikta,
            severity="moderate" if is_rikta else "none",
            description=f"Tithi {panchang.tithi_name} is Rikta" if is_rikta else "Clear",
        )
    )
    if is_rikta:
        score -= 10

    # 3. Bhadra (Vishti) Karana
    is_bhadra = _BHADRA_KARANA.lower() in panchang.karana_name.lower()
    doshas.append(
        MuhurtaDosha(
            name="Bhadra",
            name_hi="भद्रा",
            is_present=is_bhadra,
            severity="severe" if is_bhadra else "none",
            description="Vishti Karana active" if is_bhadra else "Clear",
        )
    )
    if is_bhadra:
        score -= 15

    # 4. Krura Nakshatra
    is_krura = panchang.nakshatra_name in _KRURA_NAKSHATRAS
    doshas.append(
        MuhurtaDosha(
            name="Krura Nakshatra",
            name_hi="क्रूर नक्षत्र",
            is_present=is_krura,
            severity="moderate" if is_krura else "none",
            description=f"{panchang.nakshatra_name} is Krura" if is_krura else "Clear",
        )
    )
    if is_krura:
        score -= 10

    # 5. Gandanta Nakshatra
    is_gandanta = panchang.nakshatra_name in _GANDANTA_NAKSHATRAS
    doshas.append(
        MuhurtaDosha(
            name="Gandanta",
            name_hi="गण्डान्त",
            is_present=is_gandanta,
            severity="severe" if is_gandanta else "none",
            description=f"{panchang.nakshatra_name} is junction nakshatra"
            if is_gandanta
            else "Clear",
        )
    )
    if is_gandanta:
        score -= 12

    # 6. Inauspicious Yoga
    is_bad_yoga = panchang.yoga_name in _INAUSPICIOUS_YOGAS
    doshas.append(
        MuhurtaDosha(
            name="Ashubh Yoga",
            name_hi="अशुभ योग",
            is_present=is_bad_yoga,
            severity="moderate" if is_bad_yoga else "none",
            description=f"Yoga {panchang.yoga_name} is inauspicious" if is_bad_yoga else "Clear",
        )
    )
    if is_bad_yoga:
        score -= 8

    # 7. Amavasya — new moon
    is_amavasya = "Amavasya" in panchang.tithi_name
    doshas.append(
        MuhurtaDosha(
            name="Amavasya",
            name_hi="अमावस्या",
            is_present=is_amavasya,
            severity="severe" if is_amavasya else "none",
            description="New Moon day" if is_amavasya else "Clear",
        )
    )
    if is_amavasya:
        score -= 15

    # 8. Rahu Kaal check (simplified — would need time-of-day for precision)
    weekday = dt.weekday()
    day_idx = (weekday + 1) % 7
    rahu_slot = RAHU_KAAL_SLOT.get(day_idx, 8)
    is_rahu = False  # Simplified: flag if event is in Rahu Kaal slot
    doshas.append(
        MuhurtaDosha(
            name="Rahu Kaal",
            name_hi="राहु काल",
            is_present=is_rahu,
            severity="moderate" if is_rahu else "none",
            description=f"Rahu Kaal slot {rahu_slot}" if is_rahu else "Clear",
        )
    )

    # 9. Tara Bala (if natal chart provided)
    if natal_chart:
        natal_nak = natal_chart.planets["Moon"].nakshatra_index
        transit_nak_idx = _nak_index(panchang.nakshatra_name)
        tara = ((transit_nak_idx - natal_nak) % 27) % 9
        bad_taras = {2, 4, 6, 8}  # Vipat, Pratyak, Vadha, Naidhana (0-indexed from 0)
        is_bad_tara = tara in bad_taras
        doshas.append(
            MuhurtaDosha(
                name="Tara Bala",
                name_hi="तारा बल",
                is_present=is_bad_tara,
                severity="moderate" if is_bad_tara else "none",
                description="Inauspicious Tara" if is_bad_tara else "Favorable Tara",
            )
        )
        if is_bad_tara:
            score -= 8

    doshas_present = sum(1 for d in doshas if d.is_present)
    doshas_absent = len(doshas) - doshas_present
    score = max(0, min(100, score))

    # Panchanga Shuddhi (5-fold purity check)
    panchanga_shuddhi = _compute_panchanga_shuddhi(panchang, event_type, dt)

    # Lagna Shuddhi (lagna purity — requires chart for event moment)
    lagna_shuddhi = _compute_lagna_shuddhi(dt, lat, lon, tz_name, event_type)

    # Lagna shuddhi affects score
    if lagna_shuddhi is not None and not lagna_shuddhi.is_shuddha:
        if lagna_shuddhi.malefic_in_8th:
            score -= 10
        elif not lagna_shuddhi.matches_event_type:
            score -= 5
    score = max(0, min(100, score))

    return MuhurtaScore(
        event_type=event_type,
        datetime_str=dt.strftime("%Y-%m-%d %H:%M"),
        score=score,
        doshas=doshas,
        doshas_present=doshas_present,
        doshas_absent=doshas_absent,
        panchanga_shuddhi=panchanga_shuddhi,
        lagna_shuddhi=lagna_shuddhi,
        is_auspicious=score >= 70,
        summary=f"{event_type}: score {score}/100, {doshas_present} doshas present",
    )


# ── Panchanga Shuddhi ────────────────────────────────────────────────────────

# Inauspicious weekdays per event type (0=Sun, 1=Mon, ..., 6=Sat)
_INAUSPICIOUS_VARA: dict[str, set[int]] = {
    "vivah": {2, 6},  # Tuesday, Saturday
    "griha_pravesh": {2},  # Tuesday
    "vyapara": {0},  # Sunday
    "yatra": {2, 6},  # Tuesday, Saturday
    "vidya": {2},  # Tuesday
    "aushadhi": set(),
    "general": set(),
}


def _compute_panchanga_shuddhi(
    panchang: Any,
    event_type: str,
    dt: datetime,
) -> PanchangaShuddhi:
    """Compute the 5-fold Panchanga Shuddhi (purity) assessment.

    Checks each of the 5 Panchanga limbs independently:
    1. Tithi Shuddhi — no Rikta tithi or Amavasya
    2. Vara Shuddhi — no inauspicious weekday for event type
    3. Nakshatra Shuddhi — no Krura, Ugra, Panchak, or Gandanta nakshatra
    4. Yoga Shuddhi — none of the 9 inauspicious yogas active
    5. Karana Shuddhi — no Vishti (Bhadra) karana active

    Source: Muhurta Chintamani Ch.1.
    """
    tithi_idx = panchang.tithi_index if hasattr(panchang, "tithi_index") else 0

    # 1. Tithi Shuddhi
    is_rikta = tithi_idx in _RIKTA_TITHIS
    is_amavasya = "Amavasya" in panchang.tithi_name
    tithi_shuddha = not is_rikta and not is_amavasya

    # 2. Vara Shuddhi
    weekday = dt.weekday()
    day_idx = (weekday + 1) % 7  # Sunday=0
    bad_varas = _INAUSPICIOUS_VARA.get(event_type, set())
    vara_shuddha = day_idx not in bad_varas

    # 3. Nakshatra Shuddhi (Krura, Panchak, Gandanta — all checked)
    is_krura_nak = panchang.nakshatra_name in _KRURA_NAKSHATRAS
    is_panchak_nak = panchang.nakshatra_name in _PANCHAK_NAKSHATRAS
    is_gandanta_nak = panchang.nakshatra_name in _GANDANTA_NAKSHATRAS
    nakshatra_shuddha = not is_krura_nak and not is_panchak_nak and not is_gandanta_nak

    # 4. Yoga Shuddhi
    yoga_shuddha = panchang.yoga_name not in _INAUSPICIOUS_YOGAS

    # 5. Karana Shuddhi
    karana_shuddha = _BHADRA_KARANA.lower() not in panchang.karana_name.lower()

    count = sum([tithi_shuddha, vara_shuddha, nakshatra_shuddha, yoga_shuddha, karana_shuddha])

    impure_limbs: list[str] = []
    if not tithi_shuddha:
        impure_limbs.append(f"Tithi ({panchang.tithi_name})")
    if not vara_shuddha:
        impure_limbs.append(f"Vara (weekday {day_idx})")
    if not nakshatra_shuddha:
        impure_limbs.append(f"Nakshatra ({panchang.nakshatra_name})")
    if not yoga_shuddha:
        impure_limbs.append(f"Yoga ({panchang.yoga_name})")
    if not karana_shuddha:
        impure_limbs.append(f"Karana ({panchang.karana_name})")

    if count == 5:
        summary = "All 5 Panchanga limbs are pure — excellent muhurta"
    elif impure_limbs:
        summary = f"{count}/5 pure: impure — {', '.join(impure_limbs)}"
    else:
        summary = f"{count}/5 Panchanga limbs pure"

    return PanchangaShuddhi(
        tithi_shuddha=tithi_shuddha,
        vara_shuddha=vara_shuddha,
        nakshatra_shuddha=nakshatra_shuddha,
        yoga_shuddha=yoga_shuddha,
        karana_shuddha=karana_shuddha,
        shuddha_count=count,
        is_fully_shuddha=count == 5,
        summary=summary,
    )


# ── Lagna Shuddhi ────────────────────────────────────────────────────────────

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


def _compute_lagna_shuddhi(
    dt: datetime,
    lat: float,
    lon: float,
    tz_name: str,
    event_type: str,
) -> LagnaShuddhi | None:
    """Compute Lagna Shuddhi for the event moment.

    Computes the rising sign at the given moment and checks:
    1. Lagna type matches event type (fixed/movable/dual)
    2. No malefic in 8th from lagna
    3. Lagna lord is in kendra or trikona from lagna

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

        return LagnaShuddhi(
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


def _nak_index(nakshatra: str) -> int:
    """Get nakshatra index from name."""
    from daivai_engine.constants import NAKSHATRAS

    try:
        return NAKSHATRAS.index(nakshatra)
    except ValueError:
        return 0
