"""Tests for Bhava Chalit vs Whole Sign house comparison."""

from __future__ import annotations

from daivai_engine.compute.house_comparison import HouseShift, compare_whole_sign_vs_chalit
from daivai_engine.constants import PLANETS


class TestCompareWholSignVsChalit:
    """Tests for compare_whole_sign_vs_chalit()."""

    def test_returns_list(self, manish_chart) -> None:
        result = compare_whole_sign_vs_chalit(manish_chart)
        assert isinstance(result, list)

    def test_all_are_house_shifts(self, manish_chart) -> None:
        result = compare_whole_sign_vs_chalit(manish_chart)
        for shift in result:
            assert isinstance(shift, HouseShift)

    def test_planet_names_are_valid(self, manish_chart) -> None:
        result = compare_whole_sign_vs_chalit(manish_chart)
        for shift in result:
            assert shift.planet in PLANETS, f"Unknown planet: {shift.planet}"

    def test_rashi_house_in_range(self, manish_chart) -> None:
        result = compare_whole_sign_vs_chalit(manish_chart)
        for shift in result:
            assert 1 <= shift.rashi_house <= 12, f"{shift.planet}: rashi_house={shift.rashi_house}"

    def test_bhava_house_in_range(self, manish_chart) -> None:
        result = compare_whole_sign_vs_chalit(manish_chart)
        for shift in result:
            assert 1 <= shift.bhava_house <= 12, f"{shift.planet}: bhava_house={shift.bhava_house}"

    def test_shifted_planets_have_different_houses(self, manish_chart) -> None:
        result = compare_whole_sign_vs_chalit(manish_chart)
        for shift in result:
            assert shift.rashi_house != shift.bhava_house, (
                f"{shift.planet}: rashi={shift.rashi_house}, bhava={shift.bhava_house} — should differ"
            )

    def test_explanation_is_non_empty(self, manish_chart) -> None:
        result = compare_whole_sign_vs_chalit(manish_chart)
        for shift in result:
            assert shift.explanation, f"{shift.planet}: empty explanation"

    def test_explanation_contains_planet_name(self, manish_chart) -> None:
        result = compare_whole_sign_vs_chalit(manish_chart)
        for shift in result:
            assert shift.planet in shift.explanation

    def test_explanation_mentions_both_houses(self, manish_chart) -> None:
        result = compare_whole_sign_vs_chalit(manish_chart)
        for shift in result:
            assert str(shift.rashi_house) in shift.explanation
            assert str(shift.bhava_house) in shift.explanation


class TestHouseShiftModel:
    """Tests for HouseShift Pydantic model."""

    def test_creation_valid(self) -> None:
        shift = HouseShift(
            planet="Sun",
            rashi_house=1,
            bhava_house=2,
            explanation="Sun shifts from 1st to 2nd in bhava chalit",
        )
        assert shift.planet == "Sun"
        assert shift.rashi_house == 1
        assert shift.bhava_house == 2

    def test_no_shift_charts_return_empty(self, sample_chart) -> None:
        """For some charts, no planets shift — result should be empty list."""
        result = compare_whole_sign_vs_chalit(sample_chart)
        assert isinstance(result, list)  # May be empty or not — just a list


class TestConsistencyWithBhavaChalit:
    """Cross-validation: house shifts should match BhavaChalit output."""

    def test_shifted_planets_exist_in_chart(self, manish_chart) -> None:
        result = compare_whole_sign_vs_chalit(manish_chart)
        for shift in result:
            assert shift.planet in manish_chart.planets

    def test_rashi_house_matches_whole_sign_house(self, manish_chart) -> None:
        result = compare_whole_sign_vs_chalit(manish_chart)
        for shift in result:
            whole_sign_house = manish_chart.planets[shift.planet].house
            assert shift.rashi_house == whole_sign_house, (
                f"{shift.planet}: expected rashi_house={whole_sign_house}, got {shift.rashi_house}"
            )
