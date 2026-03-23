"""Tests for Nisheka (conception) chart computation.

Primary fixture: manish_chart (Manish Chaurasia — verified reference chart).
  DOB: 13/03/1989  TOB: 12:17  Place: Varanasi
  Lagna: Mithuna (Gemini)   Moon: Rohini Pada 2

The Nisheka chart estimates the conception moment using BPHS Ch.4 rules.
Gestation ~ 273 days, adjusted by Moon's position.

Source: BPHS Ch.4.
"""

from __future__ import annotations

from daivai_engine.compute.nisheka import (
    _compute_conception_jd,
    _compute_sidereal_lagna,
    _compute_sidereal_moon,
    _jd_to_date_str,
    _moon_degrees_in_sign,
    _moon_house,
    compute_nisheka,
)
from daivai_engine.constants import SIGNS_EN
from daivai_engine.models.chart import ChartData
from daivai_engine.models.nisheka import NishekaResult


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


class TestMoonHelpers:
    """Test Moon position helper functions."""

    def test_moon_degrees_in_sign_range(self, manish_chart: ChartData) -> None:
        """Moon's degree within sign must be 0-30."""
        deg = _moon_degrees_in_sign(manish_chart)
        assert 0 <= deg < 30

    def test_moon_house_range(self, manish_chart: ChartData) -> None:
        """Moon's house must be 1-12."""
        house = _moon_house(manish_chart)
        assert 1 <= house <= 12


class TestConceptionJD:
    """Test the conception Julian Day computation."""

    def test_conception_jd_before_birth(self, manish_chart: ChartData) -> None:
        """Conception JD must be earlier than birth JD."""
        conception_jd = _compute_conception_jd(manish_chart)
        assert conception_jd < manish_chart.julian_day

    def test_conception_approximately_273_days_before(self, manish_chart: ChartData) -> None:
        """Conception should be roughly 240-310 days before birth."""
        conception_jd = _compute_conception_jd(manish_chart)
        days_diff = manish_chart.julian_day - conception_jd
        assert 240 <= days_diff <= 310, (
            f"Conception {days_diff:.0f} days before birth — outside expected range"
        )


class TestJDToDateStr:
    """Test Julian Day to date string conversion."""

    def test_known_jd_to_date(self) -> None:
        """J2000.0 = 01/01/2000 at noon."""
        import swisseph as swe

        jd = swe.julday(2000, 1, 1, 12.0)
        date_str = _jd_to_date_str(jd)
        assert date_str == "01/01/2000"

    def test_format_dd_mm_yyyy(self) -> None:
        import swisseph as swe

        jd = swe.julday(1989, 3, 13, 12.0)
        date_str = _jd_to_date_str(jd)
        assert date_str == "13/03/1989"


# ---------------------------------------------------------------------------
# Sidereal position computations
# ---------------------------------------------------------------------------


class TestSiderealComputation:
    """Test sidereal lagna and Moon computations."""

    def test_sidereal_lagna_returns_valid_sign(self, manish_chart: ChartData) -> None:
        """The sign index must be 0-11."""
        jd = manish_chart.julian_day
        _, sign_idx = _compute_sidereal_lagna(jd, manish_chart.latitude, manish_chart.longitude)
        assert 0 <= sign_idx <= 11

    def test_sidereal_moon_returns_valid_sign(self, manish_chart: ChartData) -> None:
        jd = manish_chart.julian_day
        _, sign_idx = _compute_sidereal_moon(jd)
        assert 0 <= sign_idx <= 11


# ---------------------------------------------------------------------------
# Full Nisheka computation
# ---------------------------------------------------------------------------


class TestComputeNisheka:
    """Integration tests for compute_nisheka."""

    def test_result_type(self, manish_chart: ChartData) -> None:
        result = compute_nisheka(manish_chart)
        assert isinstance(result, NishekaResult)

    def test_conception_date_format(self, manish_chart: ChartData) -> None:
        """Date should be DD/MM/YYYY."""
        result = compute_nisheka(manish_chart)
        parts = result.conception_date.split("/")
        assert len(parts) == 3
        assert len(parts[0]) == 2  # DD
        assert len(parts[1]) == 2  # MM
        assert len(parts[2]) == 4  # YYYY

    def test_conception_before_birth_date(self, manish_chart: ChartData) -> None:
        """Conception date year should be 1988 for a 1989 birth."""
        result = compute_nisheka(manish_chart)
        conception_year = int(result.conception_date.split("/")[2])
        assert conception_year == 1988

    def test_nisheka_lagna_is_valid_sign(self, manish_chart: ChartData) -> None:
        result = compute_nisheka(manish_chart)
        assert result.nisheka_lagna_sign in SIGNS_EN
        assert 0 <= result.nisheka_lagna_sign_index <= 11

    def test_nisheka_moon_is_valid_sign(self, manish_chart: ChartData) -> None:
        result = compute_nisheka(manish_chart)
        assert result.nisheka_moon_sign in SIGNS_EN
        assert 0 <= result.nisheka_moon_sign_index <= 11

    def test_verification_flags_are_boolean(self, manish_chart: ChartData) -> None:
        result = compute_nisheka(manish_chart)
        assert isinstance(result.nisheka_lagna_matches_birth_moon, bool)
        assert isinstance(result.birth_lagna_matches_nisheka_moon, bool)
        assert isinstance(result.verification_passed, bool)

    def test_verification_logic_consistent(self, manish_chart: ChartData) -> None:
        """verification_passed = either condition met."""
        result = compute_nisheka(manish_chart)
        expected = (
            result.nisheka_lagna_matches_birth_moon or result.birth_lagna_matches_nisheka_moon
        )
        assert result.verification_passed == expected

    def test_summary_nonempty(self, manish_chart: ChartData) -> None:
        result = compute_nisheka(manish_chart)
        assert len(result.summary) > 0
        assert "Nisheka Lagna" in result.summary

    def test_days_before_birth_positive(self, manish_chart: ChartData) -> None:
        result = compute_nisheka(manish_chart)
        assert result.conception_approx_days_before_birth > 0

    def test_sample_chart_also_works(self, sample_chart: ChartData) -> None:
        """Nisheka computation should work for any valid chart."""
        result = compute_nisheka(sample_chart)
        assert isinstance(result, NishekaResult)
        assert result.conception_approx_days_before_birth > 0
