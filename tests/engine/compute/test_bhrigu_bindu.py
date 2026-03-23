"""Tests for Bhrigu Bindu computation."""

from __future__ import annotations

import pytest

from daivai_engine.compute.bhrigu_bindu import _midpoint_longitude, compute_bhrigu_bindu
from daivai_engine.models.bhrigu_bindu import BhriguBinduResult


class TestBhriguBinduStructure:
    def test_returns_model_instance(self, manish_chart):
        """compute_bhrigu_bindu returns a BhriguBinduResult."""
        result = compute_bhrigu_bindu(manish_chart)
        assert isinstance(result, BhriguBinduResult)

    def test_longitude_in_valid_range(self, manish_chart):
        """Bhrigu Bindu longitude is in [0, 360)."""
        result = compute_bhrigu_bindu(manish_chart)
        assert 0.0 <= result.longitude < 360.0

    def test_sign_index_valid(self, manish_chart):
        """Sign index is in 0-11."""
        result = compute_bhrigu_bindu(manish_chart)
        assert 0 <= result.sign_index <= 11

    def test_degree_in_sign_valid(self, manish_chart):
        """Degree within sign is in [0, 30)."""
        result = compute_bhrigu_bindu(manish_chart)
        assert 0.0 <= result.degree_in_sign < 30.0

    def test_house_valid(self, manish_chart):
        """House is in 1-12."""
        result = compute_bhrigu_bindu(manish_chart)
        assert 1 <= result.house <= 12

    def test_nakshatra_index_valid(self, manish_chart):
        """Nakshatra index is in 0-26."""
        result = compute_bhrigu_bindu(manish_chart)
        assert 0 <= result.nakshatra_index <= 26

    def test_nakshatra_non_empty(self, manish_chart):
        """Nakshatra and lord strings are non-empty."""
        result = compute_bhrigu_bindu(manish_chart)
        assert result.nakshatra
        assert result.nakshatra_lord
        assert result.sign_lord

    def test_input_longitudes_recorded(self, manish_chart):
        """Result stores the Rahu and Moon longitudes used."""
        result = compute_bhrigu_bindu(manish_chart)
        assert result.rahu_longitude == manish_chart.planets["Rahu"].longitude
        assert result.moon_longitude == manish_chart.planets["Moon"].longitude


class TestBhriguBinduFormula:
    def test_longitude_is_midpoint_of_rahu_and_moon(self, manish_chart):
        """BB longitude equals the shorter-arc midpoint of Rahu and Moon."""
        rahu_lon = manish_chart.planets["Rahu"].longitude
        moon_lon = manish_chart.planets["Moon"].longitude
        expected = _midpoint_longitude(rahu_lon, moon_lon)
        result = compute_bhrigu_bindu(manish_chart)
        assert abs(result.longitude - expected) < 1e-9

    def test_sign_consistent_with_longitude(self, manish_chart):
        """sign_index matches int(longitude / 30)."""
        result = compute_bhrigu_bindu(manish_chart)
        assert result.sign_index == int(result.longitude / 30.0)

    def test_degree_in_sign_consistent(self, manish_chart):
        """degree_in_sign = longitude - sign_index * 30."""
        result = compute_bhrigu_bindu(manish_chart)
        expected_deg = result.longitude - result.sign_index * 30.0
        assert abs(result.degree_in_sign - expected_deg) < 1e-9

    def test_house_is_whole_sign_from_lagna(self, manish_chart):
        """House = (sign_index - lagna_sign_index) % 12 + 1."""
        result = compute_bhrigu_bindu(manish_chart)
        expected_house = ((result.sign_index - manish_chart.lagna_sign_index) % 12) + 1
        assert result.house == expected_house


class TestBhriguBinduMidpointHelper:
    @pytest.mark.parametrize(
        "lon_a,lon_b,expected",
        [
            (0.0, 180.0, 90.0),  # simple average
            (10.0, 50.0, 30.0),  # same-side pair
            (350.0, 10.0, 180.0),  # across zero: (350+10)/2 = 180°
            (44.683, 310.3, 177.49),  # Manish: (44.683+310.3)/2 ≈ 177.49° → Virgo
        ],
    )
    def test_midpoint_simple_average(self, lon_a: float, lon_b: float, expected: float):
        """_midpoint_longitude returns simple average mod 360."""
        result = _midpoint_longitude(lon_a, lon_b)
        assert abs(result - expected) < 0.1, f"Expected ~{expected}, got {result}"


class TestBhriguBinduManishKnownValues:
    @pytest.mark.safety
    def test_manish_bhrigu_bindu_in_kanya(self, manish_chart):
        """For Manish: Moon≈44.68° (Taurus), Rahu≈310.3° (Aquarius).
        BB = (44.68 + 310.3) / 2 ≈ 177.49° → Kanya (Virgo), sign_index=5."""
        result = compute_bhrigu_bindu(manish_chart)
        # Simple average: (Moon_lon + Rahu_lon) / 2 ≈ 177.49° → Virgo (index 5)
        assert result.sign_index == 5, (
            f"Expected Virgo (5), got sign_index={result.sign_index} ({result.sign_en})"
        )
        # Virgo is the 4th house from Mithuna lagna (Gemini=2 → Virgo=(5-2)%12+1=4)
        assert result.house == 4
        assert 0 <= result.degree_in_sign < 30
