"""KP system house grouping tables for event promise analysis."""

from __future__ import annotations


# Classical KP house groupings for determining if an event will occur.
# An event happens when the cusp sub lord of the relevant house group
# is a significator of the supportive houses for that event.
# Source: KP Reader 1-6 by K.S. Krishnamurti.
KP_HOUSE_GROUPS: dict[str, dict[str, list[int] | str | int]] = {
    "marriage": {
        "positive_houses": [2, 7, 11],
        "negative_houses": [1, 6, 10, 12],
        "primary_cusp": 7,
        "description": (
            "Marriage: Sub lord of 7th cusp must signify 2, 7, or 11. "
            "If it also signifies 1, 6, or 10, separation/delay is possible. "
            "Venus + Jupiter as significators = ideal."
        ),
    },
    "career": {
        "positive_houses": [2, 6, 10, 11],
        "negative_houses": [1, 5, 9, 12],
        "primary_cusp": 10,
        "description": (
            "Career/job: Sub lord of 10th cusp must signify 2, 6, 10, or 11. "
            "Saturn in 6 or 10 = service; Jupiter = teaching; Sun = authority."
        ),
    },
    "property": {
        "positive_houses": [4, 11, 12],
        "negative_houses": [3, 6, 10],
        "primary_cusp": 4,
        "description": (
            "Property purchase: Sub lord of 4th cusp must signify 4, 11, 12. "
            "12 = parting with money (buying). 6 = renting. 3 = selling."
        ),
    },
    "travel_foreign": {
        "positive_houses": [8, 9, 12],
        "negative_houses": [2, 3, 4],
        "primary_cusp": 9,
        "description": (
            "Foreign travel/settlement: Sub lord of 9th/12th must signify 8, 9, 12. "
            "12 = foreign land; 8 = permanent settlement; 9 = long journey."
        ),
    },
    "education": {
        "positive_houses": [4, 9, 11],
        "negative_houses": [1, 5, 12],
        "primary_cusp": 4,
        "description": (
            "Education success: Sub lord of 4th/9th must signify 4, 9, 11. "
            "11 = fulfillment; 4 = academic qualification; 9 = higher learning."
        ),
    },
    "health_recovery": {
        "positive_houses": [1, 5, 11],
        "negative_houses": [6, 8, 12],
        "primary_cusp": 1,
        "description": (
            "Health/recovery: Sub lord of 1st cusp must signify 1, 5, 11. "
            "6, 8, 12 indicate illness. 11 = recovery. Saturn in 6 = chronic."
        ),
    },
    "children": {
        "positive_houses": [2, 5, 11],
        "negative_houses": [1, 4, 10],
        "primary_cusp": 5,
        "description": (
            "Children/progeny: Sub lord of 5th must signify 2, 5, 11. "
            "If it signifies 1, 4, 10 with 5 = adoption/step-child."
        ),
    },
    "wealth_gains": {
        "positive_houses": [2, 6, 10, 11],
        "negative_houses": [5, 8, 12],
        "primary_cusp": 11,
        "description": (
            "Financial gains: Sub lord of 11th must signify 2, 6, 10, 11. "
            "12 = losses. 8 = sudden gains/inheritance. 5 = speculation."
        ),
    },
}
