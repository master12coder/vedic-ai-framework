"""Tests for Nadi Amsha and Nadi Astrology Foundation."""

from __future__ import annotations

from daivai_engine.compute.nadi import (
    NadiAmshaPosition,
    NadiAnalysisResult,
    NakshatraNadiResult,
    compute_nadi_amsha,
    compute_nadi_analysis,
    compute_nakshatra_nadi,
    get_nadi_koota_score,
)
from daivai_engine.models.chart import ChartData


_VALID_NAKSHATRA_NADIS = {"aadi", "madhya", "antya"}
_VALID_AMSHA_NADIS = {"pingala", "ida", "sushumna"}


class TestNakshatraNadi:
    def test_returns_7_results(self, manish_chart: ChartData) -> None:
        results = compute_nakshatra_nadi(manish_chart)
        assert len(results) == 7

    def test_nadi_values_valid(self, manish_chart: ChartData) -> None:
        results = compute_nakshatra_nadi(manish_chart)
        for r in results:
            assert r.nadi in _VALID_NAKSHATRA_NADIS

    def test_nakshatra_indices_valid(self, manish_chart: ChartData) -> None:
        results = compute_nakshatra_nadi(manish_chart)
        for r in results:
            assert 0 <= r.nakshatra_index <= 26

    def test_nadi_name_non_empty(self, manish_chart: ChartData) -> None:
        results = compute_nakshatra_nadi(manish_chart)
        for r in results:
            assert len(r.nadi_name) > 0

    def test_nadi_hi_contains_hindi(self, manish_chart: ChartData) -> None:
        results = compute_nakshatra_nadi(manish_chart)
        for r in results:
            # Hindi names should contain Devanagari characters
            assert any("\u0900" <= c <= "\u097f" for c in r.nadi_hi)

    def test_planet_names_are_valid(self, manish_chart: ChartData) -> None:
        results = compute_nakshatra_nadi(manish_chart)
        planets = {r.planet for r in results}
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert planets == expected

    def test_nakshatra_matches_chart(self, manish_chart: ChartData) -> None:
        results = compute_nakshatra_nadi(manish_chart)
        for r in results:
            chart_nakshatra = manish_chart.planets[r.planet].nakshatra
            assert r.nakshatra == chart_nakshatra

    def test_returns_nakshatra_nadi_result_instances(self, manish_chart: ChartData) -> None:
        results = compute_nakshatra_nadi(manish_chart)
        for r in results:
            assert isinstance(r, NakshatraNadiResult)

    def test_nadi_follows_cycle_pattern(self, manish_chart: ChartData) -> None:
        """Nadi at nakshatra_index % 3: 0=aadi, 1=madhya, 2=antya."""
        results = compute_nakshatra_nadi(manish_chart)
        cycle = ["aadi", "madhya", "antya"]
        for r in results:
            expected_nadi = cycle[r.nakshatra_index % 3]
            assert r.nadi == expected_nadi

    def test_moon_rohini_is_aadi_nadi(self, manish_chart: ChartData) -> None:
        """Manish: Moon in Rohini (nakshatra index 3). 3 % 3 = 0 = aadi."""
        results = compute_nakshatra_nadi(manish_chart)
        moon = next(r for r in results if r.planet == "Moon")
        # Rohini is nakshatra index 3 → 3 % 3 = 0 → aadi
        assert moon.nakshatra_index == 3
        assert moon.nadi == "aadi"


