"""Muhurta Panchanga Shuddhi (5-fold purity) computation.

Implements Tithi, Vara, Nakshatra, Yoga, and Karana purity checks
for classical muhurta selection.

Source: Muhurta Chintamani Ch.1.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    pass


# Favorable conditions per event type (for reference by callers)
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


# Rikta tithis — BPHS: 4th, 9th, 14th are inauspicious
_RIKTA_TITHIS: set[int] = {3, 8, 13, 18, 23, 28}

# Bhadra (Vishti) karana
_BHADRA_KARANA = "Vishti"

# Panchak nakshatras — Muhurta Chintamani
_PANCHAK_NAKSHATRAS: set[str] = {
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
}

# Krura/Ugra nakshatras
_KRURA_NAKSHATRAS: set[str] = {
    "Bharani",
    "Magha",
    "Purva Phalguni",
    "Purva Ashadha",
    "Purva Bhadrapada",
}

# Gandanta junction nakshatras
_GANDANTA_NAKSHATRAS: set[str] = {
    "Ashlesha",
    "Jyeshtha",
    "Revati",
    "Magha",
    "Moola",
    "Ashwini",
}

# Inauspicious yogas (from 27 panchang yogas)
_INAUSPICIOUS_YOGAS: set[str] = {
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


def compute_panchanga_shuddhi(
    panchang: Any,
    event_type: str,
    dt: datetime,
    panchanga_shuddhi_class: type,
) -> Any:
    """Compute the 5-fold Panchanga Shuddhi (purity) assessment.

    Checks each of the 5 Panchanga limbs independently:
    1. Tithi Shuddhi — no Rikta tithi or Amavasya
    2. Vara Shuddhi — no inauspicious weekday for event type
    3. Nakshatra Shuddhi — no Krura, Ugra, Panchak, or Gandanta nakshatra
    4. Yoga Shuddhi — none of the 9 inauspicious yogas active
    5. Karana Shuddhi — no Vishti (Bhadra) karana active

    Args:
        panchang: Computed panchang data for the datetime.
        event_type: Event type (vivah/griha_pravesh/etc.)
        dt: The datetime being evaluated.
        panchanga_shuddhi_class: PanchangaShuddhi class (passed to avoid circular import).

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

    return panchanga_shuddhi_class(
        tithi_shuddha=tithi_shuddha,
        vara_shuddha=vara_shuddha,
        nakshatra_shuddha=nakshatra_shuddha,
        yoga_shuddha=yoga_shuddha,
        karana_shuddha=karana_shuddha,
        shuddha_count=count,
        is_fully_shuddha=count == 5,
        summary=summary,
    )
