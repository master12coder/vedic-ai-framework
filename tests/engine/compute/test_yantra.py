"""Tests for yantra (magic square) computation module.

Primary fixture: manish_chart - Manish Chaurasia, Mithuna lagna (Gemini).
Known facts:
  Lagna lord = Mercury → Mercury Yantra (vedic number 5, magic sum 123)
  Moon in Rohini → nakshatra lord Moon → Moon Yantra may be included
"""

from __future__ import annotations

import pytest

from daivai_engine.compute.yantra import (
    _LO_SHU,
    _VEDIC_NUMBERS,
    compute_remedy_yantras,
    construct_yantra_grid,
    get_yantra_data,
    validate_yantra,
)
from daivai_engine.knowledge.loader import load_yantra_data
from daivai_engine.models.chart import ChartData
from daivai_engine.models.remedies import YantraRecommendation


# ── Lo Shu base grid ──────────────────────────────────────────────────────────


def test_lo_shu_base_is_valid_magic_square() -> None:
    """The base Lo Shu grid must be a valid 3x3 magic square with sum 15."""
    assert validate_yantra(_LO_SHU)
    assert sum(_LO_SHU[0]) == 15


def test_lo_shu_contains_numbers_1_to_9() -> None:
    """Base Lo Shu must contain exactly the numbers 1-9."""
    flat = [cell for row in _LO_SHU for cell in row]
    assert sorted(flat) == list(range(1, 10))


# ── construct_yantra_grid ─────────────────────────────────────────────────────


def test_construct_sun_yantra_magic_sum_is_15() -> None:
    """Sun (vedic 1, offset 0) yantra magic sum must be 15."""
    grid = construct_yantra_grid("Sun")
    assert validate_yantra(grid)
    assert sum(grid[0]) == 15


def test_construct_moon_yantra_magic_sum_is_42() -> None:
    """Moon (vedic 2, offset 9) yantra magic sum must be 42."""
    grid = construct_yantra_grid("Moon")
    assert validate_yantra(grid)
    assert sum(grid[0]) == 42


def test_construct_mercury_yantra_magic_sum_is_123() -> None:
    """Mercury (vedic 5, offset 36) yantra magic sum must be 123."""
    grid = construct_yantra_grid("Mercury")
    assert validate_yantra(grid)
    assert sum(grid[0]) == 123


def test_construct_saturn_yantra_magic_sum_is_204() -> None:
    """Saturn (vedic 8, offset 63) yantra magic sum must be 204."""
    grid = construct_yantra_grid("Saturn")
    assert validate_yantra(grid)
    assert sum(grid[0]) == 204


def test_construct_mars_yantra_magic_sum_is_231() -> None:
    """Mars (vedic 9, offset 72) yantra magic sum must be 231."""
    grid = construct_yantra_grid("Mars")
    assert validate_yantra(grid)
    assert sum(grid[0]) == 231


def test_all_nine_planet_yantras_are_valid_magic_squares() -> None:
    """All 9 planetary yantras must be valid 3x3 magic squares."""
    for planet in _VEDIC_NUMBERS:
        grid = construct_yantra_grid(planet)
        assert validate_yantra(grid), f"{planet} yantra is not a valid magic square"


def test_yantra_grid_is_3x3() -> None:
    """construct_yantra_grid must return a 3x3 list of lists."""
    for planet in _VEDIC_NUMBERS:
        grid = construct_yantra_grid(planet)
        assert len(grid) == 3
        for row in grid:
            assert len(row) == 3


def test_construct_yantra_unknown_planet_raises_value_error() -> None:
    """Unknown planet name must raise ValueError."""
    with pytest.raises(ValueError, match="Unknown planet"):
        construct_yantra_grid("Nibiru")


def test_yantra_grids_have_no_duplicate_numbers() -> None:
    """Each planet's yantra must contain 9 unique numbers."""
    for planet in _VEDIC_NUMBERS:
        grid = construct_yantra_grid(planet)
        flat = [cell for row in grid for cell in row]
        assert len(flat) == len(set(flat)), f"{planet} yantra has duplicates"


def test_center_cell_is_median_of_sequence() -> None:
    """The center cell (row 1, col 1) must be the median of the 9 numbers."""
    for planet in _VEDIC_NUMBERS:
        grid = construct_yantra_grid(planet)
        flat_sorted = sorted(cell for row in grid for cell in row)
        median = flat_sorted[4]  # middle of 9 = index 4
        assert grid[1][1] == median, f"{planet} center {grid[1][1]} != median {median}"


# ── validate_yantra ───────────────────────────────────────────────────────────


def test_validate_yantra_invalid_broken_row() -> None:
    """A grid with a broken row sum must fail validation."""
    bad = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ]
    assert not validate_yantra(bad)


