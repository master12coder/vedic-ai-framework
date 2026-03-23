"""Tests for Mudda Dasha (compressed annual Vimshottari) computation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from daivai_engine.compute.mudda_dasha import (
    MuddaDashaPeriod,
    MuddaDashaResult,
    compute_mudda_antardashas,
    compute_mudda_dasha,
    get_active_mudda_dasha,
)
from daivai_engine.constants import DASHA_SEQUENCE, DASHA_TOTAL_YEARS, DASHA_YEARS
from daivai_engine.models.chart import ChartData


_VARSHA_PRAVESH_2026 = datetime(2026, 3, 13, 12, 0, tzinfo=UTC)

_SOLAR_YEAR_DAYS = 365.25


class TestMuddaDashaResult:
    def test_returns_pydantic_model(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(manish_chart, _VARSHA_PRAVESH_2026, 2026)
        assert isinstance(result, MuddaDashaResult)

    def test_year_field_set(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(manish_chart, _VARSHA_PRAVESH_2026, 2026)
        assert result.year == 2026

    def test_first_lord_matches_moon_nakshatra_lord(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(manish_chart, _VARSHA_PRAVESH_2026, 2026)
        assert result.first_lord == manish_chart.planets["Moon"].nakshatra_lord

    def test_moon_nakshatra_non_empty(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(manish_chart, _VARSHA_PRAVESH_2026, 2026)
        assert len(result.moon_nakshatra) > 0

    def test_total_days_is_365_25(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(manish_chart, _VARSHA_PRAVESH_2026, 2026)
        assert abs(result.total_days - _SOLAR_YEAR_DAYS) < 0.01

    def test_periods_count_is_at_most_9(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(manish_chart, _VARSHA_PRAVESH_2026, 2026)
        md_periods = [p for p in result.periods if p.level == "MD"]
        assert 1 <= len(md_periods) <= 9

    def test_all_lords_are_valid_planets(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(manish_chart, _VARSHA_PRAVESH_2026, 2026)
        valid = set(DASHA_SEQUENCE)
        for p in result.periods:
            assert p.lord in valid

    def test_periods_start_with_varsha_pravesh_date(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(manish_chart, _VARSHA_PRAVESH_2026, 2026)
        md_periods = [p for p in result.periods if p.level == "MD"]
        assert md_periods[0].start == _VARSHA_PRAVESH_2026

    def test_periods_are_contiguous(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(manish_chart, _VARSHA_PRAVESH_2026, 2026)
        md_periods = [p for p in result.periods if p.level == "MD"]
        for i in range(1, len(md_periods)):
            assert md_periods[i].start == md_periods[i - 1].end

    def test_period_duration_days_positive(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(manish_chart, _VARSHA_PRAVESH_2026, 2026)
        for p in result.periods:
            assert p.duration_days > 0

    def test_start_date_set_correctly(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(manish_chart, _VARSHA_PRAVESH_2026, 2026)
        assert result.start_date == _VARSHA_PRAVESH_2026


class TestMuddaDashaProportions:
    def test_ketu_dasha_proportion(self, manish_chart: ChartData) -> None:
        """Ketu Mudda = (7/120) * 365.25 ~= 21.31 days."""
        expected_days = (DASHA_YEARS["Ketu"] / DASHA_TOTAL_YEARS) * _SOLAR_YEAR_DAYS
        assert abs(expected_days - 21.31) < 0.1

    def test_venus_dasha_proportion(self, manish_chart: ChartData) -> None:
        """Venus Mudda = (20/120) * 365.25 ~= 60.88 days."""
        expected_days = (DASHA_YEARS["Venus"] / DASHA_TOTAL_YEARS) * _SOLAR_YEAR_DAYS
        assert abs(expected_days - 60.88) < 0.1

    def test_sum_of_all_proportions_equals_year(self) -> None:
        """Sum of all planet Mudda proportions must equal 365.25."""
        total = sum((DASHA_YEARS[p] / DASHA_TOTAL_YEARS) * _SOLAR_YEAR_DAYS for p in DASHA_SEQUENCE)
        assert abs(total - _SOLAR_YEAR_DAYS) < 0.01


class TestMuddaAntardashas:
    def test_antardashas_computed_with_flag(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(
            manish_chart, _VARSHA_PRAVESH_2026, 2026, include_antardashas=True
        )
        ad_periods = [p for p in result.periods if p.level == "AD"]
        assert len(ad_periods) > 0

    def test_each_md_produces_9_ads(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(manish_chart, _VARSHA_PRAVESH_2026, 2026)
        md_periods = [p for p in result.periods if p.level == "MD"]
        # Test just the first MD
        ads = compute_mudda_antardashas(md_periods[0])
        assert len(ads) == 9

    def test_ad_level_is_set(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(manish_chart, _VARSHA_PRAVESH_2026, 2026)
        md_periods = [p for p in result.periods if p.level == "MD"]
        ads = compute_mudda_antardashas(md_periods[0])
        for ad in ads:
            assert ad.level == "AD"

    def test_ad_parent_lord_matches_md(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(manish_chart, _VARSHA_PRAVESH_2026, 2026)
        md_periods = [p for p in result.periods if p.level == "MD"]
        md = md_periods[0]
        ads = compute_mudda_antardashas(md)
        for ad in ads:
            assert ad.parent_lord == md.lord

    def test_ad_periods_contiguous_within_md(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(manish_chart, _VARSHA_PRAVESH_2026, 2026)
        md_periods = [p for p in result.periods if p.level == "MD"]
        ads = compute_mudda_antardashas(md_periods[0])
        for i in range(1, len(ads)):
            assert ads[i].start == ads[i - 1].end


class TestGetActiveMuddaDasha:
    def test_returns_none_before_year_start(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(manish_chart, _VARSHA_PRAVESH_2026, 2026)
        query = datetime(2020, 1, 1, tzinfo=UTC)
        active = get_active_mudda_dasha(result, query)
        assert active is None

    def test_returns_period_during_year(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(manish_chart, _VARSHA_PRAVESH_2026, 2026)
        query = _VARSHA_PRAVESH_2026 + timedelta(days=10)
        active = get_active_mudda_dasha(result, query)
        assert active is not None
        assert isinstance(active, MuddaDashaPeriod)

    def test_active_period_contains_query_date(self, manish_chart: ChartData) -> None:
        result = compute_mudda_dasha(manish_chart, _VARSHA_PRAVESH_2026, 2026)
        query = _VARSHA_PRAVESH_2026 + timedelta(days=30)
        active = get_active_mudda_dasha(result, query)
        assert active is not None
        assert active.start <= query < active.end
