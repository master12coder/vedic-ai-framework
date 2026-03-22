"""Domain models for Sarvatobhadra Chakra (SBC) analysis.

The SBC is a 9x9 transit analysis grid used by both North and South Indian
pandits. Transiting planets create vedha (geometric obstruction) through
the grid, striking nakshatras, rashis, tithis, and varas.

Source: Phaladeepika Ch.26; Gopesh Kumar Ojha commentary (Bhavartha Bodhini).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SBCCell(BaseModel):
    """A single cell in the 9x9 Sarvatobhadra Chakra grid.

    Each cell occupies a unique (row, col) position and can contain one or more
    of: nakshatra assignment, vowel (svara), consonant (vyanjana), rashi, and/or
    a tithi-group with associated varas (weekdays).

    The grid has five concentric rings:
      Ring 1 (outermost): 28 nakshatras + 4 corner vowels
      Ring 2 (7x7):       consonants + 4 corner vowels
      Ring 3 (5x5):       12 rashis + 4 corner vowels
      Ring 4 (3x3):       4 tithi-vara cells + 4 corner vowels
      Center (1 cell):    Purna tithi + Saturday
    """

    model_config = ConfigDict(frozen=True)

    row: int = Field(ge=0, le=8)
    col: int = Field(ge=0, le=8)

    # Nakshatra content (1-based SBC numbers: 1-27 standard + 28=Abhijit)
    nakshatra_nums: list[int] = Field(default_factory=list)
    nakshatra_names: list[str] = Field(default_factory=list)

    # Akshara content
    vowels: list[str] = Field(default_factory=list)  # Sanskrit svaras
    consonants: list[str] = Field(default_factory=list)  # Sanskrit vyanjanas

    # Rashi content (1-based: 1=Mesha … 12=Meena)
    rashis: list[int] = Field(default_factory=list)
    rashi_names: list[str] = Field(default_factory=list)

    # Tithi/Vara content
    tithi_group: str | None = None  # Nanda / Bhadra / Jaya / Rikta / Purna
    tithi_numbers: list[int] = Field(default_factory=list)  # e.g. [1,6,11,16,21,26]
    varas: list[str] = Field(default_factory=list)  # day names

    is_center: bool = False  # True only for cell (4,4)


class SBCVedhaResult(BaseModel):
    """Result of SBC vedha analysis for one transiting planet.

    Contains the three geometric vedha types and derived summaries of all
    struck nakshatras, tithis, and varas.

    Vedha types:
      across (Tirya Vedha):     entire row + column through the planet's cell
      fore   (Agra Vedha):      / diagonal (clockwise / zodiacal direction)
      hind   (Prishthaja Vedha): \\ diagonal (counter-clockwise direction)

    Motion rule (for the products layer to apply):
      Sun / Moon          → across + fore always active
      Rahu / Ketu         → across + hind always active
      Other planets direct→ across vedha
      Other planets fast  → fore vedha
      Other planets retro → hind vedha

    Source: Phaladeepika Ch.26; Mansagari; Gopesh Kumar Ojha.
    """

    model_config = ConfigDict(frozen=True)

    transit_planet: str
    transit_nakshatra_num: int = Field(ge=1, le=28)  # 1-based SBC number
    transit_nakshatra: str
    planet_row: int = Field(ge=0, le=8)
    planet_col: int = Field(ge=0, le=8)

    # Raw struck cells per vedha type
    across_vedha: list[SBCCell]  # 16 cells: full row (8) + full col (8)
    fore_vedha: list[SBCCell]  # / diagonal cells (count varies by position)
    hind_vedha: list[SBCCell]  # \ diagonal cells (count varies by position)

    # Nakshatra names struck per vedha type
    struck_nakshatras_across: list[str]
    struck_nakshatras_fore: list[str]
    struck_nakshatras_hind: list[str]

    # Tithi groups and varas struck via across vedha (most commonly used)
    struck_tithis_across: list[str]  # e.g. ["Nanda", "Purna"]
    struck_varas_across: list[str]  # e.g. ["Saturday", "Sunday"]
