"""Tests for Rasi (sign-based) Dasha systems: Sthira, Shoola, Mandooka."""

from __future__ import annotations

import pytest

from daivai_engine.compute.dasha_rasi import (
    _mandooka_sign_sequence,
    compute_mandooka_dasha,
    compute_shoola_dasha,
    compute_sthira_dasha,
    get_shoola_maraka_signs,
)
from daivai_engine.constants import (
    MANDOOKA_SIGN_YEARS,
    MANDOOKA_TOTAL_YEARS,
    SHOOLA_TOTAL_YEARS,
    STHIRA_DASHA_YEARS,
    STHIRA_TOTAL_YEARS,
)


# ── Sthira Dasha ─────────────────────────────────────────────────────────────


class TestSthiraDasha:
    def test_twelve_periods(self, manish_chart):
        """Sthira Dasha must yield exactly 12 sign-based periods."""
        periods = compute_sthira_dasha(manish_chart)
        assert len(periods) == 12

    def test_all_signs_covered(self, manish_chart):
        """All 12 sign indices must appear exactly once."""
        periods = compute_sthira_dasha(manish_chart)
        sign_indices = [p.sign_index for p in periods]
        assert sorted(sign_indices) == list(range(12))

    def test_years_match_sign_type(self, manish_chart):
        """Each period's years must match the STHIRA_DASHA_YEARS constant.

        Chara signs → 7 yrs, Sthira signs → 8 yrs, Dwiswabhava → 9 yrs.
        """
        periods = compute_sthira_dasha(manish_chart)
        for p in periods:
            assert p.years == STHIRA_DASHA_YEARS[p.sign_index], (
                f"Sign {p.sign} (idx {p.sign_index}) expected "
                f"{STHIRA_DASHA_YEARS[p.sign_index]} yrs, got {p.years}"
            )

    def test_total_96_years(self):
        """Sthira Dasha canonical sum: 4x7 + 4x8 + 4x9 = 96."""
        total = sum(STHIRA_DASHA_YEARS.values())
        assert total == STHIRA_TOTAL_YEARS == 96

    def test_contiguous_periods(self, manish_chart):
        """Each period must start exactly where the previous one ended."""
        periods = compute_sthira_dasha(manish_chart)
        for i in range(1, len(periods)):
            gap = abs((periods[i].start - periods[i - 1].end).total_seconds())
            assert gap < 60, f"Gap between period {i-1} and {i}: {gap}s"

    def test_mithuna_lagna_forward_progression(self, manish_chart):
        """Mithuna lagna (index 2, even/odd) must go forward.

        Mithuna index=2 (Sanskrit 3rd sign = odd) → forward direction.
        First period should be Mithuna itself.
        """
        periods = compute_sthira_dasha(manish_chart)
        assert manish_chart.lagna_sign_index == 2, "Expected Mithuna lagna"
        assert periods[0].sign_index == 2, (
            f"Mithuna lagna forward: first sign should be Mithuna(2), "
            f"got {periods[0].sign}"
        )

    def test_antardasha_12_sub_periods(self, manish_chart):
        """Each Mahadasha must contain 12 Antardasha sub-periods."""
        periods = compute_sthira_dasha(manish_chart)
        for p in periods:
            assert len(p.antardasha) == 12, (
                f"MD {p.sign} should have 12 ADs, got {len(p.antardasha)}"
            )

    def test_antardasha_contiguous(self, manish_chart):
        """Antardashas within each MD must be contiguous."""
        periods = compute_sthira_dasha(manish_chart)
        md = periods[0]
        for i in range(1, len(md.antardasha)):
            gap = abs((md.antardasha[i].start - md.antardasha[i - 1].end).total_seconds())
            assert gap < 60


# ── Shoola Dasha ─────────────────────────────────────────────────────────────


