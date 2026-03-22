"""All Vedic astrology constants — single source of truth.

Merged from jyotish.domain.constants: signs, planets, nakshatras, dignity,
dashas, houses, matching, panchang, astro.
"""

from __future__ import annotations

import swisseph as swe


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

# ── Planets ──────────────────────────────────────────────────────────────────

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

PLANETS_HI = [
    "सूर्य",
    "चन्द्र",
    "मंगल",
    "बुध",
    "बृहस्पति",
    "शुक्र",
    "शनि",
    "राहु",
    "केतु",
]

# Swiss Ephemeris planet indices
SWE_PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.TRUE_NODE,  # True Node
}
# Ketu = Rahu + 180°

# Planetary friendships
NATURAL_FRIENDS: dict[str, list[str]] = {
    "Sun": ["Moon", "Mars", "Jupiter"],
    "Moon": ["Sun", "Mercury"],
    "Mars": ["Sun", "Moon", "Jupiter"],
    "Mercury": ["Sun", "Venus"],
    "Jupiter": ["Sun", "Moon", "Mars"],
    "Venus": ["Mercury", "Saturn"],
    "Saturn": ["Mercury", "Venus"],
    "Rahu": ["Mercury", "Venus", "Saturn"],
    "Ketu": ["Mars", "Jupiter"],
}

NATURAL_ENEMIES: dict[str, list[str]] = {
    "Sun": ["Saturn", "Venus"],
    "Moon": ["Rahu", "Ketu"],
    "Mars": ["Mercury"],
    "Mercury": ["Moon"],
    "Jupiter": ["Mercury", "Venus"],
    "Venus": ["Sun", "Moon"],
    "Saturn": ["Sun", "Moon", "Mars"],
    "Rahu": ["Sun", "Moon", "Mars"],
    "Ketu": ["Mercury", "Venus"],
}

NATURAL_NEUTRALS: dict[str, list[str]] = {
    "Sun": ["Mercury"],
    "Moon": ["Mars", "Jupiter", "Venus", "Saturn"],
    "Mars": ["Venus", "Saturn"],
    "Mercury": ["Mars", "Jupiter", "Saturn"],
    "Jupiter": ["Saturn"],
    "Venus": ["Mars", "Jupiter"],
    "Saturn": ["Jupiter"],
    "Rahu": ["Jupiter"],
    "Ketu": ["Saturn", "Moon", "Sun"],
}

# Combustion limits (degrees from Sun)
COMBUSTION_LIMITS: dict[str, float] = {
    "Moon": 12.0,
    "Mars": 17.0,
    "Mercury": 14.0,  # 12.0 when retrograde
    "Jupiter": 11.0,
    "Venus": 10.0,  # 8.0 when retrograde
    "Saturn": 15.0,
}

COMBUSTION_LIMITS_RETROGRADE: dict[str, float] = {
    "Mercury": 12.0,
    "Venus": 8.0,
}

# Cazimi threshold: planet within 17 arc-minutes of Sun is "in the heart of the Sun"
# (Combust by Beams). Such planets are extremely powerful — not weakened.
# Source: Saravali Ch.4; Phaladeepika Ch.2 v.6.
CAZIMI_LIMIT: float = 17.0 / 60.0  # 0.2833° = 17 arc-minutes

# Special (additional) aspects beyond the standard 7th-house aspect
SPECIAL_ASPECTS: dict[str, list[int]] = {
    "Mars": [4, 8],  # 4th and 8th house aspects
    "Jupiter": [5, 9],  # 5th and 9th house aspects
    "Saturn": [3, 10],  # 3rd and 10th house aspects
    "Rahu": [5, 9],  # Same as Jupiter
    "Ketu": [5, 9],  # Same as Jupiter
}

