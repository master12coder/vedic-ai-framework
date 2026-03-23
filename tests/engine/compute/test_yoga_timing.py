"""Tests for Yoga activation timing — structural and integration tests.

Covers:
  - Structural validity of AllYogaTimings output
  - Individual YogaTimingResult structure
  - Activation period structure and invariants
  - Manish chart integration tests (Jupiter MD activates Jupiter yogas)
  - Model immutability
  - Two charts (Manish reference + sample)

Fixture:
  manish_chart: Mithuna lagna, Moon in Rohini Pada 2.
  Current MD = Jupiter (7th lord / maraka).
"""

from __future__ import annotations

from datetime import datetime

import pytest
import pytz

from daivai_engine.compute.yoga_timing import compute_all_yoga_timings
from daivai_engine.models.chart import ChartData
from daivai_engine.models.yoga_timing import (
    AllYogaTimings,
    YogaActivationPeriod,
    YogaTimingResult,
)


_DATE = datetime(2026, 3, 22, 12, 0, 0, tzinfo=pytz.UTC)


class TestComputeAllYogaTimings:
    """Structural tests for compute_all_yoga_timings()."""

    @pytest.fixture
    def result(self, manish_chart: ChartData) -> AllYogaTimings:
        return compute_all_yoga_timings(manish_chart, _DATE)

    def test_returns_all_yoga_timings(self, result: AllYogaTimings) -> None:
        assert isinstance(result, AllYogaTimings)

    def test_yogas_not_empty(self, result: AllYogaTimings) -> None:
        assert len(result.yogas) > 0

    def test_all_results_typed(self, result: AllYogaTimings) -> None:
        for yt in result.yogas:
            assert isinstance(yt, YogaTimingResult)

    def test_active_names_are_strings(self, result: AllYogaTimings) -> None:
        for name in result.currently_active_yogas:
            assert isinstance(name, str) and len(name) > 0

    def test_active_names_in_results(self, result: AllYogaTimings) -> None:
        all_names = {yt.yoga_name for yt in result.yogas}
        for name in result.currently_active_yogas:
            assert name in all_names

    def test_upcoming_are_tuples(self, result: AllYogaTimings) -> None:
        for item in result.upcoming_activations:
            assert isinstance(item, tuple) and len(item) == 2

    def test_most_significant_valid(self, result: AllYogaTimings) -> None:
        if result.most_significant is not None:
            assert isinstance(result.most_significant, YogaTimingResult)
            assert result.most_significant.strength != "cancelled"

    def test_summary_non_empty(self, result: AllYogaTimings) -> None:
        assert len(result.summary) > 0

    def test_second_chart(self, sample_chart: ChartData) -> None:
        result = compute_all_yoga_timings(sample_chart, _DATE)
        assert isinstance(result, AllYogaTimings)


class TestYogaTimingResultStructure:
    """Structural tests for individual YogaTimingResult."""

    @pytest.fixture
    def first_yoga(self, manish_chart: ChartData) -> YogaTimingResult:
        result = compute_all_yoga_timings(manish_chart, _DATE)
        assert len(result.yogas) > 0
        return result.yogas[0]

    def test_name_non_empty(self, first_yoga: YogaTimingResult) -> None:
        assert len(first_yoga.yoga_name) > 0

    def test_planets_non_empty(self, first_yoga: YogaTimingResult) -> None:
        assert len(first_yoga.planets_involved) > 0

    def test_effect_valid(self, first_yoga: YogaTimingResult) -> None:
        assert first_yoga.effect in ("benefic", "malefic", "mixed")

    def test_strength_valid(self, first_yoga: YogaTimingResult) -> None:
        assert first_yoga.strength in ("full", "partial", "cancelled", "enhanced")

    def test_years_non_negative(self, first_yoga: YogaTimingResult) -> None:
        assert first_yoga.total_activation_years >= 0.0

    def test_active_is_bool(self, first_yoga: YogaTimingResult) -> None:
        assert isinstance(first_yoga.is_currently_active, bool)

    def test_strength_when_active(self, first_yoga: YogaTimingResult) -> None:
        if first_yoga.is_currently_active:
            assert first_yoga.current_activation_strength in ("primary", "secondary", "dual")
        else:
            assert first_yoga.current_activation_strength is None

    def test_summary(self, first_yoga: YogaTimingResult) -> None:
        assert len(first_yoga.summary) > 0


