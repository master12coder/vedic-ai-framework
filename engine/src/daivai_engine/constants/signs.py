"""Sign-related Vedic astrology constants."""

from __future__ import annotations


# ── Signs ────────────────────────────────────────────────────────────────────

SIGNS = [
    "Mesha",
    "Vrishabha",
    "Mithuna",
    "Karka",
    "Simha",
    "Kanya",
    "Tula",
    "Vrischika",
    "Dhanu",
    "Makara",
    "Kumbha",
    "Meena",
]

SIGNS_EN = [
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

SIGNS_HI = [
    "मेष",
    "वृषभ",
    "मिथुन",
    "कर्क",
    "सिंह",
    "कन्या",
    "तुला",
    "वृश्चिक",
    "धनु",
    "मकर",
    "कुम्भ",
    "मीन",
]

# Element per sign index
SIGN_ELEMENTS = [
    "Fire",
    "Earth",
    "Air",
    "Water",
    "Fire",
    "Earth",
    "Air",
    "Water",
    "Fire",
    "Earth",
    "Air",
    "Water",
]

# Sign lordships
SIGN_LORDS = {
    0: "Mars",  # Mesha / Aries
    1: "Venus",  # Vrishabha / Taurus
    2: "Mercury",  # Mithuna / Gemini
    3: "Moon",  # Karka / Cancer
    4: "Sun",  # Simha / Leo
    5: "Mercury",  # Kanya / Virgo
    6: "Venus",  # Tula / Libra
    7: "Mars",  # Vrischika / Scorpio
    8: "Jupiter",  # Dhanu / Sagittarius
    9: "Saturn",  # Makara / Capricorn
    10: "Saturn",  # Kumbha / Aquarius
    11: "Jupiter",  # Meena / Pisces
}

# Varna (caste for matching) based on sign element
SIGN_VARNA = {
    "Water": "Brahmin",  # Cancer, Scorpio, Pisces
    "Fire": "Kshatriya",  # Aries, Leo, Sagittarius
    "Earth": "Vaishya",  # Taurus, Virgo, Capricorn
    "Air": "Shudra",  # Gemini, Libra, Aquarius
}

VARNA_RANK = {"Brahmin": 4, "Kshatriya": 3, "Vaishya": 2, "Shudra": 1}

# Vasya: sign_index -> list of sign_indices that are vasya to it
VASYA_TABLE: dict[int, list[int]] = {
    0: [4, 7],  # Aries -> Leo, Scorpio
    1: [3, 5],  # Taurus -> Cancer, Virgo
    2: [5],  # Gemini -> Virgo
    3: [7, 8],  # Cancer -> Scorpio, Sagittarius
    4: [6],  # Leo -> Libra
    5: [2, 11],  # Virgo -> Gemini, Pisces
    6: [5, 9],  # Libra -> Virgo, Capricorn
    7: [3],  # Scorpio -> Cancer
    8: [11],  # Sagittarius -> Pisces
    9: [0, 10],  # Capricorn -> Aries, Aquarius
    10: [0],  # Aquarius -> Aries
    11: [8, 9],  # Pisces -> Sagittarius, Capricorn
}

# Bhakoot: unfavorable sign distances (from boy to girl and girl to boy)
BHAKOOT_NEGATIVE_COMBOS = {
    (2, 12),
    (12, 2),  # 2/12 axis
    (6, 8),
    (8, 6),  # 6/8 axis
    (5, 9),
    (9, 5),  # 5/9 axis (some traditions consider this negative)
}
