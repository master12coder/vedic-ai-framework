"""Sarvatobhadra Chakra (SBC) — 9x9 raw grid layout and tithi constants."""

from __future__ import annotations


# ── Tithi group → tithi numbers (1-30) ────────────────────────────────────────
# Five groups by position within each paksha (1st/6th/11th = Nanda, etc.)
_TITHI_GROUPS: dict[str, list[int]] = {
    "Nanda": [1, 6, 11, 16, 21, 26],
    "Bhadra": [2, 7, 12, 17, 22, 27],
    "Jaya": [3, 8, 13, 18, 23, 28],
    "Rikta": [4, 9, 14, 19, 24, 29],
    "Purna": [5, 10, 15, 20, 25, 30],
}

# ── Special name for the 28th SBC nakshatra ────────────────────────────────────
_ABHIJIT = "Abhijit"

# ── Compact raw grid definition ────────────────────────────────────────────────
# Encoding:
#   ('n', int)              nakshatra, 1-based SBC number (1-28)
#   ('v', str)              vowel (svara)
#   ('c', str)              consonant (vyanjana)
#   ('r', int)              rashi, 1-based (1=Mesha … 12=Meena)
#   ('t', str, list[str])   tithi group + varas
#   ('ct', str, list[str])  center cell: Purna tithi + Saturday

_GRID_RAW: list[list[tuple]] = [
    # Row 0 — North outer ring (left→right, zodiacal Dhanishtha→Bharani)
    [
        ("v", "ii"),
        ("n", 23),
        ("n", 24),
        ("n", 25),
        ("n", 26),
        ("n", 27),
        ("n", 1),
        ("n", 2),
        ("v", "a"),
    ],
    # Row 1 — Ring 2 North consonants; outer WEST=22(Shravana), EAST=3(Krittika)
    [
        ("n", 22),
        ("v", "rii"),
        ("c", "ga"),
        ("c", "sa"),
        ("c", "da"),
        ("c", "cha"),
        ("c", "la"),
        ("v", "u"),
        ("n", 3),
    ],
    # Row 2 — Abhijit on WEST; Ring 2 East 'a'; Ring 3 North rashis; EAST=4(Rohini)
    [
        ("n", 28),
        ("c", "kha"),
        ("v", "ai"),
        ("r", 11),
        ("r", 12),
        ("r", 1),
        ("v", "lu"),
        ("c", "a"),
        ("n", 4),
    ],
    # Row 3 — Ring 3 West/East rashis; Ring 4 corners; Rikta/Friday cell
    [
        ("n", 21),
        ("c", "ja"),
        ("r", 10),
        ("v", "ah"),
        ("t", "Rikta", ["Friday"]),
        ("v", "o"),
        ("r", 2),
        ("c", "va"),
        ("n", 5),
    ],
    # Row 4 — Center row: Jaya/Thursday, CENTER Purna/Saturday, Nanda/Sun+Tue
    [
        ("n", 20),
        ("c", "bha"),
        ("r", 9),
        ("t", "Jaya", ["Thursday"]),
        ("ct", "Purna", ["Saturday"]),
        ("t", "Nanda", ["Sunday", "Tuesday"]),
        ("r", 3),
        ("c", "ka"),
        ("n", 6),
    ],
    # Row 5 — Ring 3/4 junction; Bhadra/Mon+Wed cell
    [
        ("n", 19),
        ("c", "ya"),
        ("r", 8),
        ("v", "am"),
        ("t", "Bhadra", ["Monday", "Wednesday"]),
        ("v", "au"),
        ("r", 4),
        ("c", "ha"),
        ("n", 7),
    ],
    # Row 6 — Ring 3 South rashis (Libra, Virgo, Leo); Ring 2 East 'da'
    [
        ("n", 18),
        ("c", "na"),
        ("v", "e"),
        ("r", 7),
        ("r", 6),
        ("r", 5),
        ("v", "luu"),
        ("c", "da"),
        ("n", 8),
    ],
    # Row 7 — Ring 2 South consonants; outer WEST=17(Anuradha), EAST=9(Ashlesha)
    [
        ("n", 17),
        ("v", "ri"),
        ("c", "ta"),
        ("c", "ra"),
        ("c", "pa"),
        ("c", "tha"),
        ("c", "ma"),
        ("v", "uu"),
        ("n", 9),
    ],
    # Row 8 — South outer ring (left→right, Vishakha→Magha)
    [
        ("v", "i"),
        ("n", 16),
        ("n", 15),
        ("n", 14),
        ("n", 13),
        ("n", 12),
        ("n", 11),
        ("n", 10),
        ("v", "aa"),
    ],
]
