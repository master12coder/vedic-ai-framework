"""Lookup tables and constants for gemstone weight computation.

These are pure data: divisors, stone names, multiplier tables, free alternatives.
"""

from __future__ import annotations


# ── Planet → base weight divisor (body_weight_kg / divisor) ──────────────
BASE_DIVISOR: dict[str, float] = {
    "Sun": 10,
    "Moon": 10,
    "Mars": 10,
    "Mercury": 12,
    "Jupiter": 10,
    "Venus": 20,
    "Saturn": 15,
    "Rahu": 10,
    "Ketu": 12,
}

# ── Planet → stone name (EN, HI) ────────────────────────────────────────
PLANET_STONE: dict[str, tuple[str, str]] = {
    "Sun": ("Ruby", "माणिक्य"),
    "Moon": ("Pearl", "मोती"),
    "Mars": ("Red Coral", "मूंगा"),
    "Mercury": ("Emerald", "पन्ना"),
    "Jupiter": ("Yellow Sapphire", "पुखराज"),
    "Venus": ("Diamond", "हीरा"),
    "Saturn": ("Blue Sapphire", "नीलम"),
    "Rahu": ("Hessonite", "गोमेद"),
    "Ketu": ("Cat's Eye", "लहसुनिया"),
}

# ── Factor multiplier tables ────────────────────────────────────────────
AVASTHA_MULT: dict[str, float] = {
    "Bala": 0.80,
    "Kumara": 0.90,
    "Yuva": 1.00,
    "Vriddha": 0.75,
    "Mruta": 0.65,
}

DIGNITY_MULT: dict[str, float] = {
    "exalted": 0.75,
    "mooltrikona": 0.80,
    "own": 0.85,
    "neutral": 1.00,
    "enemy": 0.95,
    "debilitated": 0.90,
}

STONE_ENERGY: dict[str, float] = {
    "Diamond": 0.35,
    "Blue Sapphire": 0.75,
    "Cat's Eye": 0.90,
}

PURPOSE_MULT: dict[str, float] = {
    "protection": 0.60,
    "growth": 0.90,
    "maximum": 1.00,
}

# ── Free alternatives per planet ────────────────────────────────────────
FREE_ALT: dict[str, dict[str, str]] = {
    "Sun": {
        "mantra": "ओम् सूर्याय नमः (7000x)",
        "daan": "Wheat + Jaggery on Sunday",
        "color": "Red/Orange",
    },
    "Moon": {
        "mantra": "ओम् नमः शिवाय (11000x)",
        "daan": "Rice + Milk on Monday",
        "color": "White/Silver",
    },
    "Mars": {
        "mantra": "ओम् भौमाय नमः (10000x)",
        "daan": "Red lentils on Tuesday",
        "color": "Red",
    },
    "Mercury": {
        "mantra": "ओम् बुधाय नमः (9000x)",
        "daan": "Green moong on Wednesday",
        "color": "Green",
    },
    "Jupiter": {
        "mantra": "ओम् गुरुवे नमः (19000x)",
        "daan": "Turmeric + Chana on Thursday",
        "color": "Yellow",
    },
    "Venus": {
        "mantra": "ओम् शुक्राय नमः (16000x)",
        "daan": "Rice + Ghee on Friday",
        "color": "White/Pastel",
    },
    "Saturn": {
        "mantra": "ओम् शनैश्चराय नमः (23000x)",
        "daan": "Black til + Iron on Saturday",
        "color": "Black/Blue",
    },
    "Rahu": {
        "mantra": "ओम् राहवे नमः (18000x)",
        "daan": "Coconut + Blanket on Saturday",
        "color": "Grey/Smoke",
    },
    "Ketu": {
        "mantra": "ओम् केतवे नमः (17000x)",
        "daan": "Blanket for dog on Tuesday",
        "color": "Brown/Grey",
    },
}

GOOD_HOUSES: frozenset[int] = frozenset({1, 4, 5, 7, 9, 10})
TRIK_HOUSES: frozenset[int] = frozenset({6, 8, 12})
