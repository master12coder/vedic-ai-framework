"""Tests for Cazimi (in heart of Sun) detection.

Cazimi = planet within 17 arc-minutes of Sun = extremely powerful, NOT weakened.
Combust = planet within combustion limit but outside 17' = weakened.

Fixture: Manish Chaurasia — 13/03/1989, 12:17 PM, Varanasi
"""

from __future__ import annotations

import pytest

from daivai_engine.compute.chart import _check_combustion
from daivai_engine.constants import CAZIMI_LIMIT, COMBUSTION_LIMITS
from daivai_engine.models.chart import ChartData


class TestCazimiConstant:
    """Tests for the CAZIMI_LIMIT constant."""

    def test_cazimi_limit_is_17_arcminutes(self) -> None:
        """CAZIMI_LIMIT must be exactly 17/60 degrees."""
        expected = 17.0 / 60.0
        assert abs(CAZIMI_LIMIT - expected) < 1e-9

    def test_cazimi_limit_less_than_all_combustion_limits(self) -> None:
        """Cazimi threshold must be smaller than every planet's combustion limit."""
        for planet, limit in COMBUSTION_LIMITS.items():
            assert limit > CAZIMI_LIMIT, (
                f"CAZIMI_LIMIT={CAZIMI_LIMIT} must be < {planet} combustion limit {limit}"
            )


class TestCheckCombustionTuple:
    """Tests for the updated _check_combustion() return signature."""

    def test_returns_tuple_of_two_bools(self) -> None:
        result = _check_combustion("Mars", 10.0, 10.0, False)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], bool)

    def test_sun_returns_false_false(self) -> None:
        """Sun is never combust or cazimi relative to itself."""
        is_combust, is_cazimi = _check_combustion("Sun", 100.0, 100.0, False)
        assert is_combust is False
        assert is_cazimi is False

    def test_rahu_returns_false_false(self) -> None:
        is_combust, is_cazimi = _check_combustion("Rahu", 100.0, 100.0, False)
        assert is_combust is False
        assert is_cazimi is False

    def test_ketu_returns_false_false(self) -> None:
        is_combust, is_cazimi = _check_combustion("Ketu", 100.0, 100.0, False)
        assert is_combust is False
        assert is_cazimi is False

    def test_planet_within_cazimi_is_cazimi_not_combust(self) -> None:
        """Within 17': cazimi=True, combust=False — not weakened."""
        # 5 arc-minutes separation
        tiny_sep = 5.0 / 60.0
        is_combust, is_cazimi = _check_combustion("Mars", 100.0 + tiny_sep, 100.0, False)
        assert is_cazimi is True
        assert is_combust is False

    def test_planet_outside_cazimi_but_combust(self) -> None:
        """Between 17' and combustion limit: combust=True, cazimi=False."""
        # 1 degree separation (> 17', well within Mars 17° limit)
        sep = 1.0
        is_combust, is_cazimi = _check_combustion("Mars", 100.0 + sep, 100.0, False)
        assert is_combust is True
        assert is_cazimi is False

    def test_planet_outside_combustion_limit(self) -> None:
        """Beyond combustion limit: both False."""
        # Mars combustion limit = 17°; use 18° separation
        sep = 18.0
        is_combust, is_cazimi = _check_combustion("Mars", 100.0 + sep, 100.0, False)
        assert is_combust is False
        assert is_cazimi is False

    def test_cazimi_mutual_exclusion(self) -> None:
        """is_combust and is_cazimi are never both True."""
        # Test various separations for Jupiter
        for sep_arcmin in [0, 5, 10, 17, 30, 60, 120, 300, 660, 720]:
            sep = sep_arcmin / 60.0
            is_combust, is_cazimi = _check_combustion("Jupiter", 100.0 + sep, 100.0, False)
            assert not (is_combust and is_cazimi), (
                f"sep={sep:.4f}°: is_combust={is_combust} and is_cazimi={is_cazimi} both True"
            )

    def test_exact_cazimi_boundary(self) -> None:
        """At exactly CAZIMI_LIMIT, still cazimi (< not <=)."""
        # Just inside
        just_inside = CAZIMI_LIMIT * 0.999
        _, is_cazimi = _check_combustion("Venus", 100.0 + just_inside, 100.0, False)
        assert is_cazimi is True

        # Just outside
        just_outside = CAZIMI_LIMIT * 1.001
        _, is_cazimi = _check_combustion("Venus", 100.0 + just_outside, 100.0, False)
        assert is_cazimi is False

    def test_retrograde_mercury_cazimi(self) -> None:
        """Retrograde Mercury: cazimi still detected correctly."""
        tiny_sep = 5.0 / 60.0
        is_combust, is_cazimi = _check_combustion("Mercury", 100.0 + tiny_sep, 100.0, True)
        assert is_cazimi is True
        assert is_combust is False

    def test_retrograde_mercury_combust_smaller_limit(self) -> None:
        """Retrograde Mercury combustion limit = 12° (vs 14° direct)."""
        # 13° separation: direct Mercury would be combust, retrograde not
        sep = 13.0
        is_combust_direct, _ = _check_combustion("Mercury", 100.0 + sep, 100.0, False)
        is_combust_retro, _ = _check_combustion("Mercury", 100.0 + sep, 100.0, True)
        assert is_combust_direct is True
        assert is_combust_retro is False


