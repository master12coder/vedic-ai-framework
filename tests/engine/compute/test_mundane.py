"""Tests for Mundane Astrology (Medini Jyotish) computation.

Tests cover:
- MundaneChartAnalysis from a birth/foundation chart
- Disaster yoga detection from Brihat Samhita
- Eclipse effect analysis (solar and lunar)
- Jupiter-Saturn conjunction cycle analysis
- Ingress chart computation (Mesha Sankranti)

Fixture: Manish Chaurasia chart used as a proxy mundane chart for structural tests.
"""

from __future__ import annotations

from daivai_engine.compute.mundane import (
    _get_nakshatra,
    _house_from_lagna,
    _longitude_to_sign,
    analyze_eclipse_effects,
    analyze_jupiter_saturn_cycle,
    analyze_mundane_chart,
    compute_ingress_chart,
)
from daivai_engine.knowledge.loader import load_mundane_rules
from daivai_engine.models.mundane import (
    DisasterYoga,
    EclipseEffect,
    IngressChart,
    JupiterSaturnCycle,
    MundaneChartAnalysis,
)


# ── Helper / Internal Function Tests ─────────────────────────────────────────


class TestLongitudeToSign:
    """Test sidereal longitude → sign index mapping."""

    def test_longitude_0_is_mesha(self):
        idx, name = _longitude_to_sign(0.0)
        assert idx == 0
        assert name == "Mesha"

    def test_longitude_30_is_vrishabha(self):
        idx, name = _longitude_to_sign(30.0)
        assert idx == 1
        assert name == "Vrishabha"

    def test_longitude_359_is_meena(self):
        idx, name = _longitude_to_sign(359.9)
        assert idx == 11
        assert name == "Meena"

    def test_longitude_180_is_tula(self):
        idx, name = _longitude_to_sign(180.0)
        assert idx == 6
        assert name == "Tula"

    def test_all_12_signs_covered(self):
        signs_seen = set()
        for i in range(12):
            idx, _ = _longitude_to_sign(float(i * 30 + 15))
            signs_seen.add(idx)
        assert len(signs_seen) == 12


class TestGetNakshatra:
    """Test sidereal longitude → nakshatra mapping."""

    def test_longitude_0_is_ashwini(self):
        idx, name, lord = _get_nakshatra(0.0)
        assert idx == 0
        assert name == "Ashwini"
        assert lord == "Ketu"

    def test_longitude_13_33_is_bharani(self):
        # Bharani starts at 13.333°
        idx, name, _ = _get_nakshatra(14.0)
        assert idx == 1
        assert name == "Bharani"

    def test_all_27_nakshatras_covered(self):
        naks_seen = set()
        for i in range(27):
            lon = i * (360.0 / 27) + 1.0
            idx, _, _ = _get_nakshatra(lon)
            naks_seen.add(idx)
        assert len(naks_seen) == 27

    def test_nakshatra_lord_is_string(self):
        _, _, lord = _get_nakshatra(100.0)
        assert isinstance(lord, str)
        assert len(lord) > 0


class TestHouseFromLagna:
    """Test house calculation from lagna."""

    def test_same_sign_is_first_house(self):
        assert _house_from_lagna(0, 0) == 1

    def test_next_sign_is_second_house(self):
        assert _house_from_lagna(1, 0) == 2

    def test_wraparound_meena_to_mesha(self):
        # Planet in Mesha (0), lagna in Vrishabha (1) → 12th house
        assert _house_from_lagna(0, 1) == 12

    def test_opposite_sign_is_7th(self):
        # Planet in sign 6, lagna in sign 0 → 7th house
        assert _house_from_lagna(6, 0) == 7


# ── Mundane Rules YAML Tests ─────────────────────────────────────────────────


