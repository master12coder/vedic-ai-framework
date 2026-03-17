"""Tests for astronomical constants in domain.constants.astro."""

from __future__ import annotations

import pytest

from jyotish.domain.constants.astro import (
    ASHTOTTARI_TOTAL_YEARS,
    DEFAULT_CONJUNCTION_ORB,
    DEGREES_PER_SIGN,
    FULL_CIRCLE_DEG,
    HALF_CIRCLE_DEG,
    MAX_DAY_RATING,
    MAX_NAKSHATRA_INDEX,
    NAKSHATRA_SPAN_DEG,
    NUM_NAKSHATRAS,
    NUM_SIGNS,
    PADAS_PER_NAKSHATRA,
    SARVASHTAKAVARGA_TOTAL,
    YOGINI_TOTAL_YEARS,
)


class TestNakshatraConstants:
    """Tests for nakshatra-related astronomical constants."""

    def test_nakshatra_span_times_count_equals_circle(self) -> None:
        """NAKSHATRA_SPAN_DEG * NUM_NAKSHATRAS should equal 360."""
        assert pytest.approx(FULL_CIRCLE_DEG) == NAKSHATRA_SPAN_DEG * NUM_NAKSHATRAS

    def test_num_nakshatras_is_27(self) -> None:
        """There are exactly 27 nakshatras in Vedic astrology."""
        assert NUM_NAKSHATRAS == 27

    def test_max_nakshatra_index_consistent(self) -> None:
        """MAX_NAKSHATRA_INDEX should be NUM_NAKSHATRAS - 1."""
        assert MAX_NAKSHATRA_INDEX == NUM_NAKSHATRAS - 1

    def test_nakshatra_span_approximately_13_33(self) -> None:
        """Each nakshatra spans approximately 13.333 degrees."""
        assert pytest.approx(13.3333, rel=1e-3) == NAKSHATRA_SPAN_DEG

    def test_padas_per_nakshatra_is_4(self) -> None:
        """Each nakshatra has exactly 4 padas (quarters)."""
        assert PADAS_PER_NAKSHATRA == 4


class TestCircleConstants:
    """Tests for circle geometry constants."""

    def test_full_circle_is_360(self) -> None:
        """A full circle is 360 degrees."""
        assert FULL_CIRCLE_DEG == 360.0

    def test_half_circle_is_180(self) -> None:
        """A half circle is 180 degrees."""
        assert HALF_CIRCLE_DEG == 180.0

    def test_half_circle_is_half_of_full(self) -> None:
        """HALF_CIRCLE_DEG should be exactly half of FULL_CIRCLE_DEG."""
        assert HALF_CIRCLE_DEG == FULL_CIRCLE_DEG / 2

    def test_num_signs_is_12(self) -> None:
        """There are exactly 12 signs in the zodiac."""
        assert NUM_SIGNS == 12

    def test_degrees_per_sign_is_30(self) -> None:
        """Each sign spans exactly 30 degrees."""
        assert DEGREES_PER_SIGN == 30.0

    def test_signs_times_degrees_equals_circle(self) -> None:
        """NUM_SIGNS * DEGREES_PER_SIGN should equal FULL_CIRCLE_DEG."""
        assert NUM_SIGNS * DEGREES_PER_SIGN == FULL_CIRCLE_DEG


class TestMiscConstants:
    """Tests for SAV, conjunction, day rating, and dasha constants."""

    def test_sarvashtakavarga_total_is_337(self) -> None:
        """SAV total is always 337 across all signs and planets."""
        assert SARVASHTAKAVARGA_TOTAL == 337

    def test_default_conjunction_orb_positive(self) -> None:
        """Default conjunction orb should be a positive number of degrees."""
        assert DEFAULT_CONJUNCTION_ORB > 0

    def test_max_day_rating_is_10(self) -> None:
        """Day rating scale tops out at 10."""
        assert MAX_DAY_RATING == 10

    def test_yogini_total_years(self) -> None:
        """Yogini dasha total should be 36 years (sum of 1..8)."""
        assert YOGINI_TOTAL_YEARS == 36
        assert sum(range(1, 9)) == YOGINI_TOTAL_YEARS

    def test_ashtottari_total_years(self) -> None:
        """Ashtottari dasha total should be 108 years."""
        assert ASHTOTTARI_TOTAL_YEARS == 108