class TestNadiAmsha:
    def test_returns_7_positions(self, manish_chart: ChartData) -> None:
        positions = compute_nadi_amsha(manish_chart)
        assert len(positions) == 7

    def test_amsha_numbers_in_range(self, manish_chart: ChartData) -> None:
        positions = compute_nadi_amsha(manish_chart)
        for p in positions:
            assert 1 <= p.nadi_amsha_number <= 150

    def test_nadi_values_valid(self, manish_chart: ChartData) -> None:
        positions = compute_nadi_amsha(manish_chart)
        for p in positions:
            assert p.nadi in _VALID_AMSHA_NADIS

    def test_pingala_for_amshas_1_to_50(self, manish_chart: ChartData) -> None:
        positions = compute_nadi_amsha(manish_chart)
        for p in positions:
            if 1 <= p.nadi_amsha_number <= 50:
                assert p.nadi == "pingala"

    def test_ida_for_amshas_51_to_100(self, manish_chart: ChartData) -> None:
        positions = compute_nadi_amsha(manish_chart)
        for p in positions:
            if 51 <= p.nadi_amsha_number <= 100:
                assert p.nadi == "ida"

    def test_sushumna_for_amshas_101_to_150(self, manish_chart: ChartData) -> None:
        positions = compute_nadi_amsha(manish_chart)
        for p in positions:
            if 101 <= p.nadi_amsha_number <= 150:
                assert p.nadi == "sushumna"

    def test_amsha_start_less_than_end(self, manish_chart: ChartData) -> None:
        positions = compute_nadi_amsha(manish_chart)
        for p in positions:
            assert p.nadi_amsha_start < p.nadi_amsha_end

    def test_degree_in_sign_within_amsha_range(self, manish_chart: ChartData) -> None:
        positions = compute_nadi_amsha(manish_chart)
        for p in positions:
            assert (
                p.nadi_amsha_start <= p.degree_in_sign < p.nadi_amsha_end
                or abs(p.degree_in_sign - p.nadi_amsha_start) < 0.001
            )  # edge case

    def test_amsha_size_is_0_2_degrees(self, manish_chart: ChartData) -> None:
        positions = compute_nadi_amsha(manish_chart)
        for p in positions:
            amsha_size = p.nadi_amsha_end - p.nadi_amsha_start
            assert abs(amsha_size - 0.2) < 0.001

    def test_sign_names_match_sign_index(self, manish_chart: ChartData) -> None:
        from daivai_engine.constants import SIGNS

        positions = compute_nadi_amsha(manish_chart)
        for p in positions:
            assert p.sign == SIGNS[p.sign_index]

    def test_returns_nadi_amsha_position_instances(self, manish_chart: ChartData) -> None:
        positions = compute_nadi_amsha(manish_chart)
        for p in positions:
            assert isinstance(p, NadiAmshaPosition)


class TestNadiAnalysis:
    def test_returns_analysis_result(self, manish_chart: ChartData) -> None:
        result = compute_nadi_analysis(manish_chart)
        assert isinstance(result, NadiAnalysisResult)

    def test_distribution_sums_to_7(self, manish_chart: ChartData) -> None:
        result = compute_nadi_analysis(manish_chart)
        total = sum(result.nadi_distribution.values())
        assert total == 7

    def test_dominant_nadi_is_valid(self, manish_chart: ChartData) -> None:
        result = compute_nadi_analysis(manish_chart)
        assert result.dominant_nadi in _VALID_NAKSHATRA_NADIS

    def test_distribution_keys_are_valid(self, manish_chart: ChartData) -> None:
        result = compute_nadi_analysis(manish_chart)
        assert set(result.nadi_distribution.keys()) == {"aadi", "madhya", "antya"}

    def test_dominant_has_max_count(self, manish_chart: ChartData) -> None:
        result = compute_nadi_analysis(manish_chart)
        max_count = max(result.nadi_distribution.values())
        dominant_count = result.nadi_distribution[result.dominant_nadi]
        assert dominant_count == max_count

    def test_both_lists_have_7_items(self, manish_chart: ChartData) -> None:
        result = compute_nadi_analysis(manish_chart)
        assert len(result.nakshatra_nadis) == 7
        assert len(result.nadi_amshas) == 7


class TestNadiKoota:
    def test_same_chart_gives_nadi_dosha(self, manish_chart: ChartData) -> None:
        """Same chart vs itself → same Nadi → 0 score → Nadi Dosha."""
        result = get_nadi_koota_score(manish_chart, manish_chart)
        assert result["score"] == 0
        assert result["nadi_dosha"] is True

    def test_score_is_0_or_8(self, manish_chart: ChartData, sample_chart: ChartData) -> None:
        result = get_nadi_koota_score(manish_chart, sample_chart)
        assert result["score"] in (0, 8)

    def test_max_score_is_8(self, manish_chart: ChartData, sample_chart: ChartData) -> None:
        result = get_nadi_koota_score(manish_chart, sample_chart)
        assert result["max_score"] == 8

    def test_different_nadi_gives_8_points(
        self, manish_chart: ChartData, sample_chart: ChartData
    ) -> None:
        result = get_nadi_koota_score(manish_chart, sample_chart)
        if result["nadi1_key"] != result["nadi2_key"]:
            assert result["score"] == 8
            assert result["nadi_dosha"] is False

    def test_nadi_keys_valid(self, manish_chart: ChartData, sample_chart: ChartData) -> None:
        result = get_nadi_koota_score(manish_chart, sample_chart)
        assert result["nadi1_key"] in _VALID_NAKSHATRA_NADIS
        assert result["nadi2_key"] in _VALID_NAKSHATRA_NADIS

    def test_dosha_description_non_empty(
        self, manish_chart: ChartData, sample_chart: ChartData
    ) -> None:
        result = get_nadi_koota_score(manish_chart, sample_chart)
        assert len(result["dosha_description"]) > 0
