"""Planet-related Vedic astrology constants."""

from __future__ import annotations

import swisseph as swe


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
