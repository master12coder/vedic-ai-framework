"""Tests for Sarvatobhadra Chakra (SBC) grid and vedha computation.

Covers:
  - Grid structure and completeness (nakshatras, rashis, tithis, varas)
  - Nakshatra cell positions from authoritative layout (PyJHora / Phaladeepika)
  - Vedha geometry: across (row+col), fore (/diagonal), hind (\\diagonal)
  - Nakshatra striking logic and helper functions
  - Boundary / error conditions
"""

from __future__ import annotations

import pytest

from daivai_engine.compute.sarvatobhadra import (
    build_sbc_grid,
    compute_sbc_vedha,
    is_nakshatra_struck,
)
from daivai_engine.constants import NAKSHATRAS
from daivai_engine.models.sarvatobhadra import SBCCell, SBCVedhaResult


# ── Grid structure tests ──────────────────────────────────────────────────────


class TestSBCGridStructure:
    def test_grid_is_9x9(self):
        """Grid must be exactly 9 rows of 9 cells each."""
        grid = build_sbc_grid()
        assert len(grid) == 9
        for row in grid:
            assert len(row) == 9

    def test_all_cells_are_sbccell(self):
        """Every cell must be an SBCCell instance."""
        grid = build_sbc_grid()
        for row in grid:
            for cell in row:
                assert isinstance(cell, SBCCell)

    def test_cell_coordinates_match_position(self):
        """Each cell must report its own (row, col) correctly."""
        grid = build_sbc_grid()
        for r, row in enumerate(grid):
            for c, cell in enumerate(row):
                assert cell.row == r
                assert cell.col == c

    def test_all_27_standard_nakshatras_present(self):
        """All 27 standard nakshatras (Ashwini-Revati) must appear exactly once."""
        grid = build_sbc_grid()
        found: set[int] = set()
        for row in grid:
            for cell in row:
                for num in cell.nakshatra_nums:
                    assert num not in found, f"Nakshatra SBC#{num} appears twice"
                    found.add(num)
        assert set(range(1, 28)).issubset(found)

    def test_abhijit_present_exactly_once(self):
        """Abhijit (SBC nakshatra 28) must appear exactly once."""
        grid = build_sbc_grid()
        count = sum(
            1 for row in grid for cell in row if 28 in cell.nakshatra_nums
        )
        assert count == 1

    def test_all_12_rashis_present(self):
        """All 12 rashis (1-12) must appear in the grid exactly once each."""
        grid = build_sbc_grid()
        found: list[int] = []
        for row in grid:
            for cell in row:
                found.extend(cell.rashis)
        assert sorted(found) == list(range(1, 13))

    def test_all_5_tithi_groups_present(self):
        """Nanda, Bhadra, Jaya, Rikta, Purna must each appear once."""
        grid = build_sbc_grid()
        groups = {
            cell.tithi_group
            for row in grid
            for cell in row
            if cell.tithi_group
        }
        assert groups == {"Nanda", "Bhadra", "Jaya", "Rikta", "Purna"}

    def test_all_7_varas_covered(self):
        """All seven weekdays must be assigned to some cell."""
        grid = build_sbc_grid()
        varas: set[str] = set()
        for row in grid:
            for cell in row:
                varas.update(cell.varas)
        expected = {
            "Sunday", "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday",
        }
        assert varas == expected

    def test_center_cell_is_purna_saturday(self):
        """Cell (4,4) must be the center: Purna tithi + Saturday."""
        grid = build_sbc_grid()
        center = grid[4][4]
        assert center.is_center is True
        assert center.tithi_group == "Purna"
        assert "Saturday" in center.varas

    def test_four_outer_corners_are_vowels(self):
        """The four corners of the 9x9 grid must all be vowel cells."""
        grid = build_sbc_grid()
        for r, c in [(0, 0), (0, 8), (8, 0), (8, 8)]:
            cell = grid[r][c]
            assert cell.vowels, f"Corner ({r},{c}) has no vowels"
            assert not cell.nakshatra_nums, f"Corner ({r},{c}) wrongly holds nakshatra"


