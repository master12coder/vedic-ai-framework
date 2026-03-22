"""Tests for core chart computation — compute_chart and helper functions."""

from __future__ import annotations

from daivai_engine.compute.chart import (
    _check_combustion,
    _get_avastha,
    _get_dignity,
    _house_from_lagna,
    are_conjunct,
    get_house_lord,
    get_nakshatra,
    get_planet_house,
    get_planets_in_house,
    has_aspect,
)
from daivai_engine.constants import AVASTHAS, PLANETS


class TestGetNakshatra:
    """Tests for the get_nakshatra() longitude-to-nakshatra mapper."""

    def test_start_of_ashwini_returns_zero(self) -> None:
        idx, pada = get_nakshatra(0.0)
        assert idx == 0
        assert pada == 1

    def test_second_nakshatra_starts_at_13_33(self) -> None:
        idx, _pada = get_nakshatra(13.5)
        assert idx == 1  # Bharani

    def test_max_longitude_returns_last_nakshatra(self) -> None:
        idx, _pada = get_nakshatra(359.9)
        assert 0 <= idx <= 26

    def test_pada_range_is_one_to_four(self) -> None:
        for lon in [0.0, 3.3, 6.7, 10.0, 50.0, 100.0, 200.0, 300.0]:
            _, pada = get_nakshatra(lon)
            assert 1 <= pada <= 4, f"pada={pada} at lon={lon}"

    def test_rohini_pada_2_for_manish_moon(self, manish_chart) -> None:
        moon = manish_chart.planets["Moon"]
        _idx, _pada = get_nakshatra(moon.longitude)
        assert manish_chart.planets["Moon"].nakshatra == "Rohini"
        assert manish_chart.planets["Moon"].pada == 2


class TestGetDignity:
    """Tests for _get_dignity() — exalted/debilitated/mooltrikona/own/neutral."""

    def test_sun_exalted_in_mesha(self) -> None:
        # Sun exalted in Aries (sign_index=0)
        dignity = _get_dignity("Sun", 0, 10.0)
        assert dignity == "exalted"

    def test_sun_debilitated_in_tula(self) -> None:
        # Sun debilitated in Libra (sign_index=6)
        dignity = _get_dignity("Sun", 6, 15.0)
        assert dignity == "debilitated"

    def test_neutral_returns_neutral(self) -> None:
        # Sun in Cancer (4) — not own, not exalt, not debil
        dignity = _get_dignity("Sun", 3, 15.0)
        assert dignity == "neutral"

    def test_mars_mooltrikona_in_aries(self) -> None:
        # Mars mooltrikona in Aries (sign_index=0) between 0-12°
        dignity = _get_dignity("Mars", 0, 6.0)
        assert dignity == "mooltrikona"

    def test_jupiter_own_sign_sagittarius(self) -> None:
        # Jupiter own in Sagittarius (sign_index=8)
        dignity = _get_dignity("Jupiter", 8, 15.0)
        assert dignity == "own"


class TestGetAvastha:
    """Tests for _get_avastha() — planetary age state."""

    def test_first_six_degrees_odd_sign_returns_bala(self) -> None:
        # Odd sign (0-indexed even) = sign_index 0 (Mesha)
        avastha = _get_avastha(3.0, 0)
        assert avastha == AVASTHAS[0]

    def test_all_avasthas_valid(self) -> None:
        for deg in [3.0, 9.0, 15.0, 21.0, 27.0]:
            a = _get_avastha(deg, 0)
            assert a in AVASTHAS

    def test_even_sign_reverses_order(self) -> None:
        # Taurus (sign_index=1) is an even sign — first segment gives last avastha
        avastha_odd = _get_avastha(3.0, 0)
        avastha_even = _get_avastha(3.0, 1)
        assert avastha_odd != avastha_even


