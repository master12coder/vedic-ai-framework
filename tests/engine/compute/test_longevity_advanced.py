"""Tests for the upgraded longevity (Ayurdaya) module — all 3 classical methods."""

from __future__ import annotations

from daivai_engine.compute.longevity import (
    LongevityResult,
    _compute_amshayu,
    _compute_naisargika,
    _compute_pindayu,
    compute_longevity,
)
from daivai_engine.models.chart import ChartData


class TestPindayu:
    def test_pindayu_returns_positive(self, manish_chart: ChartData) -> None:
        years, _ = _compute_pindayu(manish_chart)
        assert years > 0

    def test_pindayu_max_120(self, manish_chart: ChartData) -> None:
        years, _ = _compute_pindayu(manish_chart)
        assert years <= 120.0

    def test_pindayu_has_seven_planets(self, manish_chart: ChartData) -> None:
        _, breakdown = _compute_pindayu(manish_chart)
        assert len(breakdown) == 7

    def test_pindayu_all_values_positive(self, manish_chart: ChartData) -> None:
        _, breakdown = _compute_pindayu(manish_chart)
        for planet, years in breakdown.items():
            assert years > 0, f"{planet} should have positive years"


class TestAmshayu:
    def test_amshayu_returns_positive(self, manish_chart: ChartData) -> None:
        years, _ = _compute_amshayu(manish_chart)
        assert years > 0

    def test_amshayu_max_150(self, manish_chart: ChartData) -> None:
        """Amshayu uses a 150-year ceiling, not 120."""
        years, _ = _compute_amshayu(manish_chart)
        assert years <= 150.0

    def test_amshayu_has_seven_planets(self, manish_chart: ChartData) -> None:
        _, breakdown = _compute_amshayu(manish_chart)
        assert len(breakdown) == 7

    def test_amshayu_uses_navamsha_ceiling(self, manish_chart: ChartData) -> None:
        """Amshayu has a 150-year ceiling, distinct from Pindayu's 120-year ceiling."""
        amshayu, breakdown = _compute_amshayu(manish_chart)
        # Navamsha method ran and produced 7-planet breakdown
        assert len(breakdown) == 7
        # The method applies its own ceiling
        assert amshayu <= 150.0


class TestNaisargika:
    def test_naisargika_returns_positive(self, manish_chart: ChartData) -> None:
        years = _compute_naisargika(manish_chart)
        assert years > 0

    def test_naisargika_max_120(self, manish_chart: ChartData) -> None:
        years = _compute_naisargika(manish_chart)
        assert years <= 120.0


class TestComputeLongevity:
    def test_all_three_fields_present(self, manish_chart: ChartData) -> None:
        result = compute_longevity(manish_chart)
        assert isinstance(result, LongevityResult)
        assert result.pindayu_years > 0
        assert result.amshayu_years > 0
        assert result.naisargika_years > 0

    def test_composite_years_in_range(self, manish_chart: ChartData) -> None:
        result = compute_longevity(manish_chart)
        assert 0 < result.composite_years <= 120.0

    def test_valid_category(self, manish_chart: ChartData) -> None:
        result = compute_longevity(manish_chart)
        assert result.category in ("alpayu", "madhyayu", "poornayu")

    def test_valid_hindi_category(self, manish_chart: ChartData) -> None:
        result = compute_longevity(manish_chart)
        assert result.category_hi in ("अल्पायु", "मध्यायु", "पूर्णायु")

    def test_valid_confidence(self, manish_chart: ChartData) -> None:
        result = compute_longevity(manish_chart)
        assert result.confidence in ("high", "medium", "low")

    def test_valid_method_agreement(self, manish_chart: ChartData) -> None:
        result = compute_longevity(manish_chart)
        assert result.method_agreement in ("all_agree", "two_agree", "disagree")

    def test_amshayu_breakdown_seven_planets(self, manish_chart: ChartData) -> None:
        result = compute_longevity(manish_chart)
        assert len(result.amshayu_breakdown) == 7

    def test_pindayu_breakdown_seven_planets(self, manish_chart: ChartData) -> None:
        result = compute_longevity(manish_chart)
        assert len(result.breakdown) == 7
