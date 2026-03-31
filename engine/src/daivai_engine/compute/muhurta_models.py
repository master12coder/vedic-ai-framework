"""Muhurta data models — dosha, shuddhi, and scoring results.

Pydantic v2 models used by muhurta_engine.py and downstream consumers.

Source: Muhurta Chintamani, BPHS Muhurta chapter.
"""

from __future__ import annotations

from pydantic import BaseModel


class MuhurtaDosha(BaseModel):
    """A single dosha (flaw) detected in a muhurta."""

    name: str
    name_hi: str
    is_present: bool
    severity: str  # mild / moderate / severe
    description: str


class PanchangaShuddhi(BaseModel):
    """Classical 5-fold Panchanga Shuddhi (purity) assessment.

    All five limbs (Tithi, Vara, Nakshatra, Yoga, Karana) must be pure
    for a muhurta to be classically acceptable. Partial purity = partially
    acceptable with remedies.

    Source: Muhurta Chintamani Ch.1.
    """

    tithi_shuddha: bool
    vara_shuddha: bool
    nakshatra_shuddha: bool
    yoga_shuddha: bool
    karana_shuddha: bool
    shuddha_count: int  # 0-5
    is_fully_shuddha: bool  # all 5 pure
    summary: str  # e.g. "4/5 pure: Nakshatra impure (Gandanta)"


class LagnaShuddhi(BaseModel):
    """Lagna (ascendant) purity for the muhurta moment.

    The rising sign at the muhurta time must match the event type and
    be free from malefic influence.

    Source: Muhurta Chintamani Ch.2.
    """

    lagna_sign_index: int
    lagna_sign: str
    lagna_type: str  # movable / fixed / dual
    matches_event_type: bool  # Does lagna type suit the event?
    malefic_in_8th: bool  # Malefic in 8th from lagna = strongly inauspicious
    lagna_lord_strong: bool  # Lagna lord in kendra/trikona from lagna
    is_shuddha: bool  # All conditions satisfied
    note: str


class MuhurtaScore(BaseModel):
    """Comprehensive muhurta scoring for a specific datetime and event type."""

    event_type: str
    datetime_str: str
    score: int  # 0-100
    doshas: list[MuhurtaDosha]
    doshas_present: int
    doshas_absent: int
    panchanga_shuddhi: PanchangaShuddhi | None = None
    lagna_shuddhi: LagnaShuddhi | None = None
    is_auspicious: bool  # score >= 70
    summary: str
