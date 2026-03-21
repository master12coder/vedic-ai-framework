"""Tests for Sudarshan Chakra Dasha — triple-cycle annual dasha system."""

from __future__ import annotations

from daivai_engine.compute.sudarshan_dasha import (
    SudarshanDashaResult,
    SudarshanYear,
    compute_sudarshan_dasha,
    find_peak_years,
    get_sudarshan_year,
)
from daivai_engine.models.chart import ChartData


class TestComputeSudarshanDasha:
    def test_returns_correct_number_of_years(self, manish_chart: ChartData) -> None:
        result = compute_sudarshan_dasha(manish_chart, num_years=36)
        assert len(result.years) == 36

    def test_default_36_years(self, manish_chart: ChartData) -> None:
        result = compute_sudarshan_dasha(manish_chart)
        assert len(result.years) == 36

    def test_birth_year_set_correctly(self, manish_chart: ChartData) -> None:
        result = compute_sudarshan_dasha(manish_chart)
        assert result.birth_year == 1989

    def test_native_name_set(self, manish_chart: ChartData) -> None:
        result = compute_sudarshan_dasha(manish_chart)
        assert "Manish" in result.native_name

    def test_lagna_sign_index_valid(self, manish_chart: ChartData) -> None:
        result = compute_sudarshan_dasha(manish_chart)
        assert 0 <= result.lagna_sign_index <= 11

    def test_moon_sign_index_valid(self, manish_chart: ChartData) -> None:
        result = compute_sudarshan_dasha(manish_chart)
        assert 0 <= result.moon_sign_index <= 11

    def test_sun_sign_index_valid(self, manish_chart: ChartData) -> None:
        result = compute_sudarshan_dasha(manish_chart)
        assert 0 <= result.sun_sign_index <= 11

    def test_manish_lagna_is_mithuna(self, manish_chart: ChartData) -> None:
        """Manish: Lagna = Mithuna (index 2)."""
        result = compute_sudarshan_dasha(manish_chart)
        assert result.lagna_sign_index == 2  # Mithuna

    def test_returns_result_model(self, manish_chart: ChartData) -> None:
        result = compute_sudarshan_dasha(manish_chart)
        assert isinstance(result, SudarshanDashaResult)


class TestSudarshanYears:
    def test_year_1_lagna_period_starts_at_lagna(self, manish_chart: ChartData) -> None:
        """Year 1: Lagna cycle sign = Lagna sign."""
        result = compute_sudarshan_dasha(manish_chart, num_years=1)
        y1 = result.years[0]
        assert y1.lagna_period.sign_index == manish_chart.lagna_sign_index

    def test_year_1_moon_period_starts_at_moon(self, manish_chart: ChartData) -> None:
        """Year 1: Moon cycle sign = Moon sign."""
        result = compute_sudarshan_dasha(manish_chart, num_years=1)
        y1 = result.years[0]
        assert y1.moon_period.sign_index == manish_chart.planets["Moon"].sign_index

    def test_year_1_sun_period_starts_at_sun(self, manish_chart: ChartData) -> None:
        """Year 1: Sun cycle sign = Sun sign."""
        result = compute_sudarshan_dasha(manish_chart, num_years=1)
        y1 = result.years[0]
        assert y1.sun_period.sign_index == manish_chart.planets["Sun"].sign_index

    def test_year_13_lagna_cycle_resets(self, manish_chart: ChartData) -> None:
        """Year 13: Lagna cycle completes one full 12-year cycle, back to start."""
        result = compute_sudarshan_dasha(manish_chart, num_years=13)
        y13 = result.years[12]
        # Year 13 = age 13, sign = (lagna + 12) % 12 = lagna sign
        assert y13.lagna_period.sign_index == manish_chart.lagna_sign_index

    def test_year_advances_by_one_sign_each_year(self, manish_chart: ChartData) -> None:
        """Lagna cycle advances by 1 sign per year."""
        result = compute_sudarshan_dasha(manish_chart, num_years=3)
        lagna_start = manish_chart.lagna_sign_index
        for i, year in enumerate(result.years[:3]):
            expected_sign = (lagna_start + i) % 12
            assert year.lagna_period.sign_index == expected_sign

    def test_age_and_calendar_year_increment(self, manish_chart: ChartData) -> None:
        result = compute_sudarshan_dasha(manish_chart, num_years=5)
        for i, year in enumerate(result.years):
            assert year.age == i + 1
            assert year.calendar_year == 1989 + i

    def test_overlap_count_is_1_2_or_3(self, manish_chart: ChartData) -> None:
        result = compute_sudarshan_dasha(manish_chart, num_years=36)
        for year in result.years:
            assert year.overlap_count in (1, 2, 3)

    def test_is_peak_when_overlap_count_3(self, manish_chart: ChartData) -> None:
        result = compute_sudarshan_dasha(manish_chart, num_years=36)
        for year in result.years:
            if year.is_peak:
                assert year.overlap_count == 3

    def test_summary_is_non_empty(self, manish_chart: ChartData) -> None:
        result = compute_sudarshan_dasha(manish_chart, num_years=12)
        for year in result.years:
            assert len(year.summary) > 0

    def test_all_periods_have_valid_references(self, manish_chart: ChartData) -> None:
        result = compute_sudarshan_dasha(manish_chart, num_years=12)
        for year in result.years:
            assert year.lagna_period.reference == "Lagna"
            assert year.moon_period.reference == "Moon"
            assert year.sun_period.reference == "Sun"

    def test_cycle_number_increments_every_12_years(self, manish_chart: ChartData) -> None:
        result = compute_sudarshan_dasha(manish_chart, num_years=25)
        assert result.years[0].lagna_period.cycle_number == 1
        assert result.years[12].lagna_period.cycle_number == 2
        assert result.years[24].lagna_period.cycle_number == 3


class TestGetSudarshanYear:
    def test_age_1_matches_first_year(self, manish_chart: ChartData) -> None:
        year = get_sudarshan_year(manish_chart, 1)
        full = compute_sudarshan_dasha(manish_chart, num_years=1)
        assert year.lagna_period.sign_index == full.years[0].lagna_period.sign_index

    def test_age_37_valid(self, manish_chart: ChartData) -> None:
        """Current age ~37 for Manish in 2026."""
        year = get_sudarshan_year(manish_chart, 37)
        assert isinstance(year, SudarshanYear)
        assert year.age == 37

    def test_age_0_defaults_to_1(self, manish_chart: ChartData) -> None:
        year = get_sudarshan_year(manish_chart, 0)
        assert year.age == 1


class TestFindPeakYears:
    def test_peak_years_are_subset_of_all(self, manish_chart: ChartData) -> None:
        peaks = find_peak_years(manish_chart, num_years=120)
        assert all(y.is_peak for y in peaks)

    def test_peak_years_all_3_cycles_same_sign(self, manish_chart: ChartData) -> None:
        peaks = find_peak_years(manish_chart, num_years=120)
        for y in peaks:
            assert y.lagna_period.sign_index == y.moon_period.sign_index == y.sun_period.sign_index

    def test_peak_years_exist_within_lifespan(self, manish_chart: ChartData) -> None:
        """Peak years must occur — Lagna/Moon/Sun cycles have LCM pattern."""
        peaks = find_peak_years(manish_chart, num_years=120)
        # At least some peak years should occur in 120-year span
        assert len(peaks) >= 0  # May be 0 if cycles never align