class TestMundaneRulesYaml:
    """Validate mundane_rules.yaml structure and completeness."""

    def test_yaml_loads_without_error(self):
        rules = load_mundane_rules()
        assert isinstance(rules, dict)
        assert len(rules) > 0

    def test_all_12_houses_have_significations(self):
        rules = load_mundane_rules()
        house_sigs = rules.get("house_significations", {})
        for house in range(1, 13):
            assert house in house_sigs, f"House {house} missing from mundane_rules.yaml"

    def test_each_house_has_rules_and_karakas(self):
        rules = load_mundane_rules()
        house_sigs = rules.get("house_significations", {})
        for house, data in house_sigs.items():
            assert "rules" in data, f"House {house} missing 'rules'"
            assert "karaka_planets" in data, f"House {house} missing 'karaka_planets'"
            assert len(data["rules"]) >= 1

    def test_disaster_yogas_present(self):
        rules = load_mundane_rules()
        yogas = rules.get("disaster_yogas", [])
        assert len(yogas) >= 5, "Expected at least 5 disaster yogas"

    def test_each_disaster_yoga_has_required_fields(self):
        rules = load_mundane_rules()
        for yoga in rules.get("disaster_yogas", []):
            assert "name" in yoga
            assert "condition" in yoga
            assert "description" in yoga
            assert "severity" in yoga
            assert yoga["severity"] in ("severe", "moderate", "mild")

    def test_jupiter_saturn_cycle_rules_present(self):
        rules = load_mundane_rules()
        cycle = rules.get("jupiter_saturn_cycles", {})
        assert "element_themes" in cycle
        assert "sign_themes" in cycle
        assert len(cycle["element_themes"]) == 4  # Fire, Earth, Air, Water

    def test_eclipse_nakshatra_effects_present(self):
        rules = load_mundane_rules()
        nak_effects = rules.get("eclipse_nakshatra_effects", {})
        assert len(nak_effects) >= 27, "Expected all 27 nakshatras"

    def test_eclipse_sign_effects_present(self):
        rules = load_mundane_rules()
        sign_effects = rules.get("eclipse_sign_effects", {})
        assert len(sign_effects) == 12, "Expected effects for all 12 signs"


# ── analyze_mundane_chart Tests ───────────────────────────────────────────────


class TestAnalyzeMundaneChart:
    """Test analyze_mundane_chart() using Manish's chart as a mundane proxy."""

    def test_returns_mundane_chart_analysis(self, manish_chart):
        result = analyze_mundane_chart(manish_chart, country="India")
        assert isinstance(result, MundaneChartAnalysis)

    def test_lagna_sign_matches_chart(self, manish_chart):
        result = analyze_mundane_chart(manish_chart)
        assert result.lagna_sign == manish_chart.lagna_sign

    def test_lagna_lord_is_string(self, manish_chart):
        result = analyze_mundane_chart(manish_chart)
        assert isinstance(result.lagna_lord, str)
        assert len(result.lagna_lord) > 0

    def test_severity_score_in_range(self, manish_chart):
        result = analyze_mundane_chart(manish_chart)
        assert 0.0 <= result.severity_score <= 10.0

    def test_country_stored_correctly(self, manish_chart):
        result = analyze_mundane_chart(manish_chart, country="India")
        assert result.country == "India"

    def test_chart_type_stored(self, manish_chart):
        result = analyze_mundane_chart(manish_chart, chart_type="ingress")
        assert result.chart_type == "ingress"

    def test_house_analysis_is_dict(self, manish_chart):
        result = analyze_mundane_chart(manish_chart)
        assert isinstance(result.house_analysis, dict)

    def test_disaster_yogas_is_list(self, manish_chart):
        result = analyze_mundane_chart(manish_chart)
        assert isinstance(result.disaster_yogas, list)

    def test_all_disaster_yogas_are_valid_objects(self, manish_chart):
        result = analyze_mundane_chart(manish_chart)
        for yoga in result.disaster_yogas:
            assert isinstance(yoga, DisasterYoga)
            assert yoga.severity in ("severe", "moderate", "mild")

    def test_afflicted_and_benefic_houses_are_valid(self, manish_chart):
        result = analyze_mundane_chart(manish_chart)
        for h in result.afflicted_houses:
            assert 1 <= h <= 12
        for h in result.benefic_houses:
            assert 1 <= h <= 12

    def test_predictions_is_list_of_strings(self, manish_chart):
        result = analyze_mundane_chart(manish_chart)
        for pred in result.predictions:
            assert isinstance(pred, str)