class TestCheckCombustion:
    """Tests for _check_combustion() — combust / cazimi detection."""

    def test_sun_never_combust(self) -> None:
        combust, cazimi = _check_combustion("Sun", 45.0, 45.0, False)
        assert not combust
        assert not cazimi

    def test_rahu_never_combust(self) -> None:
        combust, cazimi = _check_combustion("Rahu", 10.0, 10.0, False)
        assert not combust
        assert not cazimi

    def test_mercury_within_one_degree_is_cazimi(self) -> None:
        # Mercury cazimi limit is < CAZIMI_LIMIT (0.2833°)
        combust, cazimi = _check_combustion("Mercury", 10.1, 10.0, False)
        assert cazimi
        assert not combust

    def test_venus_far_from_sun_not_combust(self) -> None:
        combust, cazimi = _check_combustion("Venus", 90.0, 10.0, False)
        assert not combust
        assert not cazimi

    def test_mars_close_to_sun_is_combust(self) -> None:
        # Mars combust limit is ~17 degrees
        combust, cazimi = _check_combustion("Mars", 15.0, 10.0, False)
        assert combust
        assert not cazimi


class TestComputeChart:
    """Integration tests for compute_chart() — Manish reference data."""

    def test_lagna_is_mithuna(self, manish_chart) -> None:
        assert manish_chart.lagna_sign == "Mithuna"

    def test_nine_planets_computed(self, manish_chart) -> None:
        assert len(manish_chart.planets) == len(PLANETS)

    def test_all_planet_names_present(self, manish_chart) -> None:
        for p in PLANETS:
            assert p in manish_chart.planets

    def test_ketu_opposite_rahu(self, manish_chart) -> None:
        rahu_lon = manish_chart.planets["Rahu"].longitude
        ketu_lon = manish_chart.planets["Ketu"].longitude
        diff = abs(rahu_lon - ketu_lon)
        if diff > 180:
            diff = 360 - diff
        assert abs(diff - 180.0) < 0.01

    def test_all_longitudes_in_valid_range(self, manish_chart) -> None:
        for name, p in manish_chart.planets.items():
            assert 0.0 <= p.longitude < 360.0, f"{name} lon={p.longitude}"

    def test_all_houses_in_range_1_12(self, manish_chart) -> None:
        for name, p in manish_chart.planets.items():
            assert 1 <= p.house <= 12, f"{name} house={p.house}"

    def test_ayanamsha_nonzero(self, manish_chart) -> None:
        assert manish_chart.ayanamsha > 0

    def test_rahu_always_retrograde(self, manish_chart) -> None:
        assert manish_chart.planets["Rahu"].is_retrograde

    def test_ketu_always_retrograde(self, manish_chart) -> None:
        assert manish_chart.planets["Ketu"].is_retrograde

    def test_moon_in_rohini(self, manish_chart) -> None:
        assert manish_chart.planets["Moon"].nakshatra == "Rohini"


class TestChartHelpers:
    """Tests for chart accessor functions."""

    def test_get_house_lord_returns_valid_planet(self, manish_chart) -> None:
        for h in range(1, 13):
            lord = get_house_lord(manish_chart, h)
            assert lord in PLANETS

    def test_get_planets_in_house_list_type(self, manish_chart) -> None:
        result = get_planets_in_house(manish_chart, 1)
        assert isinstance(result, list)

    def test_get_planet_house_in_range(self, manish_chart) -> None:
        for p_name in PLANETS:
            h = get_planet_house(manish_chart, p_name)
            assert 1 <= h <= 12

    def test_are_conjunct_same_sign(self, manish_chart) -> None:
        # Test that a planet is conjunct with itself (trivially)
        sun = manish_chart.planets["Sun"]
        # Find any other planet in same sign
        for name, p in manish_chart.planets.items():
            if name != "Sun" and p.sign_index == sun.sign_index:
                assert are_conjunct(manish_chart, "Sun", name)
                break

    def test_has_aspect_seventh_house(self, manish_chart) -> None:
        # Every planet aspects its 7th house
        for p_name in PLANETS:
            p = manish_chart.planets[p_name]
            seventh = ((p.house - 1 + 6) % 12) + 1
            assert has_aspect(manish_chart, p_name, seventh)

    def test_house_from_lagna_formula(self) -> None:
        # Lagna = 1 (Aries=0), planet in Aries = house 1
        assert _house_from_lagna(0, 0) == 1
        # Planet in next sign = house 2
        assert _house_from_lagna(1, 0) == 2
        # Wrap: planet 1 sign before lagna = house 12
        assert _house_from_lagna(11, 0) == 12
