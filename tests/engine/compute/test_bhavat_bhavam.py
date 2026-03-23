"""Tests for Bhavat Bhavam (house from house) computation.

Source: BPHS Ch.5, Phaladeepika Ch.1.
"""

from __future__ import annotations

import pytest

from daivai_engine.compute.bhavat_bhavam import (
    _are_enemies,
    _are_friends,
    _derived_house,
    compute_all_bhavat_bhavam,
    compute_bhavat_bhavam,
)
from daivai_engine.models.bhavat_bhavam import BhavatBhavamResult, HousePerspective
from daivai_engine.models.chart import ChartData


class TestBhavatBhavamStructure:
    """Tests for the overall structure of BhavatBhavamResult."""

    def test_returns_model_instance(self, manish_chart: ChartData) -> None:
        """compute_bhavat_bhavam returns a BhavatBhavamResult."""
        result = compute_bhavat_bhavam(manish_chart, 7)
        assert isinstance(result, BhavatBhavamResult)

    def test_primary_is_house_perspective(self, manish_chart: ChartData) -> None:
        """Primary field is a HousePerspective for the query house."""
        result = compute_bhavat_bhavam(manish_chart, 7)
        assert isinstance(result.primary, HousePerspective)
        assert result.primary.house_number == 7

    def test_derived_is_house_perspective(self, manish_chart: ChartData) -> None:
        """Derived field is a HousePerspective for the Nth-from-Nth house."""
        result = compute_bhavat_bhavam(manish_chart, 7)
        assert isinstance(result.derived, HousePerspective)

    def test_karaka_perspective_present(self, manish_chart: ChartData) -> None:
        """Karaka perspective should be present for standard houses."""
        result = compute_bhavat_bhavam(manish_chart, 7)
        assert result.karaka_perspective is not None

    def test_summary_non_empty(self, manish_chart: ChartData) -> None:
        """Summary string is non-empty."""
        result = compute_bhavat_bhavam(manish_chart, 1)
        assert result.summary

    def test_natural_karaka_non_empty(self, manish_chart: ChartData) -> None:
        """Natural karaka is a valid planet name."""
        result = compute_bhavat_bhavam(manish_chart, 5)
        assert result.natural_karaka

    def test_karaka_house_in_range(self, manish_chart: ChartData) -> None:
        """Karaka house is in 1-12."""
        result = compute_bhavat_bhavam(manish_chart, 10)
        assert 1 <= result.karaka_house <= 12


class TestDerivedHouseFormula:
    """Tests for the Nth-from-Nth derived house calculation."""

    @pytest.mark.parametrize(
        "query,expected",
        [
            (1, 1),  # 1st from 1st = 1st
            (2, 3),  # 2nd from 2nd = 3rd
            (3, 5),  # 3rd from 3rd = 5th
            (4, 7),  # 4th from 4th = 7th
            (5, 9),  # 5th from 5th = 9th
            (6, 11),  # 6th from 6th = 11th
            (7, 1),  # 7th from 7th = 1st
            (8, 3),  # 8th from 8th = 3rd
            (9, 5),  # 9th from 9th = 5th
            (10, 7),  # 10th from 10th = 7th
            (11, 9),  # 11th from 11th = 9th
            (12, 11),  # 12th from 12th = 11th
        ],
    )
    def test_derived_house_formula(self, query: int, expected: int) -> None:
        """Derived house matches the formula ((N-1)*2) % 12 + 1."""
        assert _derived_house(query) == expected


class TestKnownBhavatBhavamPairs:
    """Tests for well-known Bhavat Bhavam pairs from BPHS."""

    def test_marriage_7th_derived_1st(self, manish_chart: ChartData) -> None:
        """Marriage (7th): 7th from 7th = 1st house."""
        result = compute_bhavat_bhavam(manish_chart, 7)
        assert result.derived.house_number == 1

    def test_children_5th_derived_9th(self, manish_chart: ChartData) -> None:
        """Children (5th): 5th from 5th = 9th house."""
        result = compute_bhavat_bhavam(manish_chart, 5)
        assert result.derived.house_number == 9

    def test_career_10th_derived_7th(self, manish_chart: ChartData) -> None:
        """Career (10th): 10th from 10th = 7th house."""
        result = compute_bhavat_bhavam(manish_chart, 10)
        assert result.derived.house_number == 7

    def test_wealth_2nd_derived_3rd(self, manish_chart: ChartData) -> None:
        """Wealth (2nd): 2nd from 2nd = 3rd house."""
        result = compute_bhavat_bhavam(manish_chart, 2)
        assert result.derived.house_number == 3

    def test_father_9th_derived_5th(self, manish_chart: ChartData) -> None:
        """Father (9th): 9th from 9th = 5th house."""
        result = compute_bhavat_bhavam(manish_chart, 9)
        assert result.derived.house_number == 5

    def test_mother_4th_derived_7th(self, manish_chart: ChartData) -> None:
        """Mother (4th): 4th from 4th = 7th house."""
        result = compute_bhavat_bhavam(manish_chart, 4)
        assert result.derived.house_number == 7