# Aspect strength fractions for Drik Bala computation (BPHS Ch.23)
# Key: planet → {Nth_house_from_planet: strength_fraction (0.0-1.0)}
# "Nth house from planet" is 1-indexed: 7 means the 7th house from planet.
# All planets cast 100% aspect on the 7th house.
# Planets not listed here use the default (7th house only at 100%).
ASPECT_STRENGTHS: dict[str, dict[int, float]] = {
    "Mars": {4: 0.75, 7: 1.0, 8: 1.0},  # 4th=¾, 7th=full, 8th=full
    "Jupiter": {5: 0.50, 7: 1.0, 9: 1.0},  # 5th=½, 7th=full, 9th=full
    "Saturn": {3: 0.25, 7: 1.0, 10: 1.0},  # 3rd=¼, 7th=full, 10th=full
    "Rahu": {5: 0.50, 7: 1.0, 9: 1.0},  # Parashari: same as Jupiter
    "Ketu": {5: 0.50, 7: 1.0, 9: 1.0},  # Parashari: same as Jupiter
}
# Default for Sun, Moon, Mercury, Venus: only 7th house at full strength
ASPECT_STRENGTH_DEFAULT: dict[int, float] = {7: 1.0}

# Day-planet mapping
DAY_PLANET = {
    0: "Sun",  # Sunday
    1: "Moon",  # Monday
    2: "Mars",  # Tuesday
    3: "Mercury",  # Wednesday
    4: "Jupiter",  # Thursday
    5: "Venus",  # Friday
    6: "Saturn",  # Saturday
}

DAY_NAMES = {
    0: "Sunday",
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
}

DAY_NAMES_HI = {
    0: "रविवार",
    1: "सोमवार",
    2: "मंगलवार",
    3: "बुधवार",
    4: "गुरुवार",
    5: "शुक्रवार",
    6: "शनिवार",
}

# ── Nakshatras ───────────────────────────────────────────────────────────────

NAKSHATRAS = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Moola",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]

NAKSHATRAS_HI = [
    "अश्विनी",
    "भरणी",
    "कृत्तिका",
    "रोहिणी",
    "मृगशिरा",
    "आर्द्रा",
    "पुनर्वसु",
    "पुष्य",
    "अश्लेषा",
    "मघा",
    "पूर्वा फाल्गुनी",
    "उत्तरा फाल्गुनी",
    "हस्त",
    "चित्रा",
    "स्वाती",
    "विशाखा",
    "अनुराधा",
    "ज्येष्ठा",
    "मूला",
    "पूर्वाषाढ़ा",
    "उत्तराषाढ़ा",
    "श्रवण",
    "धनिष्ठा",
    "शतभिषा",
    "पूर्वा भाद्रपद",
    "उत्तरा भाद्रपद",
    "रेवती",
]

# Nakshatra lords (Vimshottari dasha sequence)
NAKSHATRA_LORDS = [
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
]

# Nakshatra ganas: Deva, Manushya, Rakshasa
NAKSHATRA_GANAS = [
    "Deva",
    "Manushya",
    "Rakshasa",
    "Manushya",
    "Deva",
    "Manushya",
    "Deva",
    "Deva",
    "Rakshasa",
    "Rakshasa",
    "Manushya",
    "Manushya",
    "Deva",
    "Rakshasa",
    "Deva",
    "Rakshasa",
    "Deva",
    "Rakshasa",
    "Rakshasa",
    "Manushya",
    "Manushya",
    "Deva",
    "Rakshasa",
    "Rakshasa",
    "Manushya",
    "Manushya",
    "Deva",
]

# Nakshatra animals for Yoni matching (14 animal types)
NAKSHATRA_ANIMALS = [
    "Horse",
    "Elephant",
    "Goat",
    "Serpent",
    "Serpent",
    "Dog",
    "Cat",
    "Goat",
    "Cat",
    "Rat",
    "Rat",
    "Cow",
    "Buffalo",
    "Tiger",
    "Buffalo",
    "Tiger",
    "Deer",
    "Deer",
    "Dog",
    "Monkey",
    "Mongoose",
    "Monkey",
    "Lion",
    "Horse",
    "Lion",
    "Cow",
    "Elephant",
]

# Nakshatra Nadi: Aadi, Madhya, Antya
NAKSHATRA_NADIS = [
    "Aadi",
    "Aadi",
    "Aadi",
    "Madhya",
    "Madhya",
    "Madhya",
    "Antya",
    "Antya",
    "Antya",
    "Aadi",
    "Aadi",
    "Aadi",
    "Madhya",
    "Madhya",
    "Madhya",
    "Antya",
    "Antya",
    "Antya",
    "Aadi",
    "Aadi",
    "Aadi",
    "Madhya",
    "Madhya",
    "Madhya",
    "Antya",
    "Antya",
    "Antya",
]

