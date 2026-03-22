"""Domain models for Medical Astrology (Vaidya Jyotish) analysis."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BodyPartVulnerability(BaseModel):
    """Vulnerability assessment for a body area from Kala Purusha sign mapping.

    Each of the 12 signs corresponds to a body zone of the Cosmic Person.
    Afflictions to a sign (malefics placed or aspecting) indicate potential
    health issues in the corresponding body area.

    Source: BPHS Ch.7 Kala Purusha Adhyaya v.8-10.
    """

    model_config = ConfigDict(frozen=True)

    sign_index: int = Field(ge=0, le=11)
    sign: str
    sign_hi: str
    body_parts: list[str]
    body_parts_hi: list[str]
    afflicting_planets: list[str]
    vulnerability_level: str  # "high", "moderate", "low", "none"
    reason: str


class TridoshaBalance(BaseModel):
    """Ayurvedic Tridosha (three humors) balance computed from birth chart.

    Derives the Vata (air/ether), Pitta (fire), and Kapha (water/earth)
    constitution from planetary placements, dignity, and strength.

    Source: K.S. Charak "Ayurvedic Astrology" Ch.2;
            Jyotish-Ayurveda synthesis texts.
    """

    model_config = ConfigDict(frozen=True)

    vata_score: float = Field(ge=0.0)
    pitta_score: float = Field(ge=0.0)
    kapha_score: float = Field(ge=0.0)
    vata_percentage: float = Field(ge=0.0, le=100.0)
    pitta_percentage: float = Field(ge=0.0, le=100.0)
    kapha_percentage: float = Field(ge=0.0, le=100.0)
    dominant_dosha: str  # "Vata", "Pitta", "Kapha"
    secondary_dosha: str  # "Vata", "Pitta", "Kapha", or "None"
    vata_planets: list[str]  # Planets contributing to Vata
    pitta_planets: list[str]  # Planets contributing to Pitta
    kapha_planets: list[str]  # Planets contributing to Kapha
    constitution_type: str  # e.g. "Vata-Pitta", "Tridoshic", "Kapha"
    imbalance_risk: str  # "high", "moderate", "low"
    description: str


class DiseaseYoga(BaseModel):
    """A disease-indicating planetary combination (yoga) from the birth chart.

    Represents a specific planetary condition that classical Jyotish texts
    associate with health vulnerabilities or disease risk in particular body systems.

    Source: BPHS Ch.68-70 Arishta/Roga Adhyaya;
            Saravali Ch.6; Phaladeepika Ch.6.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    name_hindi: str
    is_present: bool
    severity: str  # "high", "moderate", "low", "none"
    planets_involved: list[str]
    houses_involved: list[int]
    body_system_affected: str
    disease_indicated: str
    description: str
    source: str


class SphutalResult(BaseModel):
    """Prana / Deha / Mrityu Sphuta — three sensitive points for medical prashna.

    These longitude points are used in Roga Prashna (medical horary) to assess
    vitality, body affliction risk, and longevity stress respectively.

    Formulas (all mod 360):
      Prana Sphuta  = Lagna + Sun + Moon
      Deha Sphuta   = Lagna + Mars + Moon
      Mrityu Sphuta = Lagna + Saturn + Moon

    Source: Hora Sara Ch.8 v.4-6; Jataka Parijata Medical Ch.;
            Sarvartha Chintamani Roga Adhyaya.
    """

    model_config = ConfigDict(frozen=True)

    prana_sphuta: float = Field(ge=0.0, lt=360.0)
    prana_sphuta_sign: str
    prana_sphuta_sign_index: int = Field(ge=0, le=11)
    prana_sphuta_nakshatra: str

    deha_sphuta: float = Field(ge=0.0, lt=360.0)
    deha_sphuta_sign: str
    deha_sphuta_sign_index: int = Field(ge=0, le=11)
    deha_sphuta_nakshatra: str

    mrityu_sphuta: float = Field(ge=0.0, lt=360.0)
    mrityu_sphuta_sign: str
    mrityu_sphuta_sign_index: int = Field(ge=0, le=11)
    mrityu_sphuta_nakshatra: str

    prana_deha_concordance: str  # "favorable", "neutral", "challenging"
    vitality_assessment: str
    interpretation: str


class HealthAnalysis(BaseModel):
    """Complete Vaidya Jyotish (medical astrology) analysis from a birth chart.

    Combines Kala Purusha body mapping, Tridosha balance assessment, disease
    yoga detection, and Trisphuta calculation to provide a holistic picture
    of the native's constitutional health profile and disease vulnerabilities.
    """

    model_config = ConfigDict(frozen=True)

    body_part_vulnerabilities: list[BodyPartVulnerability]
    disease_yogas: list[DiseaseYoga]
    tridosha_balance: TridoshaBalance
    sphuta_result: SphutalResult
    health_house_analysis: dict[int, list[str]]  # {6: [...], 8: [...], 12: [...]}
    dominant_health_concerns: list[str]
    health_summary: str