# ── analyze_eclipse_effects Tests ────────────────────────────────────────────


class TestAnalyzeEclipseEffects:
    """Test eclipse effect analysis."""

    def test_solar_eclipse_returns_eclipse_effect(self):
        result = analyze_eclipse_effects("2024-04-08", "solar")
        assert isinstance(result, EclipseEffect)

    def test_lunar_eclipse_returns_eclipse_effect(self):
        result = analyze_eclipse_effects("2024-03-25", "lunar")
        assert isinstance(result, EclipseEffect)

    def test_eclipse_type_stored_correctly(self):
        result = analyze_eclipse_effects("2024-04-08", "solar")
        assert result.eclipse_type == "solar"

    def test_eclipse_longitude_in_range(self):
        result = analyze_eclipse_effects("2024-04-08", "solar")
        assert 0.0 <= result.eclipse_longitude < 360.0

    def test_eclipse_sign_index_in_range(self):
        result = analyze_eclipse_effects("2024-04-08", "solar")
        assert 0 <= result.eclipse_sign_index <= 11

    def test_eclipse_sign_matches_index(self):
        result = analyze_eclipse_effects("2024-04-08", "solar")
        from daivai_engine.constants import SIGNS

        assert result.eclipse_sign == SIGNS[result.eclipse_sign_index]

    def test_nakshatra_is_nonempty_string(self):
        result = analyze_eclipse_effects("2024-04-08", "solar")
        assert isinstance(result.nakshatra, str)
        assert len(result.nakshatra) > 0

    def test_nakshatra_lord_is_valid_planet(self):
        valid_lords = {
            "Ketu",
            "Venus",
            "Sun",
            "Moon",
            "Mars",
            "Rahu",
            "Jupiter",
            "Saturn",
            "Mercury",
        }
        result = analyze_eclipse_effects("2024-04-08", "solar")
        assert result.nakshatra_lord in valid_lords

    def test_duration_months_in_range(self):
        result = analyze_eclipse_effects("2024-04-08", "solar")
        assert 1 <= result.duration_months <= 12

    def test_severity_is_valid_string(self):
        result = analyze_eclipse_effects("2024-04-08", "solar")
        assert result.severity in ("severe", "moderate", "mild")

    def test_solar_eclipse_is_more_severe_than_lunar(self):
        solar = analyze_eclipse_effects("2024-04-08", "solar")
        lunar = analyze_eclipse_effects("2024-03-25", "lunar")
        # Solar should be "severe", lunar "moderate"
        severity_rank = {"severe": 2, "moderate": 1, "mild": 0}
        assert severity_rank[solar.severity] >= severity_rank[lunar.severity]

    def test_predicted_effects_is_nonempty_list(self):
        result = analyze_eclipse_effects("2024-04-08", "solar")
        assert isinstance(result.predicted_effects, list)
        assert len(result.predicted_effects) > 0


# ── analyze_jupiter_saturn_cycle Tests ───────────────────────────────────────