def test_validate_yantra_wrong_size_returns_false() -> None:
    """A non-3x3 grid must fail validation."""
    assert not validate_yantra([[1, 2], [3, 4]])


# ── YAML data tests ────────────────────────────────────────────────────────────


def test_yantra_data_yaml_loads_all_nine_planets() -> None:
    """yantra_data.yaml must contain all 9 Vedic planets."""
    data = load_yantra_data()
    yantras = data.get("yantras", {})
    expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
    assert expected == set(yantras.keys())


def test_yantra_data_yaml_magic_sums_match_algorithm() -> None:
    """YAML magic_sum values must match the algorithmic computation."""
    data = load_yantra_data()
    for planet, entry in data.get("yantras", {}).items():
        grid = construct_yantra_grid(planet)
        computed_sum = sum(grid[0])
        yaml_sum = entry["magic_sum"]
        assert computed_sum == yaml_sum, f"{planet}: algo={computed_sum}, yaml={yaml_sum}"


def test_yantra_data_yaml_center_numbers_match_grid() -> None:
    """YAML center_number must equal grid[1][1] for each planet."""
    data = load_yantra_data()
    for planet, entry in data.get("yantras", {}).items():
        grid = construct_yantra_grid(planet)
        assert grid[1][1] == entry["center_number"], f"{planet} center mismatch"


# ── get_yantra_data ────────────────────────────────────────────────────────────


def test_get_yantra_data_mercury_returns_valid_grid() -> None:
    """Mercury yantra data must include a valid 3x3 magic square."""
    rec = get_yantra_data("Mercury")
    assert rec is not None
    assert validate_yantra(rec.grid)
    assert rec.magic_sum == 123


def test_get_yantra_data_returns_yantra_recommendation_type() -> None:
    """get_yantra_data must return a YantraRecommendation instance."""
    rec = get_yantra_data("Sun")
    assert isinstance(rec, YantraRecommendation)


def test_get_yantra_data_unknown_planet_returns_none() -> None:
    """Unknown planet name must return None."""
    rec = get_yantra_data("Pluto")
    assert rec is None


def test_get_yantra_data_includes_installation_day() -> None:
    """Every yantra must have a non-empty installation_day."""
    for planet in _VEDIC_NUMBERS:
        rec = get_yantra_data(planet)
        assert rec is not None
        assert rec.installation_day != "", f"{planet} has empty installation_day"


# ── compute_remedy_yantras ────────────────────────────────────────────────────


def test_compute_remedy_yantras_includes_lagna_lord(manish_chart: ChartData) -> None:
    """Mercury (Mithuna lagna lord) yantra must be in Manish's plan."""
    recs = compute_remedy_yantras(manish_chart)
    planets = [r.planet for r in recs]
    assert "Mercury" in planets


def test_compute_remedy_yantras_lagna_lord_is_first(manish_chart: ChartData) -> None:
    """Lagna lord yantra must be first in the recommendation list."""
    recs = compute_remedy_yantras(manish_chart)
    assert len(recs) >= 1
    assert recs[0].planet == "Mercury"


def test_compute_remedy_yantras_returns_at_most_three(manish_chart: ChartData) -> None:
    """Remedy yantras must not exceed 3 - more is energetically conflicting."""
    recs = compute_remedy_yantras(manish_chart)
    assert len(recs) <= 3


def test_compute_remedy_yantras_no_duplicate_planets(manish_chart: ChartData) -> None:
    """Each planet must appear at most once in the yantra plan."""
    recs = compute_remedy_yantras(manish_chart)
    planets = [r.planet for r in recs]
    assert len(planets) == len(set(planets))


def test_compute_remedy_yantras_each_has_nonempty_reason(manish_chart: ChartData) -> None:
    """Every yantra recommendation must have a non-empty reason string."""
    recs = compute_remedy_yantras(manish_chart)
    for rec in recs:
        assert rec.reason != "", f"{rec.planet} has empty reason"


def test_compute_remedy_yantras_all_grids_valid(manish_chart: ChartData) -> None:
    """All recommended yantras must have valid magic squares."""
    recs = compute_remedy_yantras(manish_chart)
    for rec in recs:
        assert validate_yantra(rec.grid), f"{rec.planet} yantra grid is invalid"


def test_compute_remedy_yantras_returns_list_type(manish_chart: ChartData) -> None:
    """Return type must be list of YantraRecommendation."""
    recs = compute_remedy_yantras(manish_chart)
    assert isinstance(recs, list)
    for rec in recs:
        assert isinstance(rec, YantraRecommendation)


@pytest.mark.safety
def test_compute_remedy_yantras_sample_chart(sample_chart: ChartData) -> None:
    """compute_remedy_yantras must work on any valid chart without error."""
    recs = compute_remedy_yantras(sample_chart)
    assert isinstance(recs, list)
    assert len(recs) >= 1