class TestCazimiInChart:
    """Tests for cazimi/combust fields in a computed chart."""

    def test_all_planets_have_is_cazimi_field(self, manish_chart: ChartData) -> None:
        """Every planet in the chart must have is_cazimi field."""
        for name, p in manish_chart.planets.items():
            assert hasattr(p, "is_cazimi"), f"{name} missing is_cazimi field"

    def test_cazimi_and_combust_never_both_true(self, manish_chart: ChartData) -> None:
        """No planet can be both cazimi and combust simultaneously."""
        for name, p in manish_chart.planets.items():
            assert not (p.is_combust and p.is_cazimi), (
                f"{name}: is_combust={p.is_combust} and is_cazimi={p.is_cazimi} both True"
            )

    def test_sun_not_combust_or_cazimi(self, manish_chart: ChartData) -> None:
        sun = manish_chart.planets["Sun"]
        assert sun.is_combust is False
        assert sun.is_cazimi is False

    def test_rahu_not_combust_or_cazimi(self, manish_chart: ChartData) -> None:
        rahu = manish_chart.planets["Rahu"]
        assert rahu.is_combust is False
        assert rahu.is_cazimi is False

    def test_ketu_not_combust_or_cazimi(self, manish_chart: ChartData) -> None:
        ketu = manish_chart.planets["Ketu"]
        assert ketu.is_combust is False
        assert ketu.is_cazimi is False

    def test_mercury_combust_manish_chart(self, manish_chart: ChartData) -> None:
        """Mercury is near Sun in Manish's chart (Pisces, March 1989)."""
        mercury = manish_chart.planets["Mercury"]
        sun = manish_chart.planets["Sun"]
        diff = abs(mercury.longitude - sun.longitude)
        if diff > 180:
            diff = 360 - diff
        # If within cazimi: cazimi=True, combust=False
        # If within 14°: combust=True, cazimi=False
        # Either way, they're mutually exclusive
        if mercury.is_cazimi:
            assert mercury.is_combust is False
            assert diff < CAZIMI_LIMIT + 0.01
        elif mercury.is_combust:
            assert mercury.is_cazimi is False
            assert diff < COMBUSTION_LIMITS["Mercury"]
        else:
            assert diff >= COMBUSTION_LIMITS["Mercury"] or diff < CAZIMI_LIMIT

    @pytest.mark.parametrize("planet_name", ["Mars", "Jupiter", "Venus", "Saturn", "Moon"])
    def test_non_mercury_planets_combust_consistent(
        self, planet_name: str, manish_chart: ChartData
    ) -> None:
        """For non-Mercury planets, combust/cazimi matches distance from Sun."""
        p = manish_chart.planets[planet_name]
        sun = manish_chart.planets["Sun"]
        diff = abs(p.longitude - sun.longitude)
        if diff > 180:
            diff = 360 - diff

        limit = COMBUSTION_LIMITS[planet_name]
        if diff < CAZIMI_LIMIT:
            assert p.is_cazimi is True
            assert p.is_combust is False
        elif diff < limit:
            assert p.is_combust is True
            assert p.is_cazimi is False
        else:
            assert p.is_combust is False
            assert p.is_cazimi is False
