"""Namkaran — naming ceremony calculations.

Provides nakshatra-based name letters, Gand Mool check, and basic
name numerology using the Chaldean system.

Source: Traditional Jyotish practice, Chaldean numerology.
"""

from __future__ import annotations

from pydantic import BaseModel

from daivai_engine.models.chart import ChartData


class GandMoolResult(BaseModel):
    """Gand Mool nakshatra check result."""

    is_gand_mool: bool
    nakshatra: str
    pada: int
    severity: str  # none / mild / moderate / severe
    description: str
    recommended_shanti: str


class NameNumerology(BaseModel):
    """Basic Chaldean name numerology result."""

    name: str
    name_number: int  # Single digit 1-9
    raw_sum: int
    interpretation: str


# Nakshatra pada → recommended starting letters (aksharas)
# Source: Traditional Jyotish, all 108 padas mapped
# Format: nakshatra_name → [pada1_letters, pada2, pada3, pada4]
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

# Gand Mool nakshatras — junction nakshatras at water-fire boundaries
# Different from Gandanta (degree-based); this is nakshatra-based
_GAND_MOOL_NAKSHATRAS = {"Ashwini", "Ashlesha", "Magha", "Jyeshtha", "Moola", "Revati"}

# Severity by nakshatra-pada — Moola pada 1 is most severe
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


def get_name_letters(moon_nakshatra: str, moon_pada: int) -> list[str]:
    """Get recommended starting letters for a name.

    Args:
        moon_nakshatra: Moon's nakshatra at birth.
        moon_pada: Moon's pada (1-4).

    Returns:
        List of recommended starting letters (aksharas).
    """
    letters = _NAKSHATRA_LETTERS.get(moon_nakshatra)
    if not letters or not (1 <= moon_pada <= 4):
        return []
    return letters[moon_pada - 1]


def check_gand_mool(chart: ChartData) -> GandMoolResult:
    """Check if Moon is in a Gand Mool nakshatra.

    Gand Mool = Moon in Ashwini, Ashlesha, Magha, Jyeshtha, Moola, or Revati.
    Child born in these nakshatras needs shanti puja.

    Source: Traditional Jyotish practice.
    """
    moon = chart.planets["Moon"]
    nak = moon.nakshatra
    pada = moon.pada

    if nak not in _GAND_MOOL_NAKSHATRAS:
        return GandMoolResult(
            is_gand_mool=False,
            nakshatra=nak,
            pada=pada,
            severity="none",
            description="Moon not in Gand Mool nakshatra",
            recommended_shanti="",
        )

    severity = _GAND_MOOL_SEVERITY.get(nak, {}).get(pada, "mild")
    return GandMoolResult(
        is_gand_mool=True,
        nakshatra=nak,
        pada=pada,
        severity=severity,
        description=f"Moon in {nak} Pada {pada} — Gand Mool dosha present",
        recommended_shanti=f"Gand Mool Shanti Puja recommended (nakshatra: {nak}). "
        f"Perform on 27th day after birth or on a favorable muhurta.",
    )


def compute_name_number(name: str) -> NameNumerology:
    """Compute Chaldean name numerology.

    Sum letter values, reduce to single digit (1-9).

    Source: Chaldean numerology system.
    """
    raw_sum = sum(_CHALDEAN.get(c.upper(), 0) for c in name if c.isalpha())
    number = _reduce_to_single(raw_sum)

    interpretations = {
        1: "Leadership, independence, originality",
        2: "Cooperation, diplomacy, sensitivity",
        3: "Expression, creativity, social",
        4: "Stability, discipline, hard work",
        5: "Freedom, adventure, change",
        6: "Responsibility, love, nurturing",
        7: "Spirituality, analysis, wisdom",
        8: "Power, ambition, material success",
        9: "Compassion, completion, universal love",
    }

    return NameNumerology(
        name=name,
        name_number=number,
        raw_sum=raw_sum,
        interpretation=interpretations.get(number, ""),
    )


def _reduce_to_single(n: int) -> int:
    """Reduce a number to single digit by summing digits."""
    while n > 9:
        n = sum(int(d) for d in str(n))
    return max(n, 1)