# ── Dignity ──────────────────────────────────────────────────────────────────

# Sign index where each planet is exalted
EXALTATION: dict[str, int] = {
    "Sun": 0,  # Aries
    "Moon": 1,  # Taurus
    "Mars": 9,  # Capricorn
    "Mercury": 5,  # Virgo
    "Jupiter": 3,  # Cancer
    "Venus": 11,  # Pisces
    "Saturn": 6,  # Libra
    "Rahu": 1,  # Taurus per BPHS. Alternative: Gemini per some Nadi texts.
    "Ketu": 7,  # Scorpio per BPHS. Alternative: Sagittarius per some Nadi texts.
}

# Exact exaltation degree within the sign
EXALTATION_DEGREE: dict[str, float] = {
    "Sun": 10.0,
    "Moon": 3.0,
    "Mars": 28.0,
    "Mercury": 15.0,
    "Jupiter": 5.0,
    "Venus": 27.0,
    "Saturn": 20.0,
    "Rahu": 20.0,
    "Ketu": 20.0,
}

# Sign index where each planet is debilitated (opposite of exaltation)
DEBILITATION: dict[str, int] = {
    "Sun": 6,  # Libra
    "Moon": 7,  # Scorpio
    "Mars": 3,  # Cancer
    "Mercury": 11,  # Pisces
    "Jupiter": 9,  # Capricorn
    "Venus": 5,  # Virgo
    "Saturn": 0,  # Aries
    "Rahu": 7,  # Scorpio
    "Ketu": 1,  # Taurus
}

# Own signs for each planet
OWN_SIGNS: dict[str, list[int]] = {
    "Sun": [4],  # Leo
    "Moon": [3],  # Cancer
    "Mars": [0, 7],  # Aries, Scorpio
    "Mercury": [2, 5],  # Gemini, Virgo
    "Jupiter": [8, 11],  # Sagittarius, Pisces
    "Venus": [1, 6],  # Taurus, Libra
    "Saturn": [9, 10],  # Capricorn, Aquarius
    "Rahu": [10],  # Aquarius (co-lord)
    "Ketu": [7],  # Scorpio (co-lord)
}

# Mooltrikona signs and degree ranges
MOOLTRIKONA: dict[str, tuple[int, float, float]] = {
    "Sun": (4, 0.0, 20.0),  # Leo 0-20
    "Moon": (1, 3.0, 30.0),  # Taurus 3-30
    "Mars": (0, 0.0, 12.0),  # Aries 0-12
    "Mercury": (5, 15.0, 20.0),  # Virgo 15-20
    "Jupiter": (8, 0.0, 10.0),  # Sagittarius 0-10
    "Venus": (6, 0.0, 15.0),  # Libra 0-15
    "Saturn": (10, 0.0, 20.0),  # Aquarius 0-20
}

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

# ── Houses ───────────────────────────────────────────────────────────────────

KENDRAS = [1, 4, 7, 10]  # Quadrants
TRIKONAS = [1, 5, 9]  # Trines
DUSTHANAS = [6, 8, 12]  # Malefic houses
UPACHAYAS = [3, 6, 10, 11]  # Growth houses
MARAKAS = [2, 7]  # Death-inflicting houses
TRISHADAYAS = [3, 6, 11]  # Houses of effort

# Avastha (Planetary Age States) based on degree range in odd/even signs
AVASTHAS = ["Bala", "Kumara", "Yuva", "Vriddha", "Mruta"]

# ── Matching ─────────────────────────────────────────────────────────────────

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

# Yoni: animals and their enemies for yoni matching
YONI_ENEMIES: dict[str, str] = {
    "Horse": "Buffalo",
    "Buffalo": "Horse",
    "Elephant": "Lion",
    "Lion": "Elephant",
    "Dog": "Deer",
    "Deer": "Dog",
    "Cat": "Rat",
    "Rat": "Cat",
    "Serpent": "Mongoose",
    "Mongoose": "Serpent",
    "Monkey": "Goat",
    "Goat": "Monkey",
    "Tiger": "Cow",
    "Cow": "Tiger",
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
