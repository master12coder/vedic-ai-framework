"""Additional chart computation edge-case tests."""

from __future__ import annotations

import pytest

from jyotish.compute.chart import (
    are_conjunct,
    get_house_lord,
    get_nakshatra,
    get_planet_house,
    get_planets_in_house,
    has_aspect,
)
from jyotish.domain.constants.astro import (
    NUM_NAKSHATRAS,
    PADAS_PER_NAKSHATRA,
)
from jyotish.domain.constants.signs import SIGN_LORDS


class TestGetNakshatra:
    """Tests for get_nakshatra at various longitudes."""

    def test_longitude_zero_returns_ashwini(self) -> None:
        """Longitude 0.0 should be nakshatra index 0, pada 1."""
        nak_idx, pada = get_nakshatra(0.0)
        assert nak_idx == 0
        assert pada == 1

    def test_longitude_near_360_returns_valid(self) -> None:
        """Longitude 359.99 should return a valid nakshatra and pada."""
        nak_idx, pada = get_nakshatra(359.99)
        assert 0 <= nak_idx < NUM_NAKSHATRAS
        assert 1 <= pada <= PADAS_PER_NAKSHATRA

    def test_pada_always_between_1_and_4(self) -> None:
        """Pada should always be between 1 and 4 for any longitude."""
        for lon in [0.0, 13.33, 45.0, 120.5, 200.0, 300.0, 359.99]:
            _, pada = get_nakshatra(lon)
            assert 1 <= pada <= PADAS_PER_NAKSHATRA, f"pada {pada} out of range at lon={lon}"

    def test_nakshatra_boundary_exact(self) -> None:
        """Exactly at a nakshatra boundary should move to the next one."""
        # 13.333... degrees is the boundary between nakshatra 0 and 1
        span = 360.0 / 27
        nak_idx, _ = get_nakshatra(span)
        assert nak_idx == 1

    def test_last_nakshatra(self) -> None:
        """Longitude in the last nakshatra range (Revati, index 26)."""
        nak_idx, pada = get_nakshatra(350.0)
        assert nak_idx == 26
        assert 1 <= pada <= PADAS_PER_NAKSHATRA


class TestHasAspect:
    """Tests for planetary aspect detection including special aspects."""

    def test_standard_seventh_aspect(self, manish_chart) -> None:
        """Every planet has a standard 7th-house aspect."""
        sun = manish_chart.planets["Sun"]
        sun_house = sun.house
        target_house = ((sun_house - 1 + 6) % 12) + 1
        assert has_aspect(manish_chart, "Sun", target_house)

    def test_mars_fourth_aspect(self, manish_chart) -> None:
        """Mars has a special 4th-house aspect."""
        mars_house = manish_chart.planets["Mars"].house
        target_house = ((mars_house - 1 + 3) % 12) + 1
        assert has_aspect(manish_chart, "Mars", target_house)

    def test_mars_eighth_aspect(self, manish_chart) -> None:
        """Mars has a special 8th-house aspect."""
        mars_house = manish_chart.planets["Mars"].house
        target_house = ((mars_house - 1 + 7) % 12) + 1
        assert has_aspect(manish_chart, "Mars", target_house)

    def test_jupiter_fifth_aspect(self, manish_chart) -> None:
        """Jupiter has a special 5th-house aspect."""
        jup_house = manish_chart.planets["Jupiter"].house
        target_house = ((jup_house - 1 + 4) % 12) + 1
        assert has_aspect(manish_chart, "Jupiter", target_house)

    def test_jupiter_ninth_aspect(self, manish_chart) -> None:
        """Jupiter has a special 9th-house aspect."""
        jup_house = manish_chart.planets["Jupiter"].house
        target_house = ((jup_house - 1 + 8) % 12) + 1
        assert has_aspect(manish_chart, "Jupiter", target_house)

    def test_saturn_third_aspect(self, manish_chart) -> None:
        """Saturn has a special 3rd-house aspect."""
        sat_house = manish_chart.planets["Saturn"].house
        target_house = ((sat_house - 1 + 2) % 12) + 1
        assert has_aspect(manish_chart, "Saturn", target_house)

    def test_saturn_tenth_aspect(self, manish_chart) -> None:
        """Saturn has a special 10th-house aspect."""
        sat_house = manish_chart.planets["Saturn"].house
        target_house = ((sat_house - 1 + 9) % 12) + 1
        assert has_aspect(manish_chart, "Saturn", target_house)

    def test_no_aspect_on_adjacent_house(self, manish_chart) -> None:
        """Moon (no special aspects) should not aspect the house 2 away."""
        moon_house = manish_chart.planets["Moon"].house
        adjacent = ((moon_house - 1 + 1) % 12) + 1
        assert not has_aspect(manish_chart, "Moon", adjacent)


class TestAreConjunct:
    """Tests for conjunction detection."""

    def test_same_sign_is_conjunct(self, manish_chart) -> None:
        """Planets in the same sign should be considered conjunct."""
        # Find two planets in the same sign
        signs_seen: dict[int, str] = {}
        pair_found = False
        for name, p in manish_chart.planets.items():
            if p.sign_index in signs_seen:
                other = signs_seen[p.sign_index]
                assert are_conjunct(manish_chart, name, other)
                pair_found = True
                break
            signs_seen[p.sign_index] = name
        if not pair_found:
            pytest.skip("No two planets share a sign in reference chart")

    def test_opposite_signs_not_conjunct(self, manish_chart) -> None:
        """Rahu and Ketu (180 degrees apart) should not be conjunct."""
        assert not are_conjunct(manish_chart, "Rahu", "Ketu")


class TestGetHouseLord:
    """Tests for get_house_lord across all 12 houses."""

    def test_all_12_house_lords_valid(self, manish_chart) -> None:
        """Every house lord should be a planet from SIGN_LORDS."""
        valid_planets = set(SIGN_LORDS.values())
        for house_num in range(1, 13):
            lord = get_house_lord(manish_chart, house_num)
            assert lord in valid_planets, f"House {house_num} lord '{lord}' not a valid planet"

    def test_first_house_lord_is_lagnesh(self, manish_chart) -> None:
        """First house lord should match the lord of the lagna sign."""
        expected = SIGN_LORDS[manish_chart.lagna_sign_index]
        assert get_house_lord(manish_chart, 1) == expected

    def test_seventh_house_lord(self, manish_chart) -> None:
        """7th house lord for Mithuna lagna should be Jupiter (Dhanu)."""
        assert get_house_lord(manish_chart, 7) == "Jupiter"


class TestGetPlanetsInHouse:
    """Tests for get_planets_in_house."""

    def test_all_planets_accounted_for(self, manish_chart) -> None:
        """Sum of planets across all 12 houses should equal 9."""
        total = sum(len(get_planets_in_house(manish_chart, h)) for h in range(1, 13))
        assert total == 9

    def test_returns_list(self, manish_chart) -> None:
        """get_planets_in_house should return a list."""
        result = get_planets_in_house(manish_chart, 1)
        assert isinstance(result, list)


class TestGetPlanetHouse:
    """Tests for get_planet_house."""

    def test_planet_house_in_valid_range(self, manish_chart) -> None:
        """Every planet's house should be between 1 and 12."""
        for planet_name in manish_chart.planets:
            house = get_planet_house(manish_chart, planet_name)
            assert 1 <= house <= 12, f"{planet_name} house={house} out of range"