class TestFriendshipEnemity:
    """Tests for planetary friendship/enmity helpers."""

    def test_sun_moon_friends(self) -> None:
        """Sun and Moon are natural friends."""
        assert _are_friends("Sun", "Moon")

    def test_sun_saturn_enemies(self) -> None:
        """Sun and Saturn are natural enemies."""
        assert _are_enemies("Sun", "Saturn")

    def test_same_planet_is_friend_of_itself(self) -> None:
        """A planet is always friendly with itself."""
        assert _are_friends("Mars", "Mars")

    def test_same_planet_not_enemy_of_itself(self) -> None:
        """A planet is never an enemy of itself."""
        assert not _are_enemies("Jupiter", "Jupiter")

    def test_venus_mercury_friends(self) -> None:
        """Venus and Mercury are natural friends."""
        assert _are_friends("Venus", "Mercury")


class TestReinforcingConflicting:
    """Tests for reinforcing/conflicting flag logic."""

    def test_reinforcing_and_conflicting_mutually_exclusive(self, manish_chart: ChartData) -> None:
        """A result cannot be both reinforcing and conflicting."""
        for h in range(1, 13):
            result = compute_bhavat_bhavam(manish_chart, h)
            assert not (result.reinforcing and result.conflicting)

    def test_reinforcing_when_same_lord(self, manish_chart: ChartData) -> None:
        """If primary and derived lords are the same, result is reinforcing."""
        for h in range(1, 13):
            result = compute_bhavat_bhavam(manish_chart, h)
            if result.primary.lord == result.derived.lord:
                assert result.reinforcing


class TestComputeAll:
    """Tests for compute_all_bhavat_bhavam."""

    def test_returns_12_results(self, manish_chart: ChartData) -> None:
        """compute_all_bhavat_bhavam returns exactly 12 results."""
        results = compute_all_bhavat_bhavam(manish_chart)
        assert len(results) == 12

    def test_query_houses_cover_1_to_12(self, manish_chart: ChartData) -> None:
        """All 12 houses are covered in order."""
        results = compute_all_bhavat_bhavam(manish_chart)
        houses = [r.query_house for r in results]
        assert houses == list(range(1, 13))

    def test_each_result_is_valid_type(self, manish_chart: ChartData) -> None:
        """Each result is a BhavatBhavamResult instance."""
        results = compute_all_bhavat_bhavam(manish_chart)
        for r in results:
            assert isinstance(r, BhavatBhavamResult)


class TestInputValidation:
    """Tests for input validation."""

    def test_invalid_house_zero_raises(self, manish_chart: ChartData) -> None:
        """query_house=0 raises ValueError."""
        with pytest.raises(ValueError, match="query_house must be 1-12"):
            compute_bhavat_bhavam(manish_chart, 0)

    def test_invalid_house_13_raises(self, manish_chart: ChartData) -> None:
        """query_house=13 raises ValueError."""
        with pytest.raises(ValueError, match="query_house must be 1-12"):
            compute_bhavat_bhavam(manish_chart, 13)


class TestBhavatBhavamManish:
    """Tests with known Manish chart (Mithuna lagna)."""

    def test_house_7_karaka_is_venus(self, manish_chart: ChartData) -> None:
        """Natural karaka for 7th house (marriage) is Venus."""
        result = compute_bhavat_bhavam(manish_chart, 7)
        assert result.natural_karaka == "Venus"

    def test_house_5_karaka_is_jupiter(self, manish_chart: ChartData) -> None:
        """Natural karaka for 5th house (children) is Jupiter."""
        result = compute_bhavat_bhavam(manish_chart, 5)
        assert result.natural_karaka == "Jupiter"

    def test_house_1_karaka_is_sun(self, manish_chart: ChartData) -> None:
        """Natural karaka for 1st house (self) is Sun."""
        result = compute_bhavat_bhavam(manish_chart, 1)
        assert result.natural_karaka == "Sun"

    def test_house_10_karaka_is_mercury(self, manish_chart: ChartData) -> None:
        """Natural karaka for 10th house (career) is Mercury (primary)."""
        result = compute_bhavat_bhavam(manish_chart, 10)
        assert result.natural_karaka == "Mercury"

    def test_sample_chart_works(self, sample_chart: ChartData) -> None:
        """Bhavat Bhavam works for the secondary test chart."""
        result = compute_bhavat_bhavam(sample_chart, 7)
        assert isinstance(result, BhavatBhavamResult)
        assert result.query_house == 7