# ── Nakshatra position tests ──────────────────────────────────────────────────


class TestNakshatraPositions:
    """Verify exact cell coordinates for key nakshatras.

    Layout: zodiacal order goes clockwise starting from Ashwini at (0,6):
      North row  (0, cols 6→7):  1=Ashwini, 2=Bharani
      East col   (rows 1→7, 8):  3=Krittika … 9=Ashlesha
      South row  (8, cols 7→1):  10=Magha … 16=Vishakha
      West col   (rows 7→1, 0):  17=Anuradha … 21=Uttara Ashadha,
                                  28=Abhijit, 22=Shravana
      North row  (0, cols 1→5):  23=Dhanishtha … 27=Revati
    """

    def test_ashwini_position(self):
        """Ashwini (SBC 1) must be at row 0, col 6."""
        grid = build_sbc_grid()
        assert 1 in grid[0][6].nakshatra_nums

    def test_bharani_position(self):
        """Bharani (SBC 2) must be at row 0, col 7."""
        grid = build_sbc_grid()
        assert 2 in grid[0][7].nakshatra_nums

    def test_krittika_position(self):
        """Krittika (SBC 3) must be at row 1, col 8 (NE, start of East side)."""
        grid = build_sbc_grid()
        assert 3 in grid[1][8].nakshatra_nums

    def test_rohini_position(self):
        """Rohini (SBC 4) must be at row 2, col 8 (East side)."""
        grid = build_sbc_grid()
        assert 4 in grid[2][8].nakshatra_nums

    def test_vishakha_position(self):
        """Vishakha (SBC 16) must be at row 8, col 1 (South side, near SW)."""
        grid = build_sbc_grid()
        assert 16 in grid[8][1].nakshatra_nums

    def test_magha_position(self):
        """Magha (SBC 10) must be at row 8, col 7 (South side, near SE)."""
        grid = build_sbc_grid()
        assert 10 in grid[8][7].nakshatra_nums

    def test_anuradha_position(self):
        """Anuradha (SBC 17) must be at row 7, col 0 (West side, near SW)."""
        grid = build_sbc_grid()
        assert 17 in grid[7][0].nakshatra_nums

    def test_shravana_position(self):
        """Shravana (SBC 22) must be at row 1, col 0 (West side, near NW)."""
        grid = build_sbc_grid()
        assert 22 in grid[1][0].nakshatra_nums

    def test_abhijit_position(self):
        """Abhijit (SBC 28) must be at row 2, col 0 (between Uttara Ashadha and Shravana)."""
        grid = build_sbc_grid()
        cell = grid[2][0]
        assert 28 in cell.nakshatra_nums
        assert "Abhijit" in cell.nakshatra_names

    def test_revati_position(self):
        """Revati (SBC 27) must be at row 0, col 5."""
        grid = build_sbc_grid()
        assert 27 in grid[0][5].nakshatra_nums


# ── Vedha geometry tests ──────────────────────────────────────────────────────


