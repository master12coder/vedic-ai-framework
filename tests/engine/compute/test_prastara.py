"""Tests for Prastara Ashtakavarga and Kaksha computation."""

from __future__ import annotations

import pytest

from daivai_engine.compute.ashtakavarga import (
    compute_ashtakavarga,
    compute_kaksha,
    compute_prastara,
)
from daivai_engine.models.ashtakavarga import KakshaResult, PrastaraResult


_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
_SOURCES = [*_PLANETS, "Lagna"]
_KAKSHA_LORDS = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Lagna"]


class TestPrastaraStructure:
    def test_returns_dict_with_7_planets(self, manish_chart):
        """compute_prastara returns a dict with entries for all 7 planets."""
        prastara = compute_prastara(manish_chart)
        assert set(prastara.keys()) == set(_PLANETS)

    def test_each_planet_has_12_sign_entries(self, manish_chart):
        """Each PrastaraResult has exactly 12 contributor lists."""
        prastara = compute_prastara(manish_chart)
        for planet, result in prastara.items():
            assert isinstance(result, PrastaraResult)
            assert result.planet == planet
            assert len(result.contributors) == 12, (
                f"{planet} contributors list length {len(result.contributors)} ≠ 12"
            )

    def test_contributors_are_valid_sources(self, manish_chart):
        """Every contributor name is one of the 8 valid sources."""
        prastara = compute_prastara(manish_chart)
        valid_sources = set(_SOURCES)
        for planet, result in prastara.items():
            for sign_contributors in result.contributors:
                for contributor in sign_contributors:
                    assert contributor in valid_sources, (
                        f"Invalid contributor '{contributor}' for {planet}"
                    )

    def test_contributor_count_matches_bhinna(self, manish_chart):
        """len(contributors[sign]) must equal the Bhinna bindu count for that sign."""
        prastara = compute_prastara(manish_chart)
        bav = compute_ashtakavarga(manish_chart)
        for planet in _PLANETS:
            prastara_result = prastara[planet]
            bhinna_counts = bav.bhinna[planet]
            for sign_idx in range(12):
                contrib_count = len(prastara_result.contributors[sign_idx])
                bhinna_count = bhinna_counts[sign_idx]
                assert contrib_count == bhinna_count, (
                    f"{planet} sign {sign_idx}: prastara count {contrib_count} "
                    f"≠ bhinna count {bhinna_count}"
                )

    def test_no_duplicate_contributors_per_sign(self, manish_chart):
        """Each contributor appears at most once per sign per planet."""
        prastara = compute_prastara(manish_chart)
        for planet, result in prastara.items():
            for sign_idx, sign_contributors in enumerate(result.contributors):
                assert len(sign_contributors) == len(set(sign_contributors)), (
                    f"Duplicate contributors for {planet} in sign {sign_idx}"
                )


class TestKakshaStructure:
    def test_returns_kaksha_result_instance(self):
        """compute_kaksha returns a KakshaResult."""
        result = compute_kaksha(15.0)  # 15° Aries
        assert isinstance(result, KakshaResult)

    def test_kaksha_number_in_valid_range(self):
        """Kaksha number is always 1-8."""
        for lon in [0.0, 3.0, 7.5, 11.25, 15.0, 18.75, 22.5, 26.25, 29.99]:
            result = compute_kaksha(lon)
            assert 1 <= result.kaksha_number <= 8, (
                f"Kaksha {result.kaksha_number} out of range for lon={lon}"
            )

    def test_kaksha_lord_is_valid(self):
        """Kaksha lord is always one of the 8 valid lords."""
        valid_lords = set(_KAKSHA_LORDS)
        for lon in range(0, 360, 15):
            result = compute_kaksha(float(lon))
            assert result.kaksha_lord in valid_lords

    def test_sign_consistent_with_longitude(self):
        """sign_index matches int(longitude / 30)."""
        for lon in [0.0, 45.0, 90.0, 135.5, 180.0, 270.0, 359.9]:
            result = compute_kaksha(lon)
            expected_sign = int(lon / 30.0)
            assert result.sign_index == expected_sign

    def test_degree_in_sign_is_correct(self):
        """degree_in_sign = longitude - sign_index * 30."""
        for lon in [0.0, 44.68, 177.49, 310.3]:
            result = compute_kaksha(lon)
            expected = lon - result.sign_index * 30.0
            assert abs(result.degree_in_sign - expected) < 1e-9

    def test_kaksha_range_contains_degree(self):
        """degree_in_sign falls within [kaksha_start, kaksha_end)."""
        for lon in [0.0, 3.74, 3.75, 7.5, 15.0, 22.5, 29.99]:
            result = compute_kaksha(lon)
            assert result.kaksha_start <= result.degree_in_sign < result.kaksha_end, (
                f"lon={lon}: degree {result.degree_in_sign:.3f} not in "
                f"[{result.kaksha_start}, {result.kaksha_end})"
            )


class TestKakshaKnownValues:
    @pytest.mark.parametrize(
        "degree_in_sign,expected_kaksha,expected_lord",
        [
            (0.0, 1, "Saturn"),  # 0-3d45m: Saturn
            (1.0, 1, "Saturn"),
            (3.75, 2, "Jupiter"),  # 3d45m-7d30m: Jupiter
            (5.0, 2, "Jupiter"),
            (7.5, 3, "Mars"),  # 7d30m-11d15m: Mars
            (11.25, 4, "Sun"),  # 11d15m-15d: Sun
            (15.0, 5, "Venus"),  # 15d-18d45m: Venus
            (18.75, 6, "Mercury"),  # 18d45m-22d30m: Mercury
            (22.5, 7, "Moon"),  # 22d30m-26d15m: Moon
            (26.25, 8, "Lagna"),  # 26d15m-30d: Lagna
            (29.99, 8, "Lagna"),
        ],
    )
    def test_kaksha_lord_for_known_degree(
        self, degree_in_sign: float, expected_kaksha: int, expected_lord: str
    ):
        """Kaksha lord is correct for specific degrees within a sign."""
        # Use Aries (0-30°) for testing
        result = compute_kaksha(degree_in_sign)
        assert result.kaksha_number == expected_kaksha, (
            f"Degree {degree_in_sign}: expected kaksha {expected_kaksha}, "
            f"got {result.kaksha_number}"
        )
        assert result.kaksha_lord == expected_lord, (
            f"Degree {degree_in_sign}: expected lord {expected_lord}, got {result.kaksha_lord}"
        )

    def test_longitude_mod_360_applied(self):
        """Longitudes ≥360 are reduced mod 360 before computation."""
        result1 = compute_kaksha(15.0)
        result2 = compute_kaksha(375.0)  # 375 % 360 = 15
        assert result1.kaksha_number == result2.kaksha_number
        assert result1.kaksha_lord == result2.kaksha_lord
