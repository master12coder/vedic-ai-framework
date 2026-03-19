"""Tests for gandanta detection."""

from __future__ import annotations

from daivai_engine.compute.gandanta import check_gandanta
from daivai_engine.models.chart import ChartData


class TestGandanta:
    def test_moon_not_gandanta_for_manish(self, manish_chart: ChartData) -> None:
        """Moon at ~14.7 deg Taurus is NOT in a gandanta zone."""
        results = check_gandanta(manish_chart)
        moon_result = next(r for r in results if r.planet == "Moon")
        assert not moon_result.is_gandanta

    def test_returns_result_for_every_planet(self, manish_chart: ChartData) -> None:
        results = check_gandanta(manish_chart)
        assert len(results) == 9  # All 9 planets

    def test_all_planets_checked(self, manish_chart: ChartData) -> None:
        results = check_gandanta(manish_chart)
        names = {r.planet for r in results}
        assert "Sun" in names
        assert "Moon" in names
        assert "Rahu" in names

    def test_gandanta_detected_at_cancer_leo_junction(
        self, manish_chart: ChartData
    ) -> None:
        """Synthetic: if Moon were at 28 deg Cancer, should be gandanta."""
        # Modify Moon to be at end of Cancer (sign index 3, ~28 deg)
        from daivai_engine.compute.gandanta import _check_one

        result = _check_one("Moon", 3, 28.0)  # Cancer, 28 degrees
        assert result.is_gandanta
        assert result.junction == "Ashlesha-Magha"
        assert result.severity == "mild"

    def test_severe_gandanta_at_exact_junction(self) -> None:
        """Within 1 deg of junction = severe."""
        from daivai_engine.compute.gandanta import _check_one

        result = _check_one("Moon", 3, 29.5)  # Cancer, 29.5 degrees
        assert result.is_gandanta
        assert result.severity == "severe"

    def test_fire_sign_start_gandanta(self) -> None:
        """Planet at 1 deg Sagittarius (fire sign after Scorpio)."""
        from daivai_engine.compute.gandanta import _check_one

        result = _check_one("Mars", 8, 1.0)  # Sagittarius, 1 degree
        assert result.is_gandanta
        assert result.junction == "Jyeshtha-Moola"
        assert result.severity == "mild"  # 1 deg < 3.33 zone but > 1 deg threshold

    def test_fire_sign_start_severe(self) -> None:
        """Planet at 0.5 deg Sagittarius = severe gandanta."""
        from daivai_engine.compute.gandanta import _check_one

        result = _check_one("Mars", 8, 0.5)
        assert result.is_gandanta
        assert result.severity == "severe"

    def test_not_gandanta_in_middle_of_sign(self) -> None:
        from daivai_engine.compute.gandanta import _check_one

        result = _check_one("Saturn", 7, 15.0)  # Scorpio, 15 degrees
        assert not result.is_gandanta