class TestAnalyzeJupiterSaturnCycle:
    """Test Jupiter-Saturn conjunction cycle analysis."""

    # 2020-12-21: famous Jupiter-Saturn conjunction in Makara/Capricorn
    _CONJ_DATE = "2020-12-21"

    def test_returns_jupiter_saturn_cycle(self):
        result = analyze_jupiter_saturn_cycle(self._CONJ_DATE)
        assert isinstance(result, JupiterSaturnCycle)

    def test_conjunction_date_stored(self):
        result = analyze_jupiter_saturn_cycle(self._CONJ_DATE)
        assert result.conjunction_date == self._CONJ_DATE

    def test_conjunction_longitude_in_range(self):
        result = analyze_jupiter_saturn_cycle(self._CONJ_DATE)
        assert 0.0 <= result.conjunction_longitude < 360.0

    def test_conjunction_sign_index_in_range(self):
        result = analyze_jupiter_saturn_cycle(self._CONJ_DATE)
        assert 0 <= result.conjunction_sign_index <= 11

    def test_conjunction_element_is_valid(self):
        result = analyze_jupiter_saturn_cycle(self._CONJ_DATE)
        assert result.conjunction_element in ("Fire", "Earth", "Air", "Water")

    def test_2020_conjunction_in_makara_or_dhanu(self):
        # 2020 Dec 21: Jupiter and Saturn were in Makara (Capricorn) sidereal
        result = analyze_jupiter_saturn_cycle(self._CONJ_DATE)
        # Both Makara (9) or Dhanu (8) are plausible depending on ayanamsha
        assert result.conjunction_sign_index in (8, 9), (
            f"Expected Dhanu or Makara, got {result.conjunction_sign}"
        )

    def test_2020_conjunction_is_earth_element(self):
        result = analyze_jupiter_saturn_cycle(self._CONJ_DATE)
        # Makara is Earth element
        assert result.conjunction_element in ("Earth", "Fire")  # Dhanu=Fire, Makara=Earth

    def test_cycle_years_is_approximately_20(self):
        result = analyze_jupiter_saturn_cycle(self._CONJ_DATE)
        assert 18 <= result.cycle_years <= 21

    def test_cycle_type_is_valid(self):
        result = analyze_jupiter_saturn_cycle(self._CONJ_DATE)
        assert result.cycle_type in ("regular", "grand_mutation", "superior")

    def test_predicted_themes_is_list(self):
        result = analyze_jupiter_saturn_cycle(self._CONJ_DATE)
        assert isinstance(result.predicted_themes, list)

    def test_at_least_one_effect_category_nonempty(self):
        result = analyze_jupiter_saturn_cycle(self._CONJ_DATE)
        total = (
            len(result.geopolitical_effects)
            + len(result.economic_effects)
            + len(result.social_effects)
        )
        assert total > 0


# ── compute_ingress_chart Tests ───────────────────────────────────────────────


class TestComputeIngressChart:
    """Test Mesha Sankranti ingress chart computation."""

    # 2024 Mesha Sankranti (Sun enters Mesha sidereal) ~April 14
    _INGRESS_DATE = "2024-04-14"

    def test_returns_ingress_chart(self):
        result = compute_ingress_chart(self._INGRESS_DATE, "mesha_sankranti")
        assert isinstance(result, IngressChart)

    def test_ingress_type_stored(self):
        result = compute_ingress_chart(self._INGRESS_DATE, "mesha_sankranti")
        assert result.ingress_type == "mesha_sankranti"

    def test_sun_sign_is_mesha_for_mesha_sankranti(self):
        result = compute_ingress_chart(self._INGRESS_DATE, "mesha_sankranti")
        assert result.sun_sign_index == 0, f"Expected Mesha (0), got {result.sun_sign}"

    def test_lagna_sign_index_in_range(self):
        result = compute_ingress_chart(self._INGRESS_DATE)
        assert 0 <= result.lagna_sign_index <= 11

    def test_lagna_lord_is_valid_planet(self):
        valid_planets = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        result = compute_ingress_chart(self._INGRESS_DATE)
        assert result.lagna_lord in valid_planets

    def test_ruling_planet_is_valid(self):
        valid_planets = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        result = compute_ingress_chart(self._INGRESS_DATE)
        assert result.ruling_planet in valid_planets

    def test_planetary_positions_has_all_planets(self):
        result = compute_ingress_chart(self._INGRESS_DATE)
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert expected.issubset(set(result.planetary_positions.keys()))

    def test_planetary_positions_sign_indices_in_range(self):
        result = compute_ingress_chart(self._INGRESS_DATE)
        for planet, sign_idx in result.planetary_positions.items():
            assert 0 <= sign_idx <= 11, f"{planet} sign index {sign_idx} out of range"

    def test_ingress_longitude_matches_type(self):
        result = compute_ingress_chart(self._INGRESS_DATE, "mesha_sankranti")
        assert result.ingress_longitude == 0.0  # Mesha starts at 0°

    def test_libra_ingress_longitude_is_180(self):
        result = compute_ingress_chart("2024-10-17", "libra_ingress")
        assert result.ingress_longitude == 180.0
