"""Lal Kitab constants — Pakka Ghar, friendships, enemies.

Source: Lal Kitab (1939-1952) by Pandit Roop Chand Joshi.
"""

from __future__ import annotations

from daivai_engine.constants import EXALTATION


# Pakka Ghar (permanent house) for each planet — fixed regardless of chart
PAKKA_GHAR: dict[str, int] = {
    "Sun": 1,
    "Moon": 4,
    "Mars": 3,
    "Mercury": 7,
    "Jupiter": 2,
    "Venus": 7,
    "Saturn": 8,
    "Rahu": 12,
    "Ketu": 6,
}

# Lal Kitab friendships (different from Parashari)
LK_FRIENDS: dict[str, list[str]] = {
    "Sun": ["Moon", "Mars", "Jupiter"],
    "Moon": ["Sun", "Mercury"],
    "Mars": ["Sun", "Moon", "Jupiter"],
    "Mercury": ["Venus", "Saturn", "Moon"],
    "Jupiter": ["Sun", "Moon", "Mars"],
    "Venus": ["Mercury", "Saturn"],
    "Saturn": ["Mercury", "Venus"],
    "Rahu": ["Mercury", "Venus", "Saturn"],
    "Ketu": ["Mars", "Jupiter"],
}

LK_ENEMIES: dict[str, list[str]] = {
    "Sun": ["Saturn", "Venus", "Rahu", "Ketu"],
    "Moon": ["Rahu", "Ketu"],
    "Mars": ["Mercury", "Ketu"],
    "Mercury": ["Moon"],
    "Jupiter": ["Mercury", "Venus", "Rahu"],
    "Venus": ["Sun", "Moon", "Rahu"],
    "Saturn": ["Sun", "Moon", "Mars"],
    "Rahu": ["Sun", "Moon", "Mars"],
    "Ketu": ["Mercury", "Venus"],
}

# Exalted house mapping (sign index → house number, 1-indexed)
EXALT_HOUSE: dict[str, int] = {p: idx + 1 for p, idx in EXALTATION.items()}