class TestVedhaGeometry:
    def test_across_vedha_returns_16_cells(self):
        """Across vedha from any non-edge cell must return 8 (row) + 8 (col) = 16 cells."""
        result = compute_sbc_vedha("Jupiter", 3)  # Rohini at (2,8) is on edge
        # Rohini is on the right edge (col 8): row has 8 others, col has 8 others = 16
        assert len(result.across_vedha) == 16

    def test_across_vedha_excludes_planet_cell(self):
        """Planet's own cell must NOT appear in across_vedha."""
        result = compute_sbc_vedha("Saturn", 3)  # Rohini at (2,8)
        for cell in result.across_vedha:
            assert not (cell.row == result.planet_row and cell.col == result.planet_col)

    def test_across_vedha_no_duplicate_cells(self):
        """No cell should appear twice in across_vedha."""
        result = compute_sbc_vedha("Mars", 0)  # Ashwini at (0,6)
        positions = [(c.row, c.col) for c in result.across_vedha]
        assert len(positions) == len(set(positions))

    def test_fore_vedha_is_slash_diagonal(self):
        """Fore vedha cells must all lie on the / diagonal through the planet's cell."""
        result = compute_sbc_vedha("Jupiter", 5)  # Ardra at (4,8)
        pr, pc = result.planet_row, result.planet_col
        for cell in result.fore_vedha:
            # / diagonal: row + col = constant (= pr + pc for the planet's diagonal)
            assert cell.row + cell.col == pr + pc

    def test_hind_vedha_is_backslash_diagonal(self):
        """Hind vedha cells must all lie on the \\ diagonal through the planet's cell."""
        result = compute_sbc_vedha("Saturn", 15)  # Vishakha at (8,1)
        pr, pc = result.planet_row, result.planet_col
        for cell in result.hind_vedha:
            # \\ diagonal: row - col = constant (= pr - pc for the planet's diagonal)
            assert cell.row - cell.col == pr - pc

    def test_fore_vedha_excludes_planet_cell(self):
        """Planet's own cell must NOT appear in fore_vedha."""
        result = compute_sbc_vedha("Venus", 8)  # Ashlesha at (7,8)
        for cell in result.fore_vedha:
            assert not (cell.row == result.planet_row and cell.col == result.planet_col)

    def test_hind_vedha_excludes_planet_cell(self):
        """Planet's own cell must NOT appear in hind_vedha."""
        result = compute_sbc_vedha("Rahu", 22)  # Dhanishtha at (0,1)
        for cell in result.hind_vedha:
            assert not (cell.row == result.planet_row and cell.col == result.planet_col)

    def test_corner_cell_has_limited_diagonal(self):
        """A nakshatra at an outer corner yields fewer diagonal cells."""
        # Bharani at (0,7): fore (/) diagonal goes lower-left only → limited
        result = compute_sbc_vedha("Moon", 1)  # Bharani at (0,7)
        # Upper-right from (0,7): (row-1,col+1) → (-1,8) out of bounds → 0 cells
        # Lower-left from (0,7): (1,6),(2,5),(3,4),(4,3),(5,2),(6,1),(7,0) → 7 cells
        assert len(result.fore_vedha) == 7

    def test_center_area_nakshatra_has_full_diagonals(self):
        """A nakshatra roughly central gets more diagonal cells than a corner one."""
        # Ardra at (4,8): hind diagonal goes upper-left+lower-right
        # Upper-left: (3,7),(2,6),(1,5),(0,4) = 4 cells
        # Lower-right: (5,9)→OOB = 0 cells
        result = compute_sbc_vedha("Ketu", 5)  # Ardra at (4,8)
        assert len(result.hind_vedha) == 4


# ── Nakshatra striking tests ──────────────────────────────────────────────────


