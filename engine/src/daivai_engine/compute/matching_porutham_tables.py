"""South Indian Porutham tables and constants."""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Rajju — body-cord nakshatra groups. Same group = eliminatory dosha.
# Source: Muhurtha Martanda; traditional South Indian matching texts.
# ---------------------------------------------------------------------------

_RAJJU: dict[str, list[int]] = {
    "Paada": [0, 8, 9, 17, 18, 26],  # Feet
    "Kati": [1, 7, 10, 16, 19, 25],  # Waist
    "Nabhi": [2, 6, 11, 15, 20, 24],  # Navel
    "Kantha": [3, 5, 12, 14, 21, 23],  # Neck
    "Shira": [4, 13, 22],  # Head
}

# Ascending nakshatras (rising through body parts: nak 0-4, 9-13, 18-22)
_RAJJU_ASCENDING: frozenset[int] = frozenset({0, 1, 2, 3, 4, 9, 10, 11, 12, 13, 18, 19, 20, 21, 22})

_NAK_TO_RAJJU: dict[int, str] = {n: part for part, naks in _RAJJU.items() for n in naks}

_RAJJU_SEVERITY: dict[str, str] = {
    "Paada": "mild",
    "Kati": "mild",
    "Nabhi": "moderate",
    "Kantha": "severe",
    "Shira": "severe",
}

_RAJJU_EFFECTS: dict[str, str] = {
    "Paada": "wandering; couple may not settle in one place",
    "Kati": "financial hardships and poverty",
    "Nabhi": "progeny difficulties",
    "Kantha": "danger to wife's longevity",
    "Shira": "danger to husband's longevity (widowhood risk)",
}

# ---------------------------------------------------------------------------
# South Indian Vedha pairs — different from North Indian Vedha.
# 13 pairs covering 26 nakshatras; Dhanishtha (22) has no Vedha partner.
# ---------------------------------------------------------------------------

_SI_VEDHA_PAIRS: frozenset[frozenset[int]] = frozenset(
    {
        frozenset({0, 17}),  # Ashwini   - Jyeshtha
        frozenset({1, 16}),  # Bharani   - Anuradha
        frozenset({2, 15}),  # Krittika  - Vishakha
        frozenset({3, 14}),  # Rohini    - Swati
        frozenset({4, 12}),  # Mrigashira- Hasta
        frozenset({5, 13}),  # Ardra     - Chitra
        frozenset({6, 11}),  # Punarvasu - Uttara Phalguni
        frozenset({7, 10}),  # Pushya    - Purva Phalguni
        frozenset({8, 9}),  # Ashlesha  - Magha
        frozenset({18, 26}),  # Moola     - Revati
        frozenset({19, 25}),  # Purva Ashadha  - Uttara Bhadrapada
        frozenset({20, 24}),  # Uttara Ashadha - Purva Bhadrapada
        frozenset({21, 23}),  # Shravana  - Shatabhisha
    }
)

# Mahendra: agreeable count positions (1-27, from girl nakshatra to boy)
_MAHENDRA_POSITIONS: frozenset[int] = frozenset({4, 7, 10, 13, 16, 19, 22, 25})

# Stree Deergha: count from boy to girl must be strictly greater than this
_STREE_DEERGHA_MIN: int = 13

# Rasi Porutham: disagreeing sign distances (1-12, from girl rasi to boy rasi)
_RASI_BAD: frozenset[int] = frozenset({2, 6, 8, 12})
