"""Tests for chart accuracy verification system."""

from __future__ import annotations

from daivai_engine.compute.verify import verify_chart_accuracy
from daivai_engine.models.chart import ChartData


class TestChartVerification:
    def test_manish_chart_passes_all_checks(self, manish_chart: ChartData) -> None:
        """The reference chart should have zero warnings."""
        warnings = verify_chart_accuracy(manish_chart)
        errors = [w for w in warnings if w.startswith("ERROR")]
        assert len(errors) == 0, f"Errors found: {errors}"

    def test_all_longitudes_valid(self, manish_chart: ChartData) -> None:
        warnings = verify_chart_accuracy(manish_chart)
        lon_errors = [w for w in warnings if "longitude" in w and "out of" in w]
        assert len(lon_errors) == 0

    def test_rahu_ketu_180_apart(self, manish_chart: ChartData) -> None:
        warnings = verify_chart_accuracy(manish_chart)
        rk_errors = [w for w in warnings if "Rahu-Ketu" in w]
        assert len(rk_errors) == 0

    def test_combustion_consistency(self, manish_chart: ChartData) -> None:
        warnings = verify_chart_accuracy(manish_chart)
        combust_errors = [w for w in warnings if "combustion" in w]
        assert len(combust_errors) == 0

    def test_ayanamsha_reasonable(self, manish_chart: ChartData) -> None:
        warnings = verify_chart_accuracy(manish_chart)
        ayanamsha_errors = [w for w in warnings if "Ayanamsha" in w]
        assert len(ayanamsha_errors) == 0

    def test_sign_consistency(self, manish_chart: ChartData) -> None:
        warnings = verify_chart_accuracy(manish_chart)
        sign_errors = [w for w in warnings if "sign mismatch" in w]
        assert len(sign_errors) == 0

    def test_retrograde_consistency(self, manish_chart: ChartData) -> None:
        warnings = verify_chart_accuracy(manish_chart)
        retro_errors = [w for w in warnings if "retrograde" in w]
        assert len(retro_errors) == 0

    def test_sample_chart_also_passes(self, sample_chart: ChartData) -> None:
        """Cross-check with a different chart."""
        warnings = verify_chart_accuracy(sample_chart)
        errors = [w for w in warnings if w.startswith("ERROR")]
        assert len(errors) == 0
