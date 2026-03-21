"""Tests for varga deep analysis — D9, D10, D7, D12, and cross-varga."""

from __future__ import annotations

import pytest

from daivai_engine.compute.varga_deep_analysis import (
    CrossVargaResult,
    VargaDeepResult,
    analyze_d7_deep,
    analyze_d9_deep,
    analyze_d10_deep,
    analyze_d12_deep,
    cross_varga_confirm,
)
from daivai_engine.models.chart import ChartData


class TestD9Deep:
    def test_returns_d9_result(self, manish_chart: ChartData) -> None:
        result = analyze_d9_deep(manish_chart)
        assert isinstance(result, VargaDeepResult)
        assert result.varga == "D9"
        assert result.varga_name == "Navamsha"

    def test_key_house_is_7th(self, manish_chart: ChartData) -> None:
        result = analyze_d9_deep(manish_chart)
        assert result.key_house_index == 7

    def test_d9_lagna_valid(self, manish_chart: ChartData) -> None:
        result = analyze_d9_deep(manish_chart)
        assert 0 <= result.varga_lagna_sign_index <= 11
        assert result.varga_lagna_sign

    def test_key_house_sign_is_7th_from_lagna(self, manish_chart: ChartData) -> None:
        """D9 7th should be 6 signs forward from D9 lagna."""
        from daivai_engine.compute.divisional import compute_navamsha_sign
        from daivai_engine.constants import SIGNS
        result = analyze_d9_deep(manish_chart)
        d9_lagna = compute_navamsha_sign(manish_chart.lagna_longitude)
        expected_7th = (d9_lagna + 6) % 12
        assert result.varga_lagna_sign_index == d9_lagna
        assert result.key_house_sign == SIGNS[expected_7th]

    def test_has_at_least_two_findings(self, manish_chart: ChartData) -> None:
        result = analyze_d9_deep(manish_chart)
        assert len(result.key_findings) >= 2

    def test_strength_valid(self, manish_chart: ChartData) -> None:
        result = analyze_d9_deep(manish_chart)
        assert result.strength in ("strong", "moderate", "weak")

    def test_vargottama_planets_are_list(self, manish_chart: ChartData) -> None:
        result = analyze_d9_deep(manish_chart)
        assert isinstance(result.vargottama_planets, list)


class TestD10Deep:
    def test_returns_d10_result(self, manish_chart: ChartData) -> None:
        result = analyze_d10_deep(manish_chart)
        assert isinstance(result, VargaDeepResult)
        assert result.varga == "D10"
        assert result.varga_name == "Dasamsha"

    def test_key_house_is_10th(self, manish_chart: ChartData) -> None:
        result = analyze_d10_deep(manish_chart)
        assert result.key_house_index == 10

    def test_d10_lagna_valid(self, manish_chart: ChartData) -> None:
        result = analyze_d10_deep(manish_chart)
        assert 0 <= result.varga_lagna_sign_index <= 11

    def test_has_findings(self, manish_chart: ChartData) -> None:
        result = analyze_d10_deep(manish_chart)
        assert len(result.key_findings) >= 2

    def test_strength_valid(self, manish_chart: ChartData) -> None:
        result = analyze_d10_deep(manish_chart)
        assert result.strength in ("strong", "moderate", "weak")


class TestD7Deep:
    def test_returns_d7_result(self, manish_chart: ChartData) -> None:
        result = analyze_d7_deep(manish_chart)
        assert isinstance(result, VargaDeepResult)
        assert result.varga == "D7"
        assert result.varga_name == "Saptamsha"

    def test_key_house_is_5th(self, manish_chart: ChartData) -> None:
        result = analyze_d7_deep(manish_chart)
        assert result.key_house_index == 5

    def test_d7_lagna_valid(self, manish_chart: ChartData) -> None:
        result = analyze_d7_deep(manish_chart)
        assert 0 <= result.varga_lagna_sign_index <= 11

    def test_jupiter_finding_present(self, manish_chart: ChartData) -> None:
        """Jupiter (Putra Karaka) should appear in findings."""
        result = analyze_d7_deep(manish_chart)
        has_jup = any("Jupiter" in f for f in result.key_findings)
        assert has_jup, "Jupiter (Putra Karaka) should appear in D7 findings"


class TestD12Deep:
    def test_returns_d12_result(self, manish_chart: ChartData) -> None:
        result = analyze_d12_deep(manish_chart)
        assert isinstance(result, VargaDeepResult)
        assert result.varga == "D12"
        assert result.varga_name == "Dwadashamsha"

    def test_key_house_is_9th(self, manish_chart: ChartData) -> None:
        result = analyze_d12_deep(manish_chart)
        assert result.key_house_index == 9

    def test_has_parent_karma_findings(self, manish_chart: ChartData) -> None:
        """D12 must mention both mother (4th) and father (9th) karma."""
        result = analyze_d12_deep(manish_chart)
        has_mother = any("mother" in f.lower() or "4th" in f for f in result.key_findings)
        has_father = any("father" in f.lower() or "9th" in f for f in result.key_findings)
        assert has_mother, "Missing mother karma finding"
        assert has_father, "Missing father karma finding"

    def test_sun_moon_karakas_present(self, manish_chart: ChartData) -> None:
        result = analyze_d12_deep(manish_chart)
        sun_mentioned = any("Sun" in f for f in result.key_findings)
        moon_mentioned = any("Moon" in f for f in result.key_findings)
        assert sun_mentioned, "Sun (father karaka) should appear in D12 findings"
        assert moon_mentioned, "Moon (mother karaka) should appear in D12 findings"


class TestCrossVarga:
    @pytest.mark.parametrize("planet", ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"])
    def test_certainty_valid(self, manish_chart: ChartData, planet: str) -> None:
        result = cross_varga_confirm(manish_chart, planet)
        assert result.certainty in ("certain", "probable", "possible", "weak")

    def test_result_is_cross_varga_model(self, manish_chart: ChartData) -> None:
        result = cross_varga_confirm(manish_chart, "Mercury")
        assert isinstance(result, CrossVargaResult)

    def test_signs_populated(self, manish_chart: ChartData) -> None:
        result = cross_varga_confirm(manish_chart, "Mercury")
        assert result.d1_sign
        assert result.d9_sign
        assert result.d60_sign

    def test_planet_field_matches(self, manish_chart: ChartData) -> None:
        result = cross_varga_confirm(manish_chart, "Jupiter")
        assert result.planet == "Jupiter"

    def test_three_strong_means_certain(self, manish_chart: ChartData) -> None:
        """If all three flags are True, certainty must be 'certain'."""
        result = cross_varga_confirm(manish_chart, "Sun")
        if result.in_d1_own_or_exalt and result.in_d9_own_or_exalt and result.in_d60_own_or_exalt:
            assert result.certainty == "certain"

    def test_jupiter_saturn_cross_varga_manish(self, manish_chart: ChartData) -> None:
        """Smoke test: Jupiter and Saturn cross-varga for Manish — must not error."""
        jup = cross_varga_confirm(manish_chart, "Jupiter")
        sat = cross_varga_confirm(manish_chart, "Saturn")
        assert jup.planet == "Jupiter"
        assert sat.planet == "Saturn"
        # Certainty must be one of the valid levels
        assert jup.certainty in ("certain", "probable", "possible", "weak")
        assert sat.certainty in ("certain", "probable", "possible", "weak")
