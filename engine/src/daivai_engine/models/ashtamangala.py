"""Domain models for Ashtamangala Prashna (Kerala horary tradition)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PrashnaClassification(BaseModel):
    """Classification of a Prashna query by Deva Prashna categories.

    Maps a query type to its cosmic nature (dharma/artha/kama/moksha),
    the relevant primary house, and the natural significator planet.
    Source: Prashna Marga, Kerala Deva Prashna tradition.
    """

    model_config = ConfigDict(frozen=True)

    query_type: str
    primary_house: int
    karaka: str  # Natural significator planet
    deva_category: str  # dharma / artha / kama / moksha
    nature: str  # sattvik / rajasik / tamasik
    description: str


class AroodhaResult(BaseModel):
    """Aroodha Pada (worldly image) computation for a horary query.

    The Aroodha of the relevant house reveals the visible, external
    manifestation of the queried matter. A strong Aroodha lord indicates
    a favorable public/worldly outcome.
    Source: Jaimini Upadesha Sutras 1.2.14-15, Prashna Marga Ch.2.
    """

    model_config = ConfigDict(frozen=True)

    house: int
    aroodha_sign_index: int
    aroodha_sign: str
    aroodha_lord: str
    lord_house: int
    is_strong: bool
    reasoning: str


class MangalaAssessment(BaseModel):
    """Assessment of one of the 8 Mangala Dravyas (auspicious objects).

    Each Dravya is ruled by a planet; favorability depends on that planet's
    placement and dignity in the Prashna chart.
    Source: Prashna Marga Ch.7, Kerala Ashtamangala Deva Prashna.
    """

    model_config = ConfigDict(frozen=True)

    dravya: str  # Sanskrit name
    dravya_en: str  # English name
    planet: str
    signification: str
    is_favorable: bool
    planet_house: int
    planet_dignity: str
    reason: str


class SphutuResult(BaseModel):
    """Composite sensitive points for Ashtamangala Prashna.

    Each Sphuta synthesizes multiple chart factors into a single sensitive
    longitude. The sign and house of each Sphuta indicates the domain most
    activated by the query at the moment of asking.

    Formulas (Prashna Marga Ch.3 / Kerala tradition):
      Trisphuta    = Lagna + Moon + Gulika         (mod 360)
      Chatusphuta  = Lagna + Moon + Sun + Gulika   (mod 360)
      Panchasphuta = Lagna + Moon + Sun + Jupiter + Gulika (mod 360)
      Pranapada    = Lagna + Moon - Sun            (mod 360)
    """

    model_config = ConfigDict(frozen=True)

    trisphuta: float
    chatusphuta: float
    panchasphuta: float
    pranapada: float  # Life-breath point (Lot of Fortune in horary usage)
    trisphuta_sign_index: int
    chatusphuta_sign_index: int
    panchasphuta_sign_index: int
    pranapada_sign_index: int
    trisphuta_sign: str
    chatusphuta_sign: str
    panchasphuta_sign: str
    pranapada_sign: str


class AshtamangalaResult(BaseModel):
    """Complete Ashtamangala Prashna analysis result.

    Integrates all Kerala horary techniques: Deva Prashna classification,
    Aroodha, the 8 Mangala Dravyas, composite Sphutas, and Swara analysis
    into a single coherent verdict with confidence grading.
    """

    model_config = ConfigDict(frozen=True)

    query_type: str
    classification: PrashnaClassification
    aroodha: AroodhaResult
    most_favorable_dravya: MangalaAssessment
    all_dravyas: list[MangalaAssessment]
    sphuta: SphutuResult
    swara_analysis: str
    answer: str  # YES / NO / MAYBE
    confidence: str  # high / medium / low
    reasoning: str
    positive_score: int
    negative_score: int
