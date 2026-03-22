"""Domain models for Mundane Astrology (Medini Jyotish)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MundaneHouseSignification(BaseModel):
    """Significations of a house in a mundane (national/world) chart."""

    model_config = ConfigDict(frozen=True)

    house: int = Field(ge=1, le=12)
    rules: list[str]  # domains this house governs (economy, military, etc.)
    karaka_planets: list[str]  # natural significators for this house


class DisasterYoga(BaseModel):
    """A disaster yoga detected in a mundane chart (from Brihat Samhita)."""

    model_config = ConfigDict(frozen=False)

    name: str
    description: str
    severity: str  # "severe" | "moderate" | "mild"
    affected_domains: list[str]
    planets_involved: list[str]
    source: str = "Brihat Samhita"


class EclipseEffect(BaseModel):
    """Effects of a solar or lunar eclipse on a nation/region."""

    model_config = ConfigDict(frozen=False)

    eclipse_type: str  # "solar" | "lunar"
    eclipse_date: str  # ISO date string
    eclipse_longitude: float = Field(ge=0, lt=360)  # sidereal longitude of eclipse
    eclipse_sign_index: int = Field(ge=0, le=11)
    eclipse_sign: str
    nakshatra: str
    nakshatra_lord: str
    affected_regions: list[str]  # countries/regions per Brihat Samhita naksshatra list
    predicted_effects: list[str]
    duration_months: int = Field(ge=1, le=12)  # duration of effects in months
    severity: str  # "severe" | "moderate" | "mild"


class JupiterSaturnCycle(BaseModel):
    """Analysis of a Jupiter-Saturn conjunction cycle (Mahayuga cycle)."""

    model_config = ConfigDict(frozen=False)

    conjunction_date: str  # ISO date of exact conjunction
    conjunction_longitude: float = Field(ge=0, lt=360)
    conjunction_sign_index: int = Field(ge=0, le=11)
    conjunction_sign: str
    conjunction_element: str  # Fire / Earth / Air / Water
    cycle_type: str  # "grand_mutation" | "regular" | "superior"
    cycle_years: int  # ~20 years per conjunction
    predicted_themes: list[str]
    geopolitical_effects: list[str]
    economic_effects: list[str]
    social_effects: list[str]


class IngressChart(BaseModel):
    """Mesha Sankranti or seasonal ingress chart for mundane prediction."""

    model_config = ConfigDict(frozen=False)

    ingress_type: (
        str  # "mesha_sankranti" | "libra_ingress" | "cancer_ingress" | "capricorn_ingress"
    )
    ingress_date: str  # ISO date string
    ingress_longitude: float = Field(ge=0, lt=360)  # Sun's exact longitude at ingress
    lagna_sign_index: int = Field(ge=0, le=11)
    lagna_sign: str
    lagna_lord: str
    sun_sign_index: int = Field(ge=0, le=11)
    sun_sign: str
    moon_sign_index: int = Field(ge=0, le=11)
    moon_sign: str
    ruling_planet: str  # planet that rules this ingress period
    planetary_positions: dict[str, int]  # planet → sign_index


class MundaneChartAnalysis(BaseModel):
    """Complete mundane chart analysis for a country or the world."""

    model_config = ConfigDict(frozen=False)

    chart_type: str  # "country_foundation" | "ingress" | "eclipse" | "conjunction"
    chart_date: str
    country: str | None = None
    lagna_sign: str
    lagna_lord: str
    house_analysis: dict[int, list[str]]  # house → list of predictions
    disaster_yogas: list[DisasterYoga]
    afflicted_houses: list[int]
    benefic_houses: list[int]
    dominant_planets: list[str]
    weak_planets: list[str]
    predictions: list[str]
    severity_score: float = Field(ge=0.0, le=10.0)  # overall severity 0-10
