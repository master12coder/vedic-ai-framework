"""Test additional dasha systems — Yogini, Ashtottari, Chara."""

import pytest
from jyotish.compute.dasha_extra import (
    compute_yogini_dasha, compute_ashtottari_dasha, compute_chara_dasha,
    YOGINI_TOTAL_YEARS, ASHTOTTARI_TOTAL_YEARS,
)


class TestYoginiDasha:
    def test_eight_periods(self, manish_chart):
        periods = compute_yogini_dasha(manish_chart)
        assert len(periods) == 8

    def test_contiguous_periods(self, manish_chart):
        periods = compute_yogini_dasha(manish_chart)
        for i in range(1, len(periods)):
            diff = abs((periods[i].start - periods[i - 1].end).total_seconds())
            assert diff < 60

    def test_yogini_names_valid(self, manish_chart):
        periods = compute_yogini_dasha(manish_chart)
        valid_names = {"Mangala", "Pingala", "Dhanya", "Bhramari",
                       "Bhadrika", "Ulka", "Siddha", "Sankata"}
        for p in periods:
            assert p.yogini_name in valid_names


class TestAshtottariDasha:
    def test_eight_periods(self, manish_chart):
        periods = compute_ashtottari_dasha(manish_chart)
        assert len(periods) == 8

    def test_contiguous(self, manish_chart):
        periods = compute_ashtottari_dasha(manish_chart)
        for i in range(1, len(periods)):
            diff = abs((periods[i].start - periods[i - 1].end).total_seconds())
            assert diff < 60

    def test_planets_valid(self, manish_chart):
        periods = compute_ashtottari_dasha(manish_chart)
        valid = {"Sun", "Moon", "Mars", "Mercury", "Saturn", "Jupiter", "Rahu", "Venus"}
        for p in periods:
            assert p.planet in valid


class TestCharaDasha:
    def test_twelve_periods(self, manish_chart):
        periods = compute_chara_dasha(manish_chart)
        assert len(periods) == 12

    def test_all_signs_covered(self, manish_chart):
        periods = compute_chara_dasha(manish_chart)
        signs = {p.sign_index for p in periods}
        assert len(signs) == 12  # All 12 signs

    def test_years_in_range(self, manish_chart):
        periods = compute_chara_dasha(manish_chart)
        for p in periods:
            assert 1 <= p.years <= 12

    def test_contiguous(self, manish_chart):
        periods = compute_chara_dasha(manish_chart)
        for i in range(1, len(periods)):
            diff = abs((periods[i].start - periods[i - 1].end).total_seconds())
            assert diff < 60
