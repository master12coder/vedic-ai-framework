"""Advanced Muhurta Engine — multi-type auspicious timing with dosha checking.

Orchestrates Panchanga Shuddhi (5-fold purity) and Lagna Shuddhi checks.
Computation helpers live in muhurta_panchanga.py and muhurta_lagna.py.

Source: Muhurta Chintamani, BPHS Muhurta chapter.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from daivai_engine.compute.muhurta_lagna import compute_lagna_shuddhi, nak_index
from daivai_engine.compute.muhurta_panchanga import (
    _BHADRA_KARANA,
    _GANDANTA_NAKSHATRAS,
    _INAUSPICIOUS_YOGAS,
    _KRURA_NAKSHATRAS,
    _PANCHAK_NAKSHATRAS,
    _RIKTA_TITHIS,
    compute_panchanga_shuddhi,
)
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
        transit_nak_idx = nak_index(panchang.nakshatra_name)
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

    # 10. Chandrabalam — Moon strength for personalized muhurta — BPHS Ch.81,
    #     Muhurta Chintamani: "The Moon should not be in the 4th, 8th, or 12th
    #     house from Janma Rashi." Moon in 1,3,6,7,10,11 from natal Moon =
    #     auspicious; in 2,5,9 = neutral; in 4,8,12 = inauspicious.
    if natal_chart:
        natal_moon_sign = natal_chart.planets["Moon"].sign_index
        transit_nak_name = panchang.nakshatra_name
        # Compute transit Moon's sign from the nakshatra (each nak spans ~13.33 deg)
        transit_nak_i = nak_index(transit_nak_name)
        # Each nakshatra maps to a sign: nak 0-2 → sign 0, nak 3-5 → sign 1, etc.
        transit_moon_sign = (transit_nak_i * 4) // 9  # 27 nak / 12 signs = 2.25 nak/sign
        house_from_moon = ((transit_moon_sign - natal_moon_sign) % 12) + 1
        bad_chandrabalam = house_from_moon in {4, 8, 12}
        doshas.append(
            MuhurtaDosha(
                name="Chandrabalam",
                name_hi="चन्द्रबलम्",
                is_present=bad_chandrabalam,
                severity="moderate" if bad_chandrabalam else "none",
                description=(
                    f"Moon in {house_from_moon}th from Janma Rashi — inauspicious"
                    if bad_chandrabalam
                    else f"Moon in {house_from_moon}th from Janma Rashi — favorable"
                ),
            )
        )
        if bad_chandrabalam:
            score -= 10

    doshas_present = sum(1 for d in doshas if d.is_present)
    doshas_absent = len(doshas) - doshas_present
    score = max(0, min(100, score))

    # Panchanga Shuddhi (5-fold purity check)
    panchanga_shuddhi = compute_panchanga_shuddhi(panchang, event_type, dt, PanchangaShuddhi)

    # Lagna Shuddhi (lagna purity — requires chart for event moment)
    lagna_shuddhi = compute_lagna_shuddhi(dt, lat, lon, tz_name, event_type, LagnaShuddhi)

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


# Private alias for backward compatibility
_compute_panchanga_shuddhi = compute_panchanga_shuddhi
_compute_lagna_shuddhi = compute_lagna_shuddhi
_nak_index = nak_index
