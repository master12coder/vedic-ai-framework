"""Tests for Lo Shu grid construction and arrow pattern detection."""

from __future__ import annotations

from daivai_engine.compute.numerology_loshu import (
    _build_grid,
    _count_digits,
    _detect_arrows,
    _extract_digits,
    build_loshu_grid,
)
from daivai_engine.models.numerology import ArrowPattern, LoShuGrid


class TestExtractDigits:
    """Tests for _extract_digits() — birth date digit extraction."""

    def test_manish_dob_digits(self) -> None:
        # 13/03/1989 → "13031989" → [1,3,3,1,9,8,9] (zero removed)
        digits = _extract_digits(13, 3, 1989)
        assert 0 not in digits

    def test_no_zeros_in_output(self) -> None:
        # Date with zero: 10/01/2000 → "10012000" → [1, 1, 2] (zeros removed)
        digits = _extract_digits(10, 1, 2000)
        assert 0 not in digits

    def test_all_digits_valid_1_to_9(self) -> None:
        digits = _extract_digits(13, 3, 1989)
        for d in digits:
            assert 1 <= d <= 9

    def test_returns_list(self) -> None:
        assert isinstance(_extract_digits(1, 1, 2000), list)

    def test_known_output_for_manish(self) -> None:
        digits = _extract_digits(13, 3, 1989)
        # 1,3,3,1,9,8,9 (from "13031989")
        assert sorted(digits) == sorted([1, 3, 3, 1, 9, 8, 9])


class TestCountDigits:
    """Tests for _count_digits() — occurrence counting."""

    def test_returns_dict_1_to_9(self) -> None:
        counts = _count_digits([1, 2, 3])
        assert set(counts.keys()) == set(range(1, 10))

    def test_all_counts_non_negative(self) -> None:
        counts = _count_digits([1, 3, 3, 1, 9, 8, 9])
        for n in range(1, 10):
            assert counts[n] >= 0

    def test_correct_count_for_manish(self) -> None:
        digits = [1, 3, 3, 1, 9, 8, 9]  # From 13/03/1989
        counts = _count_digits(digits)
        assert counts[1] == 2
        assert counts[3] == 2
        assert counts[9] == 2
        assert counts[8] == 1
        assert counts[5] == 0

    def test_empty_list_gives_all_zeros(self) -> None:
        counts = _count_digits([])
        for n in range(1, 10):
            assert counts[n] == 0


class TestBuildGrid:
    """Tests for _build_grid() — 3x3 Lo Shu grid construction."""

    def test_returns_3x3_list(self) -> None:
        counts = _count_digits([])
        grid = _build_grid(counts)
        assert len(grid) == 3
        for row in grid:
            assert len(row) == 3

    def test_empty_counts_gives_all_zero_grid(self) -> None:
        counts = {n: 0 for n in range(1, 10)}
        grid = _build_grid(counts)
        for row in grid:
            for cell in row:
                assert cell == 0

    def test_position_for_number_5_is_center(self) -> None:
        # Number 5 is at (1,1) in Lo Shu
        counts = {n: 0 for n in range(1, 10)}
        counts[5] = 3
        grid = _build_grid(counts)
        assert grid[1][1] == 3


class TestDetectArrows:
    """Tests for _detect_arrows() — 8 arrow pattern detection."""

    def test_returns_8_arrows(self) -> None:
        counts = _count_digits([1, 2, 3, 4, 5, 6, 7, 8, 9])
        arrows = _detect_arrows(counts)
        assert len(arrows) == 8

    def test_all_arrows_are_arrow_pattern(self) -> None:
        counts = _count_digits([1, 2, 3])
        arrows = _detect_arrows(counts)
        for a in arrows:
            assert isinstance(a, ArrowPattern)

    def test_arrow_with_all_numbers_present_is_present(self) -> None:
        # Make all numbers present
        counts = {n: 1 for n in range(1, 10)}
        arrows = _detect_arrows(counts)
        present_count = sum(1 for a in arrows if a.is_present)
        assert present_count == 8  # All arrows present

    def test_arrow_with_no_numbers_is_missing(self) -> None:
        counts = {n: 0 for n in range(1, 10)}
        arrows = _detect_arrows(counts)
        missing_count = sum(1 for a in arrows if a.is_missing)
        assert missing_count == 8  # All arrows missing

    def test_is_present_and_is_missing_mutually_exclusive(self) -> None:
        counts = _count_digits([1, 3, 3, 1, 9, 8, 9])
        arrows = _detect_arrows(counts)
        for a in arrows:
            assert not (a.is_present and a.is_missing)


class TestBuildLoShuGrid:
    """Integration tests for build_loshu_grid()."""

    def test_returns_loshu_grid(self) -> None:
        result = build_loshu_grid(13, 3, 1989)
        assert isinstance(result, LoShuGrid)

    def test_present_numbers_for_manish(self) -> None:
        # 13/03/1989: digits [1,3,3,1,9,8,9] → present: 1,3,8,9
        result = build_loshu_grid(13, 3, 1989)
        assert 1 in result.present_numbers
        assert 3 in result.present_numbers
        assert 8 in result.present_numbers
        assert 9 in result.present_numbers

    def test_missing_numbers_for_manish(self) -> None:
        # 13/03/1989: 2,4,5,6,7 are missing
        result = build_loshu_grid(13, 3, 1989)
        for missing in [2, 4, 5, 6, 7]:
            assert missing in result.missing_numbers

    def test_present_and_missing_disjoint(self) -> None:
        result = build_loshu_grid(13, 3, 1989)
        assert set(result.present_numbers) & set(result.missing_numbers) == set()

    def test_present_and_missing_cover_1_to_9(self) -> None:
        result = build_loshu_grid(13, 3, 1989)
        all_nums = set(result.present_numbers) | set(result.missing_numbers)
        assert all_nums == set(range(1, 10))

    def test_grid_is_3x3(self) -> None:
        result = build_loshu_grid(1, 1, 2000)
        assert len(result.grid) == 3
        for row in result.grid:
            assert len(row) == 3

    def test_arrows_count_is_8(self) -> None:
        result = build_loshu_grid(13, 3, 1989)
        assert len(result.arrows) == 8

    def test_digit_counts_keys_are_string(self) -> None:
        result = build_loshu_grid(13, 3, 1989)
        for k in result.digit_counts:
            assert isinstance(k, str)
