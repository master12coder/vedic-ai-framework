"""Domain models for complete gem therapy recommendations.

Covers stone selection, weight, finger, metal, wearing muhurta, contraindication
matrix, gem activation (Pran Pratishtha), substitute stones, and quality specs.
All models are engine-layer — no LLM or product dependencies.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GemQualitySpec(BaseModel):
    """Quality requirements for a gemstone to be astrologically effective.

    Defines minimum weight, preferred origins, color, clarity standards,
    and conditions that disqualify a stone from therapeutic use.
    """

    model_config = ConfigDict(frozen=True)

    color: str
    clarity: str
    min_weight_ratti: float = Field(ge=0.5)
    min_weight_carat: float = Field(ge=0.4)
    origin_preferred: list[str]
    origin_acceptable: list[str]
    avoid_if: list[str]
    treatment_caution: list[str]


class GemUpratna(BaseModel):
    """Substitute (upratna) stone for when the primary gem is unaffordable or unavailable.

    Provides cheaper alternatives with their effectiveness rating, color guidelines,
    and cautions about their differences from the primary stone.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    name_hi: str
    effectiveness_percent: int = Field(ge=0, le=100)
    when_to_prefer: list[str]
    color_match: str
    metal: str
    caution: str


class GemActivation(BaseModel):
    """Pran Pratishtha (gem activation) ritual data.

    Contains the planetary-specific details needed to perform the activation
    ritual before wearing a gemstone for the first time.
    """

    model_config = ConfigDict(frozen=True)

    cloth_color: str
    incense: str
    flower: str
    diya_type: str
    offering: str
    mantra: str
    mantra_count: int = Field(ge=1)
    activation_steps: list[str]  # Brief step list for the planet


class WearingMuhurta(BaseModel):
    """An auspicious date and time window for wearing a gemstone.

    Scored by alignment of weekday, nakshatra, tithi, and paksha.
    Higher score = more auspicious. Includes reasons for the score.
    """

    model_config = ConfigDict(frozen=True)

    date: str  # DD/MM/YYYY
    vara: str  # Weekday name
    nakshatra: str
    tithi_name: str
    paksha: str  # Shukla/Krishna
    score: float = Field(ge=0.0)
    reasons: list[str]
    hora_timing: str  # When to wear: "First Sun hora after sunrise"
    is_trial_date: bool = False  # True if this is day 1 of Blue Sapphire trial


class ContraindicationPair(BaseModel):
    """A conflicting stone pair that should not be worn together.

    Contains the planet pair, their stones, severity level, and the
    traditional reasoning for the prohibition.
    """

    model_config = ConfigDict(frozen=True)

    planets: list[str]
    stones: list[str]
    severity: str  # "absolute" / "high" / "moderate" / "low"
    reason: str


class ContraindicationResult(BaseModel):
    """Result of checking a combination of gems for contraindications.

    Lists any conflicting pairs found and confirms which combinations are safe.
    """

    model_config = ConfigDict(frozen=True)

    gems_checked: list[str]
    conflicts: list[ContraindicationPair]
    safe_pairs: list[tuple[str, str]]
    has_absolute_conflict: bool
    summary: str


class GemTherapyRecommendation(BaseModel):
    """Complete professional gem therapy recommendation for one planet's stone.

    Integrates lordship-based status with full therapy data: weight, finger,
    metal, wearing day, auspicious nakshatra, mantra, substitute stone,
    quality specs, activation ritual, and removal conditions.
    This is the complete pandit-grade recommendation object.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    stone_name: str
    stone_name_hi: str
    status: str  # "recommended" / "test_with_caution" / "prohibited" / "neutral"
    lordship_reason: str  # Why recommended/prohibited from lordship rules

    # Wearing protocol
    finger: str
    hand: str
    metal: str
    day: str  # Planet's weekday
    hora: str  # Best planetary hour
    mantra: str
    mantra_count: int = Field(ge=1)

    # Weight (from gemstone_logic.yaml weight_formula string)
    weight_formula: str

    # Substitute stone
    upratna: GemUpratna | None = None

    # Quality requirements
    quality: GemQualitySpec | None = None

    # Activation ritual
    activation: GemActivation | None = None

    # Removal conditions (universal + stone-specific)
    removal_conditions: list[str]

    # Special precautions (e.g., Blue Sapphire 3-day trial)
    special_precaution: str | None = None

    # If prohibited, reason (truncated for display)
    prohibition_reason: str | None = None
