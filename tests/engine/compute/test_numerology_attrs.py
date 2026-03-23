"""Tests for numerology attribute lookups, Yantra generation, and compatibility."""

from __future__ import annotations

import pytest

from daivai_engine.compute.numerology_attrs import (
    compute_compatibility,
    generate_yantra,
    get_compound_number_meaning,
    get_number_attributes,
    planet_for_number,
)
from daivai_engine.exceptions import ValidationError
from daivai_engine.models.numerology import (
    CompatibilityResult,
    NumberAttributes,
    NumerologyYantra,
)


class TestGenerateYantra:
    """Tests for generate_yantra() — 3x3 magic square generation."""

    def test_returns_yantra_model(self) -> None:
        result = generate_yantra(1)
        assert isinstance(result, NumerologyYantra)

    def test_grid_is_3x3(self) -> None:
        for n in range(1, 10):
            result = generate_yantra(n)
            assert len(result.grid) == 3
            for row in result.grid:
                assert len(row) == 3

    def test_magic_constant_is_15_times_number(self) -> None:
        for n in range(1, 10):
            result = generate_yantra(n)
            assert result.magic_constant == 15 * n

    def test_all_rows_sum_to_magic_constant(self) -> None:
        for n in range(1, 10):
            result = generate_yantra(n)
            mc = result.magic_constant
            for row in result.grid:
                assert sum(row) == mc, f"n={n}, row={row}"

    def test_all_columns_sum_to_magic_constant(self) -> None:
        for n in range(1, 10):
            result = generate_yantra(n)
            mc = result.magic_constant
            for col in range(3):
                col_sum = sum(result.grid[row][col] for row in range(3))
                assert col_sum == mc, f"n={n}, col={col}"

    def test_diagonals_sum_to_magic_constant(self) -> None:
        for n in range(1, 10):
            result = generate_yantra(n)
            mc = result.magic_constant
            diag1 = result.grid[0][0] + result.grid[1][1] + result.grid[2][2]
            diag2 = result.grid[0][2] + result.grid[1][1] + result.grid[2][0]
            assert diag1 == mc, f"n={n}, diag1={diag1}"
            assert diag2 == mc, f"n={n}, diag2={diag2}"

    def test_number_stored_correctly(self) -> None:
        result = generate_yantra(5)
        assert result.number == 5

    def test_invalid_number_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            generate_yantra(0)
        with pytest.raises(ValidationError):
            generate_yantra(10)


class TestComputeCompatibility:
    """Tests for compute_compatibility() — numerology compatibility scoring."""

    def test_returns_compatibility_result(self) -> None:
        result = compute_compatibility(1, 1)
        assert isinstance(result, CompatibilityResult)

    def test_numbers_stored(self) -> None:
        result = compute_compatibility(3, 7)
        assert result.number1 == 3
        assert result.number2 == 7

    def test_score_in_0_100_range(self) -> None:
        for n1 in range(1, 10):
            for n2 in range(1, 10):
                result = compute_compatibility(n1, n2)
                assert 0 <= result.score <= 100, f"({n1},{n2}): {result.score}"

    def test_category_is_non_empty(self) -> None:
        result = compute_compatibility(1, 9)
        assert result.category

    def test_planets_are_set(self) -> None:
        result = compute_compatibility(1, 2)
        assert result.planet1
        assert result.planet2

    def test_invalid_number_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            compute_compatibility(0, 5)
        with pytest.raises(ValidationError):
            compute_compatibility(5, 10)


class TestGetNumberAttributes:
    """Tests for get_number_attributes() — planet number attribute lookup."""

    def test_returns_number_attributes(self) -> None:
        result = get_number_attributes(1)
        assert isinstance(result, NumberAttributes)

    def test_all_numbers_1_to_9_load(self) -> None:
        for n in range(1, 10):
            result = get_number_attributes(n)
            assert isinstance(result, NumberAttributes)
            assert result.number == n

    def test_planet_name_non_empty(self) -> None:
        for n in range(1, 10):
            result = get_number_attributes(n)
            assert result.planet, f"Number {n} has empty planet"

    def test_lucky_days_is_list(self) -> None:
        result = get_number_attributes(1)
        assert isinstance(result.lucky_days, list)

    def test_lucky_colors_is_list(self) -> None:
        result = get_number_attributes(2)
        assert isinstance(result.lucky_colors, list)

    def test_master_number_11_reduces_to_2(self) -> None:
        result = get_number_attributes(11)
        assert result.number == 2

    def test_master_number_22_reduces_to_4(self) -> None:
        result = get_number_attributes(22)
        assert result.number == 4

    def test_master_number_33_reduces_to_6(self) -> None:
        result = get_number_attributes(33)
        assert result.number == 6

    def test_invalid_number_raises(self) -> None:
        with pytest.raises(ValidationError):
            get_number_attributes(100)


class TestGetCompoundNumberMeaning:
    """Tests for get_compound_number_meaning()."""

    def test_returns_string(self) -> None:
        result = get_compound_number_meaning(10)
        assert isinstance(result, str)

    def test_valid_range_10_to_52(self) -> None:
        for n in [10, 20, 30, 40, 50, 52]:
            result = get_compound_number_meaning(n)
            assert isinstance(result, str)

    def test_out_of_range_returns_empty(self) -> None:
        assert get_compound_number_meaning(9) == ""
        assert get_compound_number_meaning(53) == ""


class TestPlanetForNumber:
    """Tests for planet_for_number()."""

    def test_returns_string(self) -> None:
        result = planet_for_number(1)
        assert isinstance(result, str)

    def test_number_1_is_sun(self) -> None:
        result = planet_for_number(1)
        assert result == "Sun"

    def test_number_2_is_moon(self) -> None:
        result = planet_for_number(2)
        assert result == "Moon"

    def test_all_numbers_return_known_planet(self) -> None:
        known_planets = {
            "Sun",
            "Moon",
            "Mars",
            "Mercury",
            "Jupiter",
            "Venus",
            "Saturn",
            "Rahu",
            "Ketu",
        }
        for n in range(1, 10):
            p = planet_for_number(n)
            assert p in known_planets, f"Number {n}: planet '{p}' not recognized"
