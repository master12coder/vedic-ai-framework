"""Tests for Sarvatobhadra Chakra (SBC) — 9x9 transit analysis grid."""

from __future__ import annotations

from daivai_engine.compute.sarvatobhadra import (
    build_sbc_grid,
    compute_sbc_vedha,
    is_nakshatra_struck,
)
from daivai_engine.constants import NAKSHATRAS
from daivai_engine.models.sarvatobhadra import SBCCell, SBCVedhaResult


class TestBuildSbcGrid:
    """Tests for build_sbc_grid() — 9x9 Sarvatobhadra grid construction."""

    def test_returns_9x9_grid(self) -> None:
        grid = build_sbc_grid()
        assert len(grid) == 9
        for row in grid:
            assert len(row) == 9, f"Row length {len(row)} != 9"

    def test_all_cells_are_sbc_cell(self) -> None:
        grid = build_sbc_grid()
        for row in grid:
            for cell in row:
                assert isinstance(cell, SBCCell)

    def test_28_nakshatras_in_grid(self) -> None:
        """SBC uses 27 nakshatras + Abhijit = 28."""
        grid = build_sbc_grid()
        nakshatra_cell_count = 0
        for row in grid:
            for cell in row:
                if cell.nakshatra_names:
                    nakshatra_cell_count += 1
        assert nakshatra_cell_count == 28

    def test_12_rashis_in_grid(self) -> None:
        grid = build_sbc_grid()
        rashi_cell_count = 0
        for row in grid:
            for cell in row:
                if cell.rashis:
                    rashi_cell_count += 1
        assert rashi_cell_count == 12

    def test_cell_rows_and_cols_in_range(self) -> None:
        grid = build_sbc_grid()
        for r_idx, row in enumerate(grid):
            for c_idx in range(len(row)):
                cell = grid[r_idx][c_idx]
                assert cell.row == r_idx, f"Expected row={r_idx}, got {cell.row}"
                assert cell.col == c_idx, f"Expected col={c_idx}, got {cell.col}"

    def test_center_cell_is_marked(self) -> None:
        """Center cell (4,4) should have is_center=True."""
        grid = build_sbc_grid()
        center = grid[4][4]
        assert center.is_center

    def test_non_center_cells_not_marked(self) -> None:
        grid = build_sbc_grid()
        for r in range(9):
            for c in range(9):
                if r != 4 or c != 4:
                    assert not grid[r][c].is_center


class TestComputeSbcVedha:
    """Tests for compute_sbc_vedha() — nakshatra transit vedha analysis."""

    def test_returns_sbc_vedha_result(self) -> None:
        result = compute_sbc_vedha("Moon", 3)  # Rohini = index 3
        assert isinstance(result, SBCVedhaResult)

    def test_transit_nakshatra_stored(self) -> None:
        result = compute_sbc_vedha("Moon", 3)
        assert result.transit_nakshatra == NAKSHATRAS[3]

    def test_transit_planet_stored(self) -> None:
        result = compute_sbc_vedha("Saturn", 5)
        assert result.transit_planet == "Saturn"

    def test_across_vedha_is_list(self) -> None:
        result = compute_sbc_vedha("Moon", 3)
        assert isinstance(result.across_vedha, list)

    def test_fore_vedha_is_list(self) -> None:
        result = compute_sbc_vedha("Moon", 3)
        assert isinstance(result.fore_vedha, list)

    def test_hind_vedha_is_list(self) -> None:
        result = compute_sbc_vedha("Moon", 3)
        assert isinstance(result.hind_vedha, list)

    def test_struck_nakshatras_across_is_list(self) -> None:
        result = compute_sbc_vedha("Moon", 3)
        assert isinstance(result.struck_nakshatras_across, list)

    def test_struck_nakshatras_are_valid(self) -> None:
        result = compute_sbc_vedha("Moon", 3)
        for nak in result.struck_nakshatras_across:
            assert nak in NAKSHATRAS or nak == "Abhijit", f"Invalid nakshatra: {nak}"

    def test_all_27_nakshatra_indices_return_valid_result(self) -> None:
        for idx in range(27):
            result = compute_sbc_vedha("Moon", idx)
            assert isinstance(result, SBCVedhaResult)

    def test_across_vedha_has_cells(self) -> None:
        """Row + column vedha should include multiple cells."""
        result = compute_sbc_vedha("Sun", 0)
        assert len(result.across_vedha) > 0

    def test_struck_tithis_across_is_list(self) -> None:
        result = compute_sbc_vedha("Moon", 3)
        assert isinstance(result.struck_tithis_across, list)

    def test_struck_varas_across_is_list(self) -> None:
        result = compute_sbc_vedha("Moon", 3)
        assert isinstance(result.struck_varas_across, list)


class TestIsNakshatraStruck:
    """Tests for is_nakshatra_struck()."""

    def test_returns_bool(self) -> None:
        vedha = compute_sbc_vedha("Moon", 3)  # Moon in Rohini
        result = is_nakshatra_struck(vedha, 3)  # Is Rohini struck by itself?
        assert isinstance(result, bool)

    def test_all_indices_return_bool(self) -> None:
        vedha = compute_sbc_vedha("Moon", 3)
        for idx in range(27):
            r = is_nakshatra_struck(vedha, idx)
            assert isinstance(r, bool)

    def test_specific_vedha_types_work(self) -> None:
        vedha = compute_sbc_vedha("Jupiter", 5)
        r_across = is_nakshatra_struck(vedha, 3, vedha_types=["across"])
        r_fore = is_nakshatra_struck(vedha, 3, vedha_types=["fore"])
        r_hind = is_nakshatra_struck(vedha, 3, vedha_types=["hind"])
        assert isinstance(r_across, bool)
        assert isinstance(r_fore, bool)
        assert isinstance(r_hind, bool)


class TestSbcGridConsistency:
    """Consistency tests for the SBC grid."""

    def test_grid_is_deterministic(self) -> None:
        """build_sbc_grid() should return consistent results."""
        grid1 = build_sbc_grid()
        grid2 = build_sbc_grid()
        assert grid1[0][0].row == grid2[0][0].row
        assert grid1[4][4].is_center == grid2[4][4].is_center

    def test_all_nakshatra_nums_unique_across_grid(self) -> None:
        """Each SBC nakshatra number 1-28 appears exactly once."""
        grid = build_sbc_grid()
        all_nums = []
        for row in grid:
            for cell in row:
                all_nums.extend(cell.nakshatra_nums)
        assert len(all_nums) == 28
        assert len(set(all_nums)) == 28

    def test_all_rashis_unique_across_grid(self) -> None:
        """Each rashi 1-12 appears exactly once."""
        grid = build_sbc_grid()
        all_rashis = []
        for row in grid:
            for cell in row:
                all_rashis.extend(cell.rashis)
        assert len(all_rashis) == 12
        assert len(set(all_rashis)) == 12
