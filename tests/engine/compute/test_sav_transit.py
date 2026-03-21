"""Tests for SAV Pinda-based transit analysis."""

from __future__ import annotations

from daivai_engine.compute.sav_transit import (
    BAV_BAD_THRESHOLD,
    BAV_GOOD_THRESHOLD,
    SavPindaResult,
    SavTransitScore,
    compute_sav_pinda,
    compute_sav_transit_scores,
    get_best_transit_signs,
)
from daivai_engine.models.chart import ChartData


class TestSavPinda:
    def test_returns_12_sign_profiles(self, manish_chart: ChartData) -> None:
        result = compute_sav_pinda(manish_chart)
        assert len(result.sign_profiles) == 12

    def test_total_bindus_equals_337(self, manish_chart: ChartData) -> None:
        """SAV total must always equal 337 (BPHS invariant)."""
        result = compute_sav_pinda(manish_chart)
        assert result.total_bindus == 337

    def test_sign_indices_are_0_to_11(self, manish_chart: ChartData) -> None:
        result = compute_sav_pinda(manish_chart)
        for p in result.sign_profiles:
            assert 0 <= p.sign_index <= 11

    def test_sav_totals_in_valid_range(self, manish_chart: ChartData) -> None:
        result = compute_sav_pinda(manish_chart)
        for p in result.sign_profiles:
            assert 0 <= p.sav_total <= 56

    def test_label_keys_are_valid(self, manish_chart: ChartData) -> None:
        valid_keys = {"excellent", "good", "average", "difficult", "very_adverse"}
        result = compute_sav_pinda(manish_chart)
        for p in result.sign_profiles:
            assert p.label_key in valid_keys

    def test_sav_modifier_values(self, manish_chart: ChartData) -> None:
        result = compute_sav_pinda(manish_chart)
        for p in result.sign_profiles:
            assert p.sav_modifier in (-1, 0, 1)

    def test_strongest_weakest_are_valid_sign_indices(self, manish_chart: ChartData) -> None:
        result = compute_sav_pinda(manish_chart)
        assert 0 <= result.strongest_sign_index <= 11
        assert 0 <= result.weakest_sign_index <= 11

    def test_strongest_has_higher_total_than_weakest(self, manish_chart: ChartData) -> None:
        result = compute_sav_pinda(manish_chart)
        profiles = {p.sign_index: p for p in result.sign_profiles}
        strongest_total = profiles[result.strongest_sign_index].sav_total
        weakest_total = profiles[result.weakest_sign_index].sav_total
        assert strongest_total >= weakest_total

    def test_sav_pinda_returns_model_instance(self, manish_chart: ChartData) -> None:
        result = compute_sav_pinda(manish_chart)
        assert isinstance(result, SavPindaResult)


class TestSavTransitScores:
    def test_returns_scores_for_given_planets(self, manish_chart: ChartData) -> None:
        transit_map = {"Saturn": 3, "Jupiter": 7, "Mars": 1}
        scores = compute_sav_transit_scores(manish_chart, transit_map)
        assert len(scores) == 3

    def test_planet_names_match_input(self, manish_chart: ChartData) -> None:
        transit_map = {"Saturn": 3, "Jupiter": 7}
        scores = compute_sav_transit_scores(manish_chart, transit_map)
        names = {s.planet for s in scores}
        assert names == {"Saturn", "Jupiter"}

    def test_bav_bindus_in_range(self, manish_chart: ChartData) -> None:
        transit_map = {"Saturn": 0, "Jupiter": 5, "Moon": 11}
        scores = compute_sav_transit_scores(manish_chart, transit_map)
        for s in scores:
            assert 0 <= s.bav_bindus <= 8

    def test_sav_total_in_range(self, manish_chart: ChartData) -> None:
        transit_map = {"Saturn": 0, "Jupiter": 5}
        scores = compute_sav_transit_scores(manish_chart, transit_map)
        for s in scores:
            assert 0 <= s.sav_total <= 56

    def test_combined_score_clamped(self, manish_chart: ChartData) -> None:
        transit_map = {"Saturn": 0, "Jupiter": 5, "Mars": 1, "Sun": 2, "Moon": 11}
        scores = compute_sav_transit_scores(manish_chart, transit_map)
        for s in scores:
            assert -3 <= s.combined_score <= 3

    def test_sorted_by_combined_score_descending(self, manish_chart: ChartData) -> None:
        transit_map = {"Saturn": 0, "Jupiter": 5, "Mars": 1, "Sun": 2}
        scores = compute_sav_transit_scores(manish_chart, transit_map)
        for i in range(len(scores) - 1):
            assert scores[i].combined_score >= scores[i + 1].combined_score

    def test_bav_quality_valid(self, manish_chart: ChartData) -> None:
        transit_map = {"Saturn": 3, "Jupiter": 7}
        scores = compute_sav_transit_scores(manish_chart, transit_map)
        for s in scores:
            assert s.bav_quality in ("good", "average", "difficult")

    def test_rahu_ketu_get_neutral_bav(self, manish_chart: ChartData) -> None:
        """Rahu/Ketu not in BAV tables — should get default neutral (4) bindus."""
        transit_map = {"Rahu": 3, "Ketu": 9}
        scores = compute_sav_transit_scores(manish_chart, transit_map)
        for s in scores:
            assert s.bav_bindus == 4

    def test_returns_sav_transit_score_instances(self, manish_chart: ChartData) -> None:
        transit_map = {"Jupiter": 7}
        scores = compute_sav_transit_scores(manish_chart, transit_map)
        assert isinstance(scores[0], SavTransitScore)

    def test_sign_names_match_sign_index(self, manish_chart: ChartData) -> None:
        from daivai_engine.constants import SIGNS
        transit_map = {"Jupiter": 7, "Saturn": 3}
        scores = compute_sav_transit_scores(manish_chart, transit_map)
        for s in scores:
            assert s.sign == SIGNS[s.transit_sign_index]


class TestBavThresholds:
    def test_bav_good_threshold_is_4(self) -> None:
        assert BAV_GOOD_THRESHOLD == 4

    def test_bav_bad_threshold_is_2(self) -> None:
        assert BAV_BAD_THRESHOLD == 2


class TestGetBestTransitSigns:
    def test_returns_n_signs(self, manish_chart: ChartData) -> None:
        signs = get_best_transit_signs(manish_chart, "Saturn", top_n=3)
        assert len(signs) == 3

    def test_sign_indices_valid(self, manish_chart: ChartData) -> None:
        signs = get_best_transit_signs(manish_chart, "Jupiter", top_n=3)
        for s in signs:
            assert 0 <= s.sign_index <= 11

    def test_works_for_all_planets(self, manish_chart: ChartData) -> None:
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            signs = get_best_transit_signs(manish_chart, planet, top_n=3)
            assert len(signs) == 3