class TestActivationPeriodStructure:
    """Structural tests for YogaActivationPeriod."""

    @pytest.fixture
    def periods(self, manish_chart: ChartData) -> list[YogaActivationPeriod]:
        result = compute_all_yoga_timings(manish_chart, _DATE)
        all_p: list[YogaActivationPeriod] = []
        for yt in result.yogas:
            all_p.extend(yt.activation_periods)
        return all_p

    def test_periods_exist(self, periods: list[YogaActivationPeriod]) -> None:
        assert len(periods) > 0

    def test_dasha_level_valid(self, periods: list[YogaActivationPeriod]) -> None:
        for p in periods:
            assert p.dasha_level in {"MD", "AD", "MD-AD"}

    def test_activation_strength_valid(self, periods: list[YogaActivationPeriod]) -> None:
        for p in periods:
            assert p.activation_strength in {"primary", "secondary", "dual"}

    def test_start_before_end(self, periods: list[YogaActivationPeriod]) -> None:
        for p in periods:
            assert p.start < p.end

    def test_dual_has_parent(self, periods: list[YogaActivationPeriod]) -> None:
        for p in periods:
            if p.activation_strength == "dual":
                assert p.parent_lord is not None

    def test_secondary_has_parent(self, periods: list[YogaActivationPeriod]) -> None:
        for p in periods:
            if p.activation_strength == "secondary":
                assert p.parent_lord is not None


class TestManishChartIntegration:
    """Integration tests using Manish chart — known values."""

    @pytest.fixture
    def result(self, manish_chart: ChartData) -> AllYogaTimings:
        return compute_all_yoga_timings(manish_chart, _DATE)

    def test_has_yogas(self, result: AllYogaTimings) -> None:
        assert len(result.yogas) > 0

    def test_jupiter_md_activates_jupiter_yogas(self, result: AllYogaTimings) -> None:
        for yt in result.yogas:
            if "Jupiter" in yt.planets_involved:
                assert yt.is_currently_active, (
                    f"'{yt.yoga_name}' involves Jupiter but not active in Jupiter MD"
                )

    def test_activation_years_positive(self, result: AllYogaTimings) -> None:
        total = sum(yt.total_activation_years for yt in result.yogas)
        assert total > 0

    def test_upcoming_have_descriptions(self, result: AllYogaTimings) -> None:
        for _, desc in result.upcoming_activations:
            assert len(desc) > 0


class TestModelFrozen:
    """Pydantic models should be frozen."""

    def test_all_timings_frozen(self, manish_chart: ChartData) -> None:
        result = compute_all_yoga_timings(manish_chart, _DATE)
        with pytest.raises((TypeError, Exception)):
            result.summary = "hacked"  # type: ignore[misc]

    def test_timing_result_frozen(self, manish_chart: ChartData) -> None:
        result = compute_all_yoga_timings(manish_chart, _DATE)
        if result.yogas:
            with pytest.raises((TypeError, Exception)):
                result.yogas[0].yoga_name = "hacked"  # type: ignore[misc]

    def test_activation_period_frozen(self, manish_chart: ChartData) -> None:
        result = compute_all_yoga_timings(manish_chart, _DATE)
        for yt in result.yogas:
            if yt.activation_periods:
                with pytest.raises((TypeError, Exception)):
                    yt.activation_periods[0].lord = "hacked"  # type: ignore[misc]
                break
