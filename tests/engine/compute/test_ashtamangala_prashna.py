"""Tests for Ashtamangala Prashna (Kerala horary) computation."""

from __future__ import annotations

import pytest

from daivai_engine.compute.ashtamangala_prashna import (
    _assess_mangala_dravyas,
    _compute_sphutas,
    analyze_ashtamangala,
    classify_query,
    compute_aroodha,
    number_prashna,
)
from daivai_engine.compute.prashna import compute_prashna
from daivai_engine.models.ashtamangala import (
    AroodhaResult,
    AshtamangalaResult,
    PrashnaClassification,
    SphutuResult,
)
from daivai_engine.models.chart import ChartData


class TestClassifyQuery:
    def test_marriage_maps_to_house_7(self) -> None:
        result = classify_query("marriage")
        assert result.primary_house == 7

    def test_career_maps_to_house_10(self) -> None:
        result = classify_query("career")
        assert result.primary_house == 10

    def test_spirituality_is_moksha(self) -> None:
        result = classify_query("spirituality")
        assert result.deva_category == "moksha"
        assert result.nature == "tamasik"

    def test_wealth_is_artha_rajasik(self) -> None:
        result = classify_query("wealth")
        assert result.deva_category == "artha"
        assert result.nature == "rajasik"

    def test_general_is_dharma_sattvik(self) -> None:
        result = classify_query("general")
        assert result.deva_category == "dharma"
        assert result.nature == "sattvik"

    def test_unknown_type_defaults_gracefully(self) -> None:
        result = classify_query("unknown_query")
        assert isinstance(result, PrashnaClassification)
        assert result.primary_house == 1
        assert result.karaka == "Moon"

    def test_all_query_types_return_valid_house(self) -> None:
        query_types = [
            "general",
            "health",
            "wealth",
            "marriage",
            "career",
            "children",
            "enemies",
            "longevity",
            "fortune",
            "spirituality",
        ]
        for qtype in query_types:
            result = classify_query(qtype)
            assert 1 <= result.primary_house <= 12, f"{qtype}: invalid house"
            assert result.nature in ("sattvik", "rajasik", "tamasik")


class TestComputeAroodha:
    def test_aroodha_sign_in_valid_range(self, manish_chart: ChartData) -> None:
        for house in range(1, 13):
            result = compute_aroodha(manish_chart, house)
            assert 0 <= result.aroodha_sign_index <= 11

    def test_aroodha_exception_rule(self, manish_chart: ChartData) -> None:
        """Aroodha must not equal the house sign or its 7th (Jaimini rule)."""
        for house in range(1, 13):
            house_sign = (manish_chart.lagna_sign_index + house - 1) % 12
            seventh = (house_sign + 6) % 12
            result = compute_aroodha(manish_chart, house)
            assert result.aroodha_sign_index != house_sign, (
                f"House {house}: Aroodha fell in own sign ({house_sign})"
            )
            assert result.aroodha_sign_index != seventh, (
                f"House {house}: Aroodha fell in 7th from own sign ({seventh})"
            )

    def test_returns_aroodha_result_model(self, manish_chart: ChartData) -> None:
        result = compute_aroodha(manish_chart, 7)
        assert isinstance(result, AroodhaResult)
        assert result.house == 7
        assert result.aroodha_sign != ""
        assert result.aroodha_lord != ""
        assert isinstance(result.is_strong, bool)

    def test_lord_house_in_valid_range(self, manish_chart: ChartData) -> None:
        result = compute_aroodha(manish_chart, 1)
        assert 1 <= result.lord_house <= 12


