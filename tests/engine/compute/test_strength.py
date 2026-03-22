"""Tests for Shadbala / planetary strength — compute_planet_strengths API."""

from __future__ import annotations

from daivai_engine.compute.strength import (
    NAISARGIKA,
    REQUIRED_SHADBALA,
    SHADBALA_PLANETS,
    _kendradi_bala,
    _uchcha_bala,
    compute_planet_strengths,
    get_strongest_planet,
    get_weakest_planet,
)
from daivai_engine.constants import KENDRAS, PLANETS


class TestUcchaBala:
    """Tests for _uchcha_bala() — exaltation strength."""

    def test_sun_at_exact_exaltation_returns_60(self) -> None:
        # Sun exalted at Aries 10° (longitude = 10.0)
        bala = _uchcha_bala("Sun", 10.0)
        assert abs(bala - 60.0) < 0.5

    def test_sun_at_debilitation_returns_zero(self) -> None:
        # Sun debilitated at Libra 10° (longitude = 190.0)
        bala = _uchcha_bala("Sun", 190.0)
        assert bala < 5.0

    def test_value_in_range_0_to_60(self) -> None:
        for lon in [0.0, 45.0, 90.0, 135.0, 180.0, 270.0, 359.0]:
            bala = _uchcha_bala("Sun", lon)
            assert 0.0 <= bala <= 60.0, f"lon={lon}, bala={bala}"

    def test_moon_exalted_in_taurus(self) -> None:
        # Moon exalted at Taurus 3° (longitude = 33.0)
        bala = _uchcha_bala("Moon", 33.0)
        assert bala > 50.0

    def test_mercury_exalted_in_virgo(self) -> None:
        # Mercury exalted at Virgo 15° (longitude = 165.0)
        bala = _uchcha_bala("Mercury", 165.0)
        assert bala > 50.0


class TestKendradiBala:
    """Tests for _kendradi_bala() — kendra/panapara/apoklima strength."""

    def test_kendra_returns_60(self) -> None:
        for h in KENDRAS:
            assert _kendradi_bala(h) == 60.0

    def test_panapara_returns_30(self) -> None:
        for h in {2, 5, 8, 11}:
            assert _kendradi_bala(h) == 30.0

    def test_apoklima_returns_15(self) -> None:
        for h in {3, 6, 9, 12}:
            assert _kendradi_bala(h) == 15.0


class TestComputePlanetStrengths:
    """Tests for compute_planet_strengths() — 9-planet backward-compatible API."""

    def test_returns_nine_entries(self, manish_chart) -> None:
        strengths = compute_planet_strengths(manish_chart)
        assert len(strengths) == 9  # 7 classical + Rahu + Ketu

    def test_all_planets_present(self, manish_chart) -> None:
        strengths = compute_planet_strengths(manish_chart)
        names = {s.planet for s in strengths}
        for p in PLANETS:
            assert p in names

    def test_all_values_in_0_1_range(self, manish_chart) -> None:
        strengths = compute_planet_strengths(manish_chart)
        for s in strengths:
            assert 0.0 <= s.sthana_bala <= 1.0, f"{s.planet} sthana={s.sthana_bala}"
            assert 0.0 <= s.dig_bala <= 1.0, f"{s.planet} dig={s.dig_bala}"
            assert 0.0 <= s.kala_bala <= 1.0, f"{s.planet} kala={s.kala_bala}"
            assert 0.0 <= s.total_relative <= 1.0, f"{s.planet} total={s.total_relative}"

    def test_ranks_are_assigned(self, manish_chart) -> None:
        strengths = compute_planet_strengths(manish_chart)
        ranks = [s.rank for s in strengths]
        assert sorted(ranks) == list(range(1, 10))

    def test_is_strong_field_is_bool(self, manish_chart) -> None:
        strengths = compute_planet_strengths(manish_chart)
        for s in strengths:
            assert isinstance(s.is_strong, bool)

    def test_sorted_by_total_relative_descending(self, manish_chart) -> None:
        strengths = compute_planet_strengths(manish_chart)
        totals = [s.total_relative for s in strengths]
        assert totals == sorted(totals, reverse=True)


class TestGetStrongestWeakest:
    """Tests for get_strongest_planet() and get_weakest_planet()."""

    def test_strongest_planet_in_planets_list(self, manish_chart) -> None:
        strongest = get_strongest_planet(manish_chart)
        assert strongest in PLANETS

    def test_weakest_planet_in_planets_list(self, manish_chart) -> None:
        weakest = get_weakest_planet(manish_chart)
        assert weakest in PLANETS

    def test_strongest_not_same_as_weakest(self, manish_chart) -> None:
        strongest = get_strongest_planet(manish_chart)
        weakest = get_weakest_planet(manish_chart)
        assert strongest != weakest

    def test_strongest_has_highest_rank_1(self, manish_chart) -> None:
        strongest = get_strongest_planet(manish_chart)
        strengths = compute_planet_strengths(manish_chart)
        rank1 = next(s for s in strengths if s.rank == 1)
        assert rank1.planet == strongest


class TestNaisargikaValues:
    """Tests for fixed Naisargika Bala constants."""

    def test_sun_has_highest_naisargika(self) -> None:
        assert NAISARGIKA["Sun"] == 60.0

    def test_saturn_has_lowest_naisargika(self) -> None:
        assert NAISARGIKA["Saturn"] < 10.0

    def test_all_seven_planets_defined(self) -> None:
        for p in SHADBALA_PLANETS:
            assert p in NAISARGIKA

    def test_required_shadbala_all_defined(self) -> None:
        for p in SHADBALA_PLANETS:
            assert p in REQUIRED_SHADBALA
            assert REQUIRED_SHADBALA[p] > 0
