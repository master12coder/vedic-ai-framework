"""Tests for Gochara (Transit Analysis) — compute/gochara.py.

Covers:
  - Structural validity of GocharaAnalysis output
  - Vedha obstruction rules (no vedha for houses 7/11)
  - Moorthy Nirnaya classification (Poorna/Madhya/Swalpa/Nishphala)
  - Sadesati detection and phase
  - Double transit house detection
  - YAML integrity (108 results, vedha table)
  - Private helper functions
  - Two charts (Manish reference + sample)

Fixture:
  manish_chart: Mithuna lagna, Moon in Rohini Pada 2.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import yaml

from daivai_engine.compute.gochara import (
    _bav_modifier,
    _classify_moorthy,
    _sadesati_intensity,
    _score_to_favorability,
    compute_gochara,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.gochara import (
    Favorability,
    GocharaAnalysis,
    GocharaPlanetResult,
    GocharaVedha,
    MoorthyClass,
)


# ── Shared target date ──────────────────────────────────────────────────────

_DATE = datetime(2026, 3, 22, 12, 0, 0)
_PLANETS_9 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]


# ── YAML integrity ──────────────────────────────────────────────────────────


class TestGocharaYaml:
    """Verify gochara_rules.yaml has the correct structure and content."""

    @pytest.fixture
    def yaml_data(self) -> dict[str, Any]:
        path = (
            Path(__file__).parents[3]
            / "engine"
            / "src"
            / "daivai_engine"
            / "knowledge"
            / "gochara_rules.yaml"
        )
        with open(path) as f:
            return yaml.safe_load(f)

    def test_yaml_loads(self, yaml_data: dict[str, Any]) -> None:
        assert isinstance(yaml_data, dict)

    def test_yaml_has_scores_section(self, yaml_data: dict[str, Any]) -> None:
        assert "scores" in yaml_data

    def test_yaml_has_all_9_planets(self, yaml_data: dict[str, Any]) -> None:
        scores = yaml_data["scores"]
        for planet in _PLANETS_9:
            assert planet in scores, f"{planet} missing from scores"

    def test_yaml_each_planet_has_12_scores(self, yaml_data: dict[str, Any]) -> None:
        for planet, scores in yaml_data["scores"].items():
            assert len(scores) == 12, f"{planet} does not have 12 house scores"

    def test_yaml_scores_in_range(self, yaml_data: dict[str, Any]) -> None:
        for planet, scores in yaml_data["scores"].items():
            for s in scores:
                assert -2 <= s <= 2, f"{planet} score {s} out of range"

    def test_yaml_108_total_results(self, yaml_data: dict[str, Any]) -> None:
        total = sum(len(v) for v in yaml_data["scores"].values())
        assert total == 108, f"Expected 108 results, got {total}"

    def test_yaml_has_results_section(self, yaml_data: dict[str, Any]) -> None:
        assert "results" in yaml_data
        assert len(yaml_data["results"]) == 9

    def test_yaml_has_vedha_pairs(self, yaml_data: dict[str, Any]) -> None:
        assert "vedha_pairs" in yaml_data
        pairs = yaml_data["vedha_pairs"]
        assert 1 in pairs and 5 in pairs  # 1↔5 pair
        assert 7 not in pairs  # house 7 has no vedha
        assert 11 not in pairs  # house 11 has no vedha

    def test_yaml_vedha_pairs_are_symmetric(self, yaml_data: dict[str, Any]) -> None:
        pairs = yaml_data["vedha_pairs"]
        for h, v in pairs.items():
            assert v in pairs, f"Vedha pair missing: {v}→{h}"
            assert pairs[v] == h, f"Vedha not symmetric: {h}↔{v}"

    def test_yaml_no_vedha_houses(self, yaml_data: dict[str, Any]) -> None:
        assert 7 in yaml_data["no_vedha_houses"]
        assert 11 in yaml_data["no_vedha_houses"]

    def test_yaml_moorthy_nirnaya_present(self, yaml_data: dict[str, Any]) -> None:
        mn = yaml_data["moorthy_nirnaya"]
        assert "poorna" in mn
        assert "madhya" in mn
        assert "swalpa" in mn
        assert "nishphala" in mn

    def test_yaml_moorthy_bindus_contiguous(self, yaml_data: dict[str, Any]) -> None:
        mn = yaml_data["moorthy_nirnaya"]
        assert mn["nishphala"]["bindus_min"] == 0
        assert mn["nishphala"]["bindus_max"] == 0
        assert mn["swalpa"]["bindus_min"] == 1
        assert mn["poorna"]["bindus_max"] == 8

    def test_yaml_special_names_present(self, yaml_data: dict[str, Any]) -> None:
        assert "special_names" in yaml_data
        # Sadesati and Kantak Shani must exist
        saturn_specials = yaml_data["special_names"].get("Saturn", {})
        assert 1 in saturn_specials  # Sadesati Peak
        assert 10 in saturn_specials  # Kantak Shani


# ── Model structure ─────────────────────────────────────────────────────────


class TestGocharaModels:
    """Test Pydantic model definitions."""

    def test_moorthy_class_has_4_variants(self) -> None:
        values = {m.value for m in MoorthyClass}
        assert values == {"poorna", "madhya", "swalpa", "nishphala"}

    def test_favorability_has_5_variants(self) -> None:
        values = {f.value for f in Favorability}
        assert values == {
            "very_favorable",
            "favorable",
            "neutral",
            "unfavorable",
            "very_unfavorable",
        }

    def test_gochara_vedha_frozen(self) -> None:
        v = GocharaVedha(vedha_house=5, is_active=False, blocking_planet=None)
        with pytest.raises((TypeError, Exception)):
            v.vedha_house = 6  # type: ignore[misc]

    def test_gochara_planet_result_frozen(self) -> None:
        r = GocharaPlanetResult(
            planet="Saturn",
            transit_sign_index=0,
            transit_sign="Mesha",
            house_from_moon=1,
            gochara_score=-1,
            favorability=Favorability.unfavorable,
            result_text="Test",
            bav_bindus=3,
            moorthy=MoorthyClass.madhya,
            final_score=-1,
        )
        with pytest.raises((TypeError, Exception)):
            r.planet = "Jupiter"  # type: ignore[misc]

    def test_gochara_analysis_frozen(self, manish_chart: ChartData) -> None:
        result = compute_gochara(manish_chart, _DATE)
        with pytest.raises((TypeError, Exception)):
            result.overall_rating = 99  # type: ignore[misc]


# ── Compute function: structural validity ────────────────────────────────────


class TestComputeGochara:
    """Structural tests for compute_gochara() output."""

    @pytest.fixture
    def result(self, manish_chart: ChartData) -> GocharaAnalysis:
        return compute_gochara(manish_chart, _DATE)

    def test_returns_gochara_analysis(self, result: GocharaAnalysis) -> None:
        assert isinstance(result, GocharaAnalysis)

    def test_has_all_9_planets(self, result: GocharaAnalysis) -> None:
        planet_names = [r.planet for r in result.planet_results]
        for p in _PLANETS_9:
            assert p in planet_names, f"{p} missing from planet_results"

    def test_moon_sign_index_valid(self, result: GocharaAnalysis) -> None:
        assert 0 <= result.moon_sign_index <= 11

    def test_moon_sign_non_empty(self, result: GocharaAnalysis) -> None:
        assert len(result.moon_sign) > 0

    def test_date_formatted_correctly(self, result: GocharaAnalysis) -> None:
        assert result.target_date == "22/03/2026"

    def test_chart_name_preserved(self, result: GocharaAnalysis) -> None:
        assert result.chart_name == "Manish Chaurasia"

    def test_overall_rating_in_range(self, result: GocharaAnalysis) -> None:
        assert -10 <= result.overall_rating <= 10

    def test_summary_non_empty(self, result: GocharaAnalysis) -> None:
        assert len(result.summary) > 0

    def test_sadesati_active_is_bool(self, result: GocharaAnalysis) -> None:
        assert isinstance(result.sadesati_active, bool)

    def test_sadesati_phase_valid_when_active(self, result: GocharaAnalysis) -> None:
        if result.sadesati_active:
            assert result.sadesati_phase in ("Rising", "Peak", "Setting")
            assert result.sadesati_intensity in ("mild", "moderate", "severe")

    def test_sadesati_fields_none_when_inactive(self, result: GocharaAnalysis) -> None:
        if not result.sadesati_active:
            assert result.sadesati_phase is None
            assert result.sadesati_intensity is None

    def test_double_transit_houses_in_range(self, result: GocharaAnalysis) -> None:
        for h in result.double_transit_houses:
            assert 1 <= h <= 12

    def test_planet_house_from_moon_in_range(self, result: GocharaAnalysis) -> None:
        for r in result.planet_results:
            assert 1 <= r.house_from_moon <= 12, f"{r.planet} house_from_moon out of range"

    def test_planet_gochara_score_in_range(self, result: GocharaAnalysis) -> None:
        for r in result.planet_results:
            assert -2 <= r.gochara_score <= 2, f"{r.planet} gochara_score out of range"

    def test_planet_bav_bindus_in_range(self, result: GocharaAnalysis) -> None:
        for r in result.planet_results:
            assert 0 <= r.bav_bindus <= 8, f"{r.planet} bav_bindus out of range"

    def test_planet_final_score_in_range(self, result: GocharaAnalysis) -> None:
        for r in result.planet_results:
            assert -4 <= r.final_score <= 4, f"{r.planet} final_score out of range"

    def test_planet_moorthy_valid(self, result: GocharaAnalysis) -> None:
        valid = set(MoorthyClass)
        for r in result.planet_results:
            assert r.moorthy in valid, f"{r.planet} moorthy invalid"

    def test_planet_favorability_valid(self, result: GocharaAnalysis) -> None:
        valid = set(Favorability)
        for r in result.planet_results:
            assert r.favorability in valid

    def test_planet_special_name_str_or_none(self, result: GocharaAnalysis) -> None:
        for r in result.planet_results:
            assert r.special_name is None or isinstance(r.special_name, str)

    def test_planet_result_text_non_empty(self, result: GocharaAnalysis) -> None:
        for r in result.planet_results:
            assert len(r.result_text) > 0, f"{r.planet} has empty result_text"

    def test_second_chart_returns_analysis(self, sample_chart: ChartData) -> None:
        result = compute_gochara(sample_chart, _DATE)
        assert isinstance(result, GocharaAnalysis)
        assert len(result.planet_results) == 9


# ── Vedha rules ──────────────────────────────────────────────────────────────


class TestVedha:
    """Vedha obstruction rules."""

    def test_vedha_active_zeroes_positive_score(self, manish_chart: ChartData) -> None:
        result = compute_gochara(manish_chart, _DATE)
        for r in result.planet_results:
            if r.vedha_active:
                assert r.final_score == 0, (
                    f"{r.planet} vedha active but final_score={r.final_score}"
                )

    def test_vedha_only_on_beneficial_gochara(self, manish_chart: ChartData) -> None:
        result = compute_gochara(manish_chart, _DATE)
        for r in result.planet_results:
            if r.vedha_active:
                assert r.gochara_score > 0, f"{r.planet} vedha active on non-beneficial house"

    def test_house_7_never_has_vedha(self, manish_chart: ChartData) -> None:
        result = compute_gochara(manish_chart, _DATE)
        for r in result.planet_results:
            if r.house_from_moon == 7:
                assert not r.vedha_active, f"{r.planet} has vedha at house 7 (forbidden)"

    def test_house_11_never_has_vedha(self, manish_chart: ChartData) -> None:
        result = compute_gochara(manish_chart, _DATE)
        for r in result.planet_results:
            if r.house_from_moon == 11:
                assert not r.vedha_active, f"{r.planet} has vedha at house 11 (forbidden)"


# ── Private helper functions ─────────────────────────────────────────────────


class TestPrivateHelpers:
    """Unit tests for private helper functions."""

    def test_classify_moorthy_poorna_at_5(self) -> None:
        assert _classify_moorthy(5) == MoorthyClass.poorna

    def test_classify_moorthy_poorna_at_8(self) -> None:
        assert _classify_moorthy(8) == MoorthyClass.poorna

    def test_classify_moorthy_madhya_at_3(self) -> None:
        assert _classify_moorthy(3) == MoorthyClass.madhya

    def test_classify_moorthy_madhya_at_4(self) -> None:
        assert _classify_moorthy(4) == MoorthyClass.madhya

    def test_classify_moorthy_swalpa_at_1(self) -> None:
        assert _classify_moorthy(1) == MoorthyClass.swalpa

    def test_classify_moorthy_swalpa_at_2(self) -> None:
        assert _classify_moorthy(2) == MoorthyClass.swalpa

    def test_classify_moorthy_nishphala_at_0(self) -> None:
        assert _classify_moorthy(0) == MoorthyClass.nishphala

    def test_bav_modifier_0_bindus(self) -> None:
        assert _bav_modifier(0) == -2

    def test_bav_modifier_1_bindu(self) -> None:
        assert _bav_modifier(1) == -2

    def test_bav_modifier_4_bindus(self) -> None:
        assert _bav_modifier(4) == 0

    def test_bav_modifier_7_bindus(self) -> None:
        assert _bav_modifier(7) == +2

    def test_bav_modifier_8_bindus(self) -> None:
        assert _bav_modifier(8) == +2

    def test_score_to_favorability_very_favorable(self) -> None:
        assert _score_to_favorability(2) == Favorability.very_favorable

    def test_score_to_favorability_very_unfavorable(self) -> None:
        assert _score_to_favorability(-2) == Favorability.very_unfavorable

    def test_score_to_favorability_neutral(self) -> None:
        assert _score_to_favorability(0) == Favorability.neutral

    def test_sadesati_intensity_mild_for_libra(self) -> None:
        assert _sadesati_intensity(6) == "mild"  # Libra = exalted Saturn

    def test_sadesati_intensity_mild_for_capricorn(self) -> None:
        assert _sadesati_intensity(9) == "mild"  # Capricorn = own sign

    def test_sadesati_intensity_severe_for_aries(self) -> None:
        assert _sadesati_intensity(0) == "severe"  # Aries = debilitated Saturn

    def test_sadesati_intensity_moderate_for_taurus(self) -> None:
        assert _sadesati_intensity(1) == "moderate"
