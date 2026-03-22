"""Miscellaneous Vedic astrology constants — panchang, matching, astro geometry."""

from __future__ import annotations


# ── Matching ─────────────────────────────────────────────────────────────────

# ── Panchang ─────────────────────────────────────────────────────────────────

TITHI_NAMES = [
    "Pratipada",
    "Dwitiya",
    "Tritiya",
    "Chaturthi",
    "Panchami",
    "Shashthi",
    "Saptami",
    "Ashtami",
    "Navami",
    "Dashami",
    "Ekadashi",
    "Dwadashi",
    "Trayodashi",
    "Chaturdashi",
    "Purnima",
    "Pratipada",
    "Dwitiya",
    "Tritiya",
    "Chaturthi",
    "Panchami",
    "Shashthi",
    "Saptami",
    "Ashtami",
    "Navami",
    "Dashami",
    "Ekadashi",
    "Dwadashi",
    "Trayodashi",
    "Chaturdashi",
    "Amavasya",
]

KARANA_NAMES = [
    "Bava",
    "Balava",
    "Kaulava",
    "Taitila",
    "Garaja",
    "Vanija",
    "Vishti",  # Repeating karanas
    "Shakuni",
    "Chatushpada",
    "Nagava",
    "Kimstughna",  # Fixed karanas
]

# Panchang Yoga (not planetary yoga)
PANCHANG_YOGA_NAMES = [
    "Vishkambha",
    "Priti",
    "Ayushman",
    "Saubhagya",
    "Shobhana",
    "Atiganda",
    "Sukarma",
    "Dhriti",
    "Shula",
    "Ganda",
    "Vriddhi",
    "Dhruva",
    "Vyaghata",
    "Harshana",
    "Vajra",
    "Siddhi",
    "Vyatipata",
    "Variyan",
    "Parigha",
    "Shiva",
    "Siddha",
    "Sadhya",
    "Shubha",
    "Shukla",
    "Brahma",
    "Indra",
    "Vaidhriti",
]

# Muhurta: favorable nakshatras per purpose
MUHURTA_FAVORABLE_NAKSHATRAS: dict[str, list[str]] = {
    "marriage": [
        "Rohini",
        "Mrigashira",
        "Magha",
        "Uttara Phalguni",
        "Hasta",
        "Swati",
        "Anuradha",
        "Moola",
        "Uttara Ashadha",
        "Shravana",
        "Dhanishta",
        "Uttara Bhadrapada",
        "Revati",
    ],
    "business": [
        "Ashwini",
        "Rohini",
        "Punarvasu",
        "Pushya",
        "Hasta",
        "Chitra",
        "Swati",
        "Anuradha",
        "Shravana",
        "Dhanishta",
        "Revati",
    ],
    "travel": [
        "Ashwini",
        "Mrigashira",
        "Punarvasu",
        "Pushya",
        "Hasta",
        "Anuradha",
        "Shravana",
        "Revati",
    ],
    "property": [
        "Rohini",
        "Uttara Phalguni",
        "Uttara Ashadha",
        "Uttara Bhadrapada",
        "Pushya",
        "Shravana",
    ],
}

# Rahu Kaal time slots per day (eighths of day from sunrise)
# Day index (0=Sun..6=Sat) -> which eighth of daylight is Rahu Kaal
RAHU_KAAL_SLOT: dict[int, int] = {
    0: 8,
    1: 2,
    2: 7,
    3: 5,
    4: 6,
    5: 4,
    6: 3,
}

# Yamaghanda time slots per day
YAMAGHANDA_SLOT: dict[int, int] = {
    0: 5,
    1: 4,
    2: 3,
    3: 2,
    4: 1,
    5: 7,
    6: 6,
}

# Gulika time slots per day
GULIKA_SLOT: dict[int, int] = {
    0: 7,
    1: 6,
    2: 5,
    3: 4,
    4: 3,
    5: 2,
    6: 1,
}

# ── Astro ────────────────────────────────────────────────────────────────────

# Circle geometry
FULL_CIRCLE_DEG = 360.0
HALF_CIRCLE_DEG = 180.0
NUM_SIGNS = 12
DEGREES_PER_SIGN = 30.0

# Nakshatra constants
NUM_NAKSHATRAS = 27
MAX_NAKSHATRA_INDEX = 26
NAKSHATRA_SPAN_DEG = FULL_CIRCLE_DEG / NUM_NAKSHATRAS  # 13.3333...
PADAS_PER_NAKSHATRA = 4

# Ashtakavarga
SARVASHTAKAVARGA_TOTAL = 337  # Sum of all SAV bindus is always 337

# Ashtakavarga Shodhya Pinda multipliers — BPHS Ch.71
# Rasi Gunakara: sign multiplier (index 0=Aries … 11=Pisces)
RASI_GUNAKARA: list[int] = [7, 10, 8, 4, 10, 6, 7, 8, 9, 5, 11, 12]

# Graha Gunakara: planet multiplier for Graha Pinda computation
GRAHA_GUNAKARA: dict[str, int] = {
    "Sun": 5,
    "Moon": 5,
    "Mars": 8,
    "Mercury": 5,
    "Jupiter": 10,
    "Venus": 7,
    "Saturn": 5,
}

# Conjunction and aspect defaults
DEFAULT_CONJUNCTION_ORB = 10.0  # Degrees within which two planets are conjunct

# Daily suggestion
MAX_DAY_RATING = 10  # Day rating scale: 1 to MAX_DAY_RATING
