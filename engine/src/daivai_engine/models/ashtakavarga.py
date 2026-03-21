"""Domain models for Ashtakavarga, Prastara, Kaksha, and Shodhana computation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AshtakavargaResult(BaseModel):
    """Ashtakavarga point system result from BPHS chapters 66-72.

    Contains Bhinnashtakavarga (per-planet bindu tables), Sarvashtakavarga
    (aggregate across all contributors per sign), and the total bindu count
    which must always equal 337 for a valid computation.

    Attributes:
        bhinna: Per-planet bindu tables. Keys are planet names (Sun..Saturn),
                values are lists of 12 integers (one per sign, Aries..Pisces).
        sarva: Sarvashtakavarga — sum of all 7 Bhinna tables per sign (12 values).
        total: Sum of all Sarvashtakavarga values (must equal 337).
    """

    model_config = ConfigDict(frozen=True)

    bhinna: dict[str, list[int]] = Field(default_factory=dict)
    sarva: list[int] = Field(default_factory=list)
    total: int = 0


class PrastaraResult(BaseModel):
    """Prastara (expanded) Ashtakavarga for a single planet — BPHS Ch.68.

    Shows WHICH of the 8 sources (7 planets + Lagna) contributed each bindu
    point in the Bhinnashtakavarga, per sign. This is the detailed breakdown
    behind the aggregated BAV counts.

    Attributes:
        planet: The target planet (Sun … Saturn).
        contributors: 12-element list (one per sign, Aries-first). Each
            element is a list of source names that contributed a bindu point
            in that sign (subset of Sun, Moon, Mars, Mercury, Jupiter, Venus,
            Saturn, Lagna).
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    contributors: list[list[str]] = Field(default_factory=list)


class KakshaResult(BaseModel):
    """Kaksha (sub-division) of a planetary longitude within a sign — BPHS Ch.69.

    Each sign (30°) is divided into 8 Kakshas of 3°45' each. The Kakshas are
    lorded in order by: Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon, Lagna.

    When a transit planet is in a Kaksha whose lord contributed a bindu point
    in that sign's BAV for that planet, the transit gives good results;
    otherwise poor results.

    Attributes:
        longitude: Input absolute longitude (0-360).
        sign_index: Sign index 0-11 of the input longitude.
        sign: Vedic sign name.
        sign_en: English sign name.
        degree_in_sign: Degree within sign (0-30).
        kaksha_number: Kaksha number 1-8 within the sign.
        kaksha_lord: Lord of this Kaksha (Saturn/Jupiter/Mars/Sun/Venus/Mercury/Moon/Lagna).
        kaksha_start: Start degree of this Kaksha within the sign.
        kaksha_end: End degree of this Kaksha within the sign.
    """

    model_config = ConfigDict(frozen=True)

    longitude: float = Field(ge=0, lt=360)
    sign_index: int = Field(ge=0, le=11)
    sign: str
    sign_en: str
    degree_in_sign: float = Field(ge=0, lt=30)
    kaksha_number: int = Field(ge=1, le=8)
    kaksha_lord: str
    kaksha_start: float = Field(ge=0, lt=30)
    kaksha_end: float = Field(gt=0, le=30)


class ShodhanaResult(BaseModel):
    """Shodhana (purification) reduction result — BPHS Ch.71.

    Holds the output of applying both Trikona Shodhana and Ekadhipatya
    Shodhana to an AshtakavargaResult.  The reduced tables remove the
    "base level" that repeats across trikona groups and the redundancy
    introduced by dual-ruled signs, leaving only differential strength.

    Attributes:
        reduced_bhinna: Per-planet BAV after Trikona Shodhana only.
                        Keys are planet names (Sun…Saturn); values are
                        12-element lists (Aries-first), all ≥ 0.
        trikona_sarva:  Sarvashtakavarga after Trikona Shodhana (before
                        Ekadhipatya).  12 non-negative integers.
        reduced_sarva:  Sarvashtakavarga after both reductions.  12
                        non-negative integers, with one sign in every
                        dual-owned pair reduced to 0.
    """

    model_config = ConfigDict(frozen=True)

    reduced_bhinna: dict[str, list[int]] = Field(default_factory=dict)
    trikona_sarva: list[int] = Field(default_factory=list)
    reduced_sarva: list[int] = Field(default_factory=list)


class ShodhyaPindaResult(BaseModel):
    """Shodhya Pinda score for a single planet — BPHS Ch.71.

    Shodhya Pinda = Rasi Pinda + Graha Pinda, computed from the planet's
    Trikona-reduced BAV.  It gives a single numerical strength indicator
    that combines sign-based and planet-based weighting.

    Attributes:
        planet:       Planet name (Sun … Saturn).
        rasi_pinda:   sum(reduced_bindu[sign] * RASI_GUNAKARA[sign]).
        graha_pinda:  GRAHA_GUNAKARA[planet] * sum(reduced_bindu[sign]).
        shodhya_pinda: rasi_pinda + graha_pinda.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    rasi_pinda: int = Field(ge=0)
    graha_pinda: int = Field(ge=0)
    shodhya_pinda: int = Field(ge=0)
