"""Namakarana tables — 108-pada syllable map, Gand Mool, Chaldean numerology."""

from __future__ import annotations


# ── 108-pada syllable table (27 nakshatras x 4 padas) ────────────────────────
# Source: Traditional Jyotish — recommended starting aksharas for naming.
# Format: nakshatra → [pada_1_letters, pada_2, pada_3, pada_4]
_NAKSHATRA_LETTERS: dict[str, list[list[str]]] = {
    "Ashwini": [["Chu"], ["Che"], ["Cho"], ["La"]],
    "Bharani": [["Li"], ["Lu"], ["Le"], ["Lo"]],
    "Krittika": [["A"], ["I"], ["U"], ["E"]],
    "Rohini": [["O"], ["Va"], ["Vi"], ["Vu"]],
    "Mrigashira": [["Ve"], ["Vo"], ["Ka"], ["Ki"]],
    "Ardra": [["Ku"], ["Gha"], ["Ng"], ["Na"]],
    "Punarvasu": [["Ke"], ["Ko"], ["Ha"], ["Hi"]],
    "Pushya": [["Hu"], ["He"], ["Ho"], ["Da"]],
    "Ashlesha": [["Di"], ["Du"], ["De"], ["Do"]],
    "Magha": [["Ma"], ["Mi"], ["Mu"], ["Me"]],
    "Purva Phalguni": [["Mo"], ["Ta"], ["Ti"], ["Tu"]],
    "Uttara Phalguni": [["Te"], ["To"], ["Pa"], ["Pi"]],
    "Hasta": [["Pu"], ["Sha"], ["Na"], ["Tha"]],
    "Chitra": [["Pe"], ["Po"], ["Ra"], ["Ri"]],
    "Swati": [["Ru"], ["Re"], ["Ro"], ["Ta"]],
    "Vishakha": [["Ti"], ["Tu"], ["Te"], ["To"]],
    "Anuradha": [["Na"], ["Ni"], ["Nu"], ["Ne"]],
    "Jyeshtha": [["No"], ["Ya"], ["Yi"], ["Yu"]],
    "Moola": [["Ye"], ["Yo"], ["Bha"], ["Bhi"]],
    "Purva Ashadha": [["Bhu"], ["Dha"], ["Pha"], ["Dha"]],
    "Uttara Ashadha": [["Bhe"], ["Bho"], ["Ja"], ["Ji"]],
    "Shravana": [["Ju"], ["Je"], ["Jo"], ["Gha"]],
    "Dhanishta": [["Ga"], ["Gi"], ["Gu"], ["Ge"]],
    "Shatabhisha": [["Go"], ["Sa"], ["Si"], ["Su"]],
    "Purva Bhadrapada": [["Se"], ["So"], ["Da"], ["Di"]],
    "Uttara Bhadrapada": [["Du"], ["Tha"], ["Jha"], ["Da"]],
    "Revati": [["De"], ["Do"], ["Cha"], ["Chi"]],
}

# Gand Mool nakshatras — junction points at rasi-sandhi (fire/water boundaries)
_GAND_MOOL_NAKSHATRAS: frozenset[str] = frozenset(
    {"Ashwini", "Ashlesha", "Magha", "Jyeshtha", "Moola", "Revati"}
)

# Severity per nakshatra-pada — Moola P1 and Magha P1 are most severe
_GAND_MOOL_SEVERITY: dict[str, dict[int, str]] = {
    "Moola": {1: "severe", 2: "moderate", 3: "mild", 4: "mild"},
    "Ashlesha": {1: "mild", 2: "mild", 3: "moderate", 4: "severe"},
    "Jyeshtha": {1: "mild", 2: "mild", 3: "moderate", 4: "severe"},
    "Revati": {1: "mild", 2: "mild", 3: "mild", 4: "moderate"},
    "Ashwini": {1: "moderate", 2: "mild", 3: "mild", 4: "mild"},
    "Magha": {1: "severe", 2: "moderate", 3: "mild", 4: "mild"},
}

# Chaldean numerology letter values
_CHALDEAN: dict[str, int] = {
    "A": 1,
    "B": 2,
    "C": 3,
    "D": 4,
    "E": 5,
    "F": 8,
    "G": 3,
    "H": 5,
    "I": 1,
    "J": 1,
    "K": 2,
    "L": 3,
    "M": 4,
    "N": 5,
    "O": 7,
    "P": 8,
    "Q": 1,
    "R": 2,
    "S": 3,
    "T": 4,
    "U": 6,
    "V": 6,
    "W": 6,
    "X": 5,
    "Y": 1,
    "Z": 7,
}