class TestShoolaDasha:
    def test_twelve_periods(self, manish_chart):
        """Shoola Dasha must yield exactly 12 periods."""
        periods = compute_shoola_dasha(manish_chart)
        assert len(periods) == 12

    def test_all_signs_covered(self, manish_chart):
        """All 12 signs must appear exactly once."""
        periods = compute_shoola_dasha(manish_chart)
        assert sorted(p.sign_index for p in periods) == list(range(12))

    def test_odd_sign_7_years_even_sign_8_years(self, manish_chart):
        """Shoola: odd signs (0-indexed even) → 7 yrs; even signs → 8 yrs."""
        periods = compute_shoola_dasha(manish_chart)
        for p in periods:
            expected = 7 if p.sign_index % 2 == 0 else 8
            assert p.years == expected, (
                f"Shoola sign {p.sign} (idx {p.sign_index}): "
                f"expected {expected} yrs, got {p.years}"
            )

    def test_total_90_years(self):
        """Shoola cycle: 6x7 + 6x8 = 90 years."""
        assert SHOOLA_TOTAL_YEARS == 90

    def test_contiguous_periods(self, manish_chart):
        periods = compute_shoola_dasha(manish_chart)
        for i in range(1, len(periods)):
            gap = abs((periods[i].start - periods[i - 1].end).total_seconds())
            assert gap < 60

    def test_maraka_signs_are_2nd_and_7th(self, manish_chart):
        """Shoola maraka signs must be 2nd and 7th from lagna."""
        maraka = get_shoola_maraka_signs(manish_chart)
        lagna = manish_chart.lagna_sign_index
        assert maraka[0] == (lagna + 1) % 12
        assert maraka[1] == (lagna + 6) % 12

    def test_mithuna_lagna_maraka_karka_and_dhanu(self, manish_chart):
        """Mithuna lagna: 2nd sign=Karka(3), 7th sign=Dhanu(8)."""
        assert manish_chart.lagna_sign_index == 2
        maraka = get_shoola_maraka_signs(manish_chart)
        assert maraka == [3, 8], f"Expected [3, 8], got {maraka}"


# ── Mandooka Dasha ───────────────────────────────────────────────────────────


class TestMandookaDasha:
    def test_twelve_periods(self, manish_chart):
        """Mandooka Dasha must yield exactly 12 periods."""
        periods = compute_mandooka_dasha(manish_chart)
        assert len(periods) == 12

    def test_all_signs_covered(self, manish_chart):
        """All 12 signs must appear exactly once (frog covers every sign)."""
        periods = compute_mandooka_dasha(manish_chart)
        assert sorted(p.sign_index for p in periods) == list(range(12))

    def test_all_periods_7_years(self, manish_chart):
        """Mandooka: every sign lasts exactly 7 years."""
        periods = compute_mandooka_dasha(manish_chart)
        for p in periods:
            assert p.years == MANDOOKA_SIGN_YEARS == 7

    def test_total_84_years(self):
        """Mandooka total = 12 x 7 = 84 years."""
        assert MANDOOKA_TOTAL_YEARS == 84

    def test_contiguous_periods(self, manish_chart):
        periods = compute_mandooka_dasha(manish_chart)
        for i in range(1, len(periods)):
            gap = abs((periods[i].start - periods[i - 1].end).total_seconds())
            assert gap < 60

    def test_starts_from_lagna(self, manish_chart):
        """Mandooka first period must be the lagna sign."""
        periods = compute_mandooka_dasha(manish_chart)
        assert periods[0].sign_index == manish_chart.lagna_sign_index

    def test_frog_jump_alternating_pattern(self, manish_chart):
        """Mandooka visits signs in alternating jump, not consecutive order.

        For Mithuna lagna (idx=2, even index → forward):
        First 6 signs: 2, 4, 6, 8, 10, 0 (every other sign forward)
        Next 6 signs: 3, 5, 7, 9, 11, 1 (the remaining signs)
        """
        lagna = manish_chart.lagna_sign_index  # = 2
        sequence = _mandooka_sign_sequence(lagna)
        # First 6 must be every-other-sign starting from lagna
        expected_first_six = [(lagna + 2 * i) % 12 for i in range(6)]
        assert sequence[:6] == expected_first_six, (
            f"Mandooka first 6 signs wrong: expected {expected_first_six}, "
            f"got {sequence[:6]}"
        )
        # All 12 signs appear exactly once
        assert sorted(sequence) == list(range(12))

    @pytest.mark.parametrize("lagna_idx", [0, 1, 3, 5, 7, 11])
    def test_frog_sequence_covers_all_signs(self, lagna_idx):
        """For any lagna, Mandooka must visit all 12 signs exactly once."""
        sequence = _mandooka_sign_sequence(lagna_idx)
        assert len(sequence) == 12
        assert sorted(sequence) == list(range(12))