class TestNakshatraStriking:
    def test_rohini_across_strikes_col8_nakshatras(self):
        """Saturn transiting Rohini (col 8) should strike other col-8 nakshatras.

        Col 8 holds: Krittika(3), Rohini(4), Mrigashira(5), Ardra(6),
                     Punarvasu(7), Pushya(8), Ashlesha(9).
        Across vedha on col 8 (excluding Rohini itself) must include
        Krittika, Mrigashira, Ardra, Punarvasu, Pushya, Ashlesha.
        """
        result = compute_sbc_vedha("Saturn", 3)  # Rohini = index 3
        expected = {"Krittika", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha"}
        struck = set(result.struck_nakshatras_across)
        assert expected.issubset(struck)

    def test_rohini_across_strikes_row2_abhijit(self):
        """Rohini at (2,8): across vedha's row-2 cells should include Abhijit at (2,0)."""
        result = compute_sbc_vedha("Mars", 3)  # Rohini
        assert "Abhijit" in result.struck_nakshatras_across

    def test_struck_nakshatras_are_strings(self):
        """Struck nakshatra lists must contain strings (names), not integers."""
        result = compute_sbc_vedha("Jupiter", 0)
        for name in result.struck_nakshatras_across:
            assert isinstance(name, str)
        for name in result.struck_nakshatras_fore:
            assert isinstance(name, str)

    def test_struck_tithis_are_valid_group_names(self):
        """struck_tithis_across must only contain valid tithi group names."""
        valid = {"Nanda", "Bhadra", "Jaya", "Rikta", "Purna"}
        result = compute_sbc_vedha("Saturn", 10)  # Purva Phalguni at (8,6)
        for group in result.struck_tithis_across:
            assert group in valid

    def test_struck_varas_are_valid_day_names(self):
        """struck_varas_across must only contain valid weekday names."""
        valid = {
            "Sunday", "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday",
        }
        result = compute_sbc_vedha("Venus", 6)  # Punarvasu at (5,8)
        for vara in result.struck_varas_across:
            assert vara in valid

    def test_is_nakshatra_struck_true_when_in_across(self):
        """is_nakshatra_struck returns True when nakshatra is in across vedha."""
        result = compute_sbc_vedha("Saturn", 3)  # Rohini at (2,8)
        # Ashlesha (index 8) is on col 8 → struck across
        assert is_nakshatra_struck(result, 8, ["across"])

    def test_is_nakshatra_struck_false_when_absent(self):
        """is_nakshatra_struck returns False when nakshatra is not struck."""
        result = compute_sbc_vedha("Saturn", 3)  # Rohini at (2,8)
        # Rohini itself (index 3) is not in its own vedha
        assert not is_nakshatra_struck(result, 3)

    def test_is_nakshatra_struck_checks_all_types_by_default(self):
        """With no vedha_types argument, all three types are checked."""
        result = compute_sbc_vedha("Jupiter", 0)  # Ashwini at (0,6)
        # fore vedha from (0,6): lower-left cells (1,5),(2,4),(3,3),(4,2),(5,1),(6,0)
        # (4,2) = rashi 9 cell — no nakshatra; (6,0)=Jyeshtha(18, index 17)
        assert is_nakshatra_struck(result, 17)  # Jyeshtha via fore vedha


# ── All nakshatras produce valid results (parametrized) ───────────────────────


class TestAllNakshatrasCoverage:
    @pytest.mark.parametrize("idx", range(27))
    def test_all_27_nakshatras_produce_valid_result(self, idx: int):
        """Every valid nakshatra index (0-26) must produce a well-formed result."""
        result = compute_sbc_vedha("Sun", idx)
        assert isinstance(result, SBCVedhaResult)
        assert result.transit_nakshatra == NAKSHATRAS[idx]
        assert result.transit_nakshatra_num == idx + 1
        assert 0 <= result.planet_row <= 8
        assert 0 <= result.planet_col <= 8
        # Across vedha is always 16 cells (8 row + 8 col, planet excluded)
        assert len(result.across_vedha) == 16


# ── Boundary and error tests ──────────────────────────────────────────────────


class TestBoundaryAndErrors:
    def test_index_27_raises_value_error(self):
        """Index 27 is out of range (only 0-26 are valid standard nakshatras)."""
        with pytest.raises(ValueError, match="0-26"):
            compute_sbc_vedha("Jupiter", 27)

    def test_negative_index_raises_value_error(self):
        """Negative index must raise ValueError."""
        with pytest.raises(ValueError, match="0-26"):
            compute_sbc_vedha("Saturn", -1)

    def test_is_nakshatra_struck_invalid_index_raises(self):
        """is_nakshatra_struck with out-of-range index raises ValueError."""
        result = compute_sbc_vedha("Moon", 0)
        with pytest.raises(ValueError, match="0-26"):
            is_nakshatra_struck(result, 27)

    def test_index_0_ashwini_works(self):
        """Boundary: index 0 (Ashwini) must work without error."""
        result = compute_sbc_vedha("Sun", 0)
        assert result.transit_nakshatra == "Ashwini"

    def test_index_26_revati_works(self):
        """Boundary: index 26 (Revati) must work without error."""
        result = compute_sbc_vedha("Moon", 26)
        assert result.transit_nakshatra == "Revati"

    def test_result_is_frozen(self):
        """SBCVedhaResult and SBCCell are frozen -- mutation must raise."""
        from pydantic import ValidationError

        result = compute_sbc_vedha("Saturn", 5)
        with pytest.raises(ValidationError):
            result.transit_planet = "Jupiter"  # type: ignore[misc]
