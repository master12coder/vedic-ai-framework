"""Dasha-related Vedic astrology constants."""

from __future__ import annotations


# ── Dashas ───────────────────────────────────────────────────────────────────

DASHA_SEQUENCE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

DASHA_YEARS: dict[str, int] = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17,
}

DASHA_TOTAL_YEARS = 120

# Dasha sub-systems
YOGINI_TOTAL_YEARS = 36  # Sum of 1+2+3+4+5+6+7+8
ASHTOTTARI_TOTAL_YEARS = 108  # Sum of Ashtottari dasha periods

# ── Rasi (sign-based) Dasha systems ─────────────────────────────────────────

# Sthira Dasha: fixed years by sign type (BPHS Ch.47)
# Chara (movable) = 7 yrs, Sthira (fixed) = 8 yrs, Dwiswabhava (dual) = 9 yrs
STHIRA_DASHA_YEARS: dict[int, int] = {
    0: 7,  # Mesha — chara
    1: 8,  # Vrishabha — sthira
    2: 9,  # Mithuna — dwiswabhava
    3: 7,  # Karka — chara
    4: 8,  # Simha — sthira
    5: 9,  # Kanya — dwiswabhava
    6: 7,  # Tula — chara
    7: 8,  # Vrischika — sthira
    8: 9,  # Dhanu — dwiswabhava
    9: 7,  # Makara — chara
    10: 8,  # Kumbha — sthira
    11: 9,  # Meena — dwiswabhava
}
STHIRA_TOTAL_YEARS = 96  # 4x7 + 4x8 + 4x9

# Shoola Dasha: odd signs = 7 yrs, even signs = 8 yrs (BPHS Ch.48)
SHOOLA_DASHA_YEARS: dict[int, int] = {
    0: 7,  # Mesha — odd
    1: 8,  # Vrishabha — even
    2: 7,  # Mithuna — odd
    3: 8,  # Karka — even
    4: 7,  # Simha — odd
    5: 8,  # Kanya — even
    6: 7,  # Tula — odd
    7: 8,  # Vrischika — even
    8: 7,  # Dhanu — odd
    9: 8,  # Makara — even
    10: 7,  # Kumbha — odd
    11: 8,  # Meena — even
}
SHOOLA_TOTAL_YEARS = 90  # 6x7 + 6x8

# Mandooka Dasha: frog-jump, each sign = 7 yrs, total = 84 yrs (BPHS Ch.49)
MANDOOKA_SIGN_YEARS = 7
MANDOOKA_TOTAL_YEARS = 84  # 12 x 7

# ── Conditional Nakshatra-based Dasha systems ────────────────────────────────

# Dwisaptati Sama Dasha (72 years) — BPHS Ch.50
# Condition: Lagna lord in 7th house
DWISAPTATI_SEQUENCE: list[tuple[str, int]] = [
    ("Sun", 9),
    ("Moon", 9),
    ("Mars", 9),
    ("Mercury", 9),
    ("Jupiter", 9),
    ("Venus", 9),
    ("Saturn", 9),
    ("Rahu", 9),
]
DWISAPTATI_TOTAL_YEARS = 72

# Shatabdika Dasha (100 years) — BPHS Ch.51
# Condition: Lagna lord in lagna (own house)
SHATABDIKA_SEQUENCE: list[tuple[str, int]] = [
    ("Sun", 20),
    ("Moon", 20),
    ("Jupiter", 20),
    ("Mars", 20),
    ("Saturn", 20),
]
SHATABDIKA_TOTAL_YEARS = 100

# Chaturaseeti Sama Dasha (84 years) — BPHS Ch.52
# Condition: Lagna lord in 10th house
CHATURASEETI_SEQUENCE: list[tuple[str, int]] = [
    ("Sun", 12),
    ("Moon", 12),
    ("Mars", 12),
    ("Mercury", 12),
    ("Jupiter", 12),
    ("Venus", 12),
    ("Saturn", 12),
]
CHATURASEETI_TOTAL_YEARS = 84

# Dwadashottari Dasha (112 years) — BPHS Ch.53
# Condition: Venus in lagna
DWADASHOTTARI_SEQUENCE: list[tuple[str, int]] = [
    ("Sun", 7),
    ("Moon", 14),
    ("Mars", 8),
    ("Mercury", 17),
    ("Jupiter", 10),
    ("Venus", 25),
    ("Saturn", 10),
    ("Rahu", 21),
]
DWADASHOTTARI_TOTAL_YEARS = 112

# Panchottari Dasha (105 years) — BPHS Ch.54
# Condition: Cancer lagna with Moon in lagna
PANCHOTTARI_SEQUENCE: list[tuple[str, int]] = [
    ("Sun", 12),
    ("Moon", 21),
    ("Mars", 16),
    ("Mercury", 42),
    ("Saturn", 14),
]
PANCHOTTARI_TOTAL_YEARS = 105

# Shashtihayani Dasha (60 years) — BPHS Ch.55
# Condition: Sun in lagna
SHASHTIHAYANI_SEQUENCE: list[tuple[str, int]] = [
    ("Sun", 30),
    ("Moon", 30),
]
SHASHTIHAYANI_TOTAL_YEARS = 60

# Shatrimsha Sama Dasha (36 years) — BPHS Ch.56
# Condition: Mars in lagna
SHATRIMSHA_SEQUENCE: list[tuple[str, int]] = [
    ("Sun", 6),
    ("Moon", 6),
    ("Venus", 6),
    ("Mercury", 6),
    ("Saturn", 6),
    ("Jupiter", 6),
]
SHATRIMSHA_TOTAL_YEARS = 36
