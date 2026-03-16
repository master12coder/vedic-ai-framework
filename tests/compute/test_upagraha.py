"""Test Upagraha (shadow planet) computation."""

import pytest
from jyotish.compute.upagraha import compute_all_upagrahas, compute_sun_upagrahas


class TestUpagraha:
    def test_sun_upagrahas_count(self, manish_chart):
        """Should compute 5 Sun-derived upagrahas."""
        result = compute_sun_upagrahas(manish_chart)
        assert len(result) == 5

    def test_sun_upagraha_names(self, manish_chart):
        result = compute_sun_upagrahas(manish_chart)
        names = [u.name for u in result]
        assert "Dhuma" in names
        assert "Vyatipata" in names
        assert "Parivesha" in names
        assert "Indrachapa" in names
        assert "Upaketu" in names

    def test_upagraha_valid_positions(self, manish_chart):
        result = compute_sun_upagrahas(manish_chart)
        for u in result:
            assert 0 <= u.longitude < 360
            assert 0 <= u.sign_index <= 11
            assert 0 <= u.degree_in_sign < 30
            assert 1 <= u.house <= 12

    def test_all_upagrahas(self, manish_chart):
        """Should compute Gulika + Mandi + 5 Sun upagrahas."""
        result = compute_all_upagrahas(manish_chart)
        assert len(result) >= 5  # At least Sun-derived
        names = [u.name for u in result]
        assert "Dhuma" in names

    def test_dhuma_formula(self, manish_chart):
        """Dhuma = Sun + 133°20'."""
        sun_lon = manish_chart.planets["Sun"].longitude
        expected_dhuma = (sun_lon + 133.333) % 360.0
        result = compute_sun_upagrahas(manish_chart)
        dhuma = next(u for u in result if u.name == "Dhuma")
        assert abs(dhuma.longitude - expected_dhuma) < 0.01
