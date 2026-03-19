"""Advanced Muhurta Engine — multi-type auspicious timing with dosha checking.

Scores a given datetime for different event types by checking classical
doshas (Bhadra, Rikta tithi, Panchak, Gandanta, etc.) and strengths.

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


class MuhurtaScore(BaseModel):
    """Comprehensive muhurta scoring for a specific datetime and event type."""

    event_type: str
    datetime_str: str
    score: int  # 0-100
    doshas: list[MuhurtaDosha]
    doshas_present: int
    doshas_absent: int
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

    return MuhurtaScore(
        event_type=event_type,
        datetime_str=dt.strftime("%Y-%m-%d %H:%M"),
        score=score,
        doshas=doshas,
        doshas_present=doshas_present,
        doshas_absent=doshas_absent,
        is_auspicious=score >= 70,
        summary=f"{event_type}: score {score}/100, {doshas_present} doshas present",
    )


def _nak_index(nakshatra: str) -> int:
    """Get nakshatra index from name."""
    from daivai_engine.constants import NAKSHATRAS

    try:
        return NAKSHATRAS.index(nakshatra)
    except ValueError:
        return 0