class TestComputeSphutas:
    def test_all_sphutas_in_valid_range(self, manish_chart: ChartData) -> None:
        result = _compute_sphutas(manish_chart)
        for attr in ("trisphuta", "chatusphuta", "panchasphuta", "pranapada"):
            val = getattr(result, attr)
            assert 0.0 <= val < 360.0, f"{attr} = {val} out of range"

    def test_sign_indices_match_longitudes(self, manish_chart: ChartData) -> None:
        result = _compute_sphutas(manish_chart)
        assert result.trisphuta_sign_index == int(result.trisphuta // 30)
        assert result.panchasphuta_sign_index == int(result.panchasphuta // 30)
        assert result.pranapada_sign_index == int(result.pranapada // 30)

    def test_returns_sphuta_result_model(self, manish_chart: ChartData) -> None:
        result = _compute_sphutas(manish_chart)
        assert isinstance(result, SphutuResult)
        assert result.trisphuta_sign != ""
        assert result.panchasphuta_sign != ""

    def test_sphutas_are_deterministic(self, manish_chart: ChartData) -> None:
        r1 = _compute_sphutas(manish_chart)
        r2 = _compute_sphutas(manish_chart)
        assert r1.trisphuta == r2.trisphuta
        assert r1.panchasphuta == r2.panchasphuta


class TestAssessMangalaDravyas:
    def test_returns_eight_dravyas(self, manish_chart: ChartData) -> None:
        results = _assess_mangala_dravyas(manish_chart, "general")
        assert len(results) == 8

    def test_each_dravya_has_required_fields(self, manish_chart: ChartData) -> None:
        results = _assess_mangala_dravyas(manish_chart, "marriage")
        for d in results:
            assert d.dravya != ""
            assert d.dravya_en != ""
            assert d.planet != ""
            assert isinstance(d.is_favorable, bool)
            assert 1 <= d.planet_house <= 12

    def test_combust_planet_is_unfavorable(self, manish_chart: ChartData) -> None:
        results = _assess_mangala_dravyas(manish_chart, "career")
        for d in results:
            if "combust" in d.reason.lower():
                assert not d.is_favorable


class TestAnalyzeAshtamangala:
    def test_returns_ashtamangala_result(self, manish_chart: ChartData) -> None:
        result = analyze_ashtamangala(manish_chart, "marriage")
        assert isinstance(result, AshtamangalaResult)

    def test_answer_is_valid(self, manish_chart: ChartData) -> None:
        result = analyze_ashtamangala(manish_chart, "career")
        assert result.answer in ("YES", "NO", "MAYBE")

    def test_confidence_is_valid(self, manish_chart: ChartData) -> None:
        result = analyze_ashtamangala(manish_chart, "wealth")
        assert result.confidence in ("high", "medium", "low")

    def test_all_dravyas_count(self, manish_chart: ChartData) -> None:
        result = analyze_ashtamangala(manish_chart, "general")
        assert len(result.all_dravyas) == 8

    def test_most_favorable_dravya_is_favorable(self, manish_chart: ChartData) -> None:
        result = analyze_ashtamangala(manish_chart, "spirituality")
        # most_favorable_dravya should be favorable if ANY dravya is favorable
        if any(d.is_favorable for d in result.all_dravyas):
            assert result.most_favorable_dravya.is_favorable

    def test_scores_are_consistent(self, manish_chart: ChartData) -> None:
        result = analyze_ashtamangala(manish_chart, "children")
        assert result.positive_score >= 0
        assert result.negative_score >= 0
        # positive + negative >= 8 (Dravyas) + aroodha contribution
        total_dravya = len(result.all_dravyas)
        assert result.positive_score + result.negative_score >= total_dravya

    def test_reasoning_mentions_deva_category(self, manish_chart: ChartData) -> None:
        result = analyze_ashtamangala(manish_chart, "fortune")
        assert "dharma" in result.reasoning.lower() or "artha" in result.reasoning.lower()

    def test_classification_embedded_correctly(self, manish_chart: ChartData) -> None:
        result = analyze_ashtamangala(manish_chart, "marriage")
        assert result.classification.primary_house == 7
        assert result.classification.deva_category == "kama"

    def test_swara_analysis_mentions_nostril(self, manish_chart: ChartData) -> None:
        result = analyze_ashtamangala(manish_chart, "career")
        assert "Ida" in result.swara_analysis or "Pingala" in result.swara_analysis

    @pytest.mark.parametrize(
        "qtype",
        [
            "general",
            "marriage",
            "career",
            "wealth",
            "health",
            "spirituality",
            "children",
            "longevity",
        ],
    )
    def test_multiple_query_types(self, manish_chart: ChartData, qtype: str) -> None:
        result = analyze_ashtamangala(manish_chart, qtype)
        assert result.answer in ("YES", "NO", "MAYBE")
        assert 0 <= result.aroodha.aroodha_sign_index <= 11


class TestNumberPrashna:
    def test_number_1_is_mesha(self) -> None:
        result = number_prashna(1)
        assert result["rashi_index"] == 0
        assert result["navamsha_position"] == 1

    def test_number_9_is_still_mesha(self) -> None:
        result = number_prashna(9)
        assert result["rashi_index"] == 0
        assert result["navamsha_position"] == 9

    def test_number_10_is_vrishabha(self) -> None:
        result = number_prashna(10)
        assert result["rashi_index"] == 1
        assert result["navamsha_position"] == 1

    def test_number_108_is_meena(self) -> None:
        result = number_prashna(108)
        assert result["rashi_index"] == 11
        assert result["navamsha_position"] == 9

    def test_out_of_range_clamped(self) -> None:
        assert number_prashna(0)["number"] == 1
        assert number_prashna(999)["number"] == 108

    def test_kendra_navamsha_is_favorable(self) -> None:
        # Navamsha position 4 = kendra
        result = number_prashna(4)
        assert result["navamsha_favorable"] is True

    def test_dusthana_navamsha_is_not_favorable(self) -> None:
        # Navamsha position 6 = dusthana
        result = number_prashna(6)
        assert result["navamsha_favorable"] is False


class TestPrashnaAshtamangalaIntegration:
    def test_compute_prashna_with_ashtamangala(self) -> None:
        result = compute_prashna(
            "Will I get married this year?",
            lat=25.3176,
            lon=83.0067,
            question_type="marriage",
            use_ashtamangala=True,
        )
        assert result["ashtamangala"] is not None
        am = result["ashtamangala"]
        assert isinstance(am, AshtamangalaResult)
        assert am.answer in ("YES", "NO", "MAYBE")

    def test_compute_prashna_without_ashtamangala_is_none(self) -> None:
        result = compute_prashna(
            "test",
            lat=25.3176,
            lon=83.0067,
        )
        assert result["ashtamangala"] is None

    def test_ashtamangala_aroodha_in_result(self) -> None:
        result = compute_prashna(
            "Career question",
            lat=25.3176,
            lon=83.0067,
            question_type="career",
            use_ashtamangala=True,
        )
        am = result["ashtamangala"]
        assert am.aroodha.house == 10
        assert 0 <= am.aroodha.aroodha_sign_index <= 11
