"""Tests for the Bhava Chalit chart computation."""

from __future__ import annotations

import pytest

from jyotish.compute.bhava_chalit import (
    compute_bhava_chalit,
    get_bhava_shifted_planets,
    get_planets_in_bhava,
)
from jyotish.utils.constants import PLANETS
from jyotish.domain.models.bhava_chalit import BhavaChalitResult, BhavaPlanet


class TestBhavaChalitComputation:
    """Core Bhava Chalit computation tests."""

    def test_returns_twelve_cusps(self, manish_chart):
        result = compute_bhava_chalit(manish_chart)
        assert len(result.cusps) == 12

    def test_cusps_in_valid_range(self, manish_chart):
        result = compute_bhava_chalit(manish_chart)
        for i, cusp in enumerate(result.cusps):
            assert 0.0 <= cusp < 360.0, (
                f"Cusp {i + 1} = {cusp} is out of 0-360 range"
            )

    def test_all_planets_present(self, manish_chart):
        result = compute_bhava_chalit(manish_chart)
        assert len(result.planets) == len(PLANETS)
        for planet_name in PLANETS:
            assert planet_name in result.planets

    def test_bhava_house_range(self, manish_chart):
        result = compute_bhava_chalit(manish_chart)
        for name, bp in result.planets.items():
            assert 1 <= bp.bhava_house <= 12, (
                f"{name} has bhava_house={bp.bhava_house}, expected 1-12"
            )

    def test_rashi_house_range(self, manish_chart):
        result = compute_bhava_chalit(manish_chart)
        for name, bp in result.planets.items():
            assert 1 <= bp.rashi_house <= 12, (
                f"{name} has rashi_house={bp.rashi_house}, expected 1-12"
            )

    def test_rashi_house_matches_chart(self, manish_chart):
        result = compute_bhava_chalit(manish_chart)
        for planet_name in PLANETS:
            expected = manish_chart.planets[planet_name].house
            assert result.planets[planet_name].rashi_house == expected, (
                f"{planet_name}: rashi_house={result.planets[planet_name].rashi_house}, "
                f"chart.house={expected}"
            )

    def test_bhava_shift_flag_consistency(self, manish_chart):
        result = compute_bhava_chalit(manish_chart)
        for name, bp in result.planets.items():
            expected_shift = bp.rashi_house != bp.bhava_house
            assert bp.has_bhava_shift == expected_shift, (
                f"{name}: has_bhava_shift={bp.has_bhava_shift}, "
                f"rashi={bp.rashi_house}, bhava={bp.bhava_house}"
            )

    def test_cusp_longitude_valid(self, manish_chart):
        result = compute_bhava_chalit(manish_chart)
        for name, bp in result.planets.items():
            assert 0.0 <= bp.cusp_longitude < 360.0, (
                f"{name}: cusp_longitude={bp.cusp_longitude} out of range"
            )

    def test_cusp_longitude_is_from_cusp_list(self, manish_chart):
        result = compute_bhava_chalit(manish_chart)
        cusps_set = set(result.cusps)
        for name, bp in result.planets.items():
            assert bp.cusp_longitude in cusps_set, (
                f"{name}: cusp_longitude={bp.cusp_longitude} not in cusps"
            )

    def test_planet_names_match(self, manish_chart):
        result = compute_bhava_chalit(manish_chart)
        for name, bp in result.planets.items():
            assert bp.name == name

    def test_result_type(self, manish_chart):
        result = compute_bhava_chalit(manish_chart)
        assert isinstance(result, BhavaChalitResult)
        for bp in result.planets.values():
            assert isinstance(bp, BhavaPlanet)


class TestBhavaChalitHelpers:
    """Tests for convenience helper functions."""

    def test_shifted_planets_subset(self, manish_chart):
        shifted = get_bhava_shifted_planets(manish_chart)
        for bp in shifted:
            assert bp.has_bhava_shift is True

    def test_planets_in_bhava_valid(self, manish_chart):
        for house in range(1, 13):
            planets = get_planets_in_bhava(manish_chart, house)
            for bp in planets:
                assert bp.bhava_house == house

    def test_all_planets_accounted_for_across_bhavas(self, manish_chart):
        all_names = set()
        for house in range(1, 13):
            planets = get_planets_in_bhava(manish_chart, house)
            for bp in planets:
                all_names.add(bp.name)
        assert all_names == set(PLANETS)
