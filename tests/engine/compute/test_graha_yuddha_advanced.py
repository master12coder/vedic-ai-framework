"""Tests for upgraded Graha Yuddha — latitude-based winner determination."""

from __future__ import annotations

from daivai_engine.compute.graha_yuddha import (
    _BRIGHTNESS_RANK,
    _WAR_PLANETS,
    _circular_distance,
    detect_planetary_war,
)
from daivai_engine.models.chart import ChartData


class TestGrahaYuddhaBrightnessRank:
    def test_brightness_rank_has_five_planets(self) -> None:
        assert len(_BRIGHTNESS_RANK) == 5

    def test_venus_is_brightest(self) -> None:
        """Venus has the lowest rank value (= brightest)."""
        assert _BRIGHTNESS_RANK["Venus"] == 1

    def test_saturn_is_dimmest(self) -> None:
        """Saturn has the highest rank value (= dimmest)."""
        assert _BRIGHTNESS_RANK["Saturn"] == 5

    def test_all_war_planets_in_brightness_rank(self) -> None:
        for p in _WAR_PLANETS:
            assert p in _BRIGHTNESS_RANK, f"{p} missing from brightness rank"


class TestGrahaYuddhaDetection:
    def test_winner_loser_from_chart(self, manish_chart: ChartData) -> None:
        """Winner and loser should always differ and be valid planets."""
        wars = detect_planetary_war(manish_chart)
        for w in wars:
            assert w.winner != w.loser
            assert w.winner in _WAR_PLANETS
            assert w.loser in _WAR_PLANETS

    def test_no_sun_moon_rahu_ketu_in_war(self, manish_chart: ChartData) -> None:
        wars = detect_planetary_war(manish_chart)
        for w in wars:
            for excluded in ("Sun", "Moon", "Rahu", "Ketu"):
                assert w.planet1 != excluded
                assert w.planet2 != excluded

    def test_separation_within_threshold(self, manish_chart: ChartData) -> None:
        wars = detect_planetary_war(manish_chart)
        for w in wars:
            assert w.separation_degrees <= 1.0

    def test_affected_houses_valid(self, manish_chart: ChartData) -> None:
        wars = detect_planetary_war(manish_chart)
        for w in wars:
            assert len(w.affected_houses) > 0
            for h in w.affected_houses:
                assert 1 <= h <= 12


class TestCircularDistance:
    def test_same_longitude_is_zero(self) -> None:
        assert _circular_distance(45.0, 45.0) == 0.0

    def test_opposite_is_180(self) -> None:
        assert _circular_distance(0.0, 180.0) == 180.0

    def test_wrap_around_gives_correct_distance(self) -> None:
        """358° and 2° are 4° apart, not 356°."""
        assert abs(_circular_distance(358.0, 2.0) - 4.0) < 0.001

    def test_order_doesnt_matter(self) -> None:
        """Distance should be symmetric."""
        d1 = _circular_distance(30.0, 350.0)
        d2 = _circular_distance(350.0, 30.0)
        assert abs(d1 - d2) < 0.001
