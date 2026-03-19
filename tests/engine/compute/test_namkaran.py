"""Tests for Namkaran — naming, Gand Mool, numerology."""

from __future__ import annotations

from daivai_engine.compute.namkaran import (
    check_gand_mool,
    compute_name_number,
    get_name_letters,
)
from daivai_engine.models.chart import ChartData


class TestNameLetters:
    def test_rohini_pada_2(self) -> None:
        """Manish's Moon: Rohini Pada 2 → 'Va'."""
        letters = get_name_letters("Rohini", 2)
        assert "Va" in letters

    def test_ashwini_pada_1(self) -> None:
        letters = get_name_letters("Ashwini", 1)
        assert "Chu" in letters

    def test_invalid_nakshatra(self) -> None:
        letters = get_name_letters("NonExistent", 1)
        assert letters == []


class TestGandMool:
    def test_manish_not_gand_mool(self, manish_chart: ChartData) -> None:
        """Moon in Rohini is NOT Gand Mool."""
        result = check_gand_mool(manish_chart)
        assert not result.is_gand_mool

    def test_severity_for_moola_pada_1(self) -> None:
        """Moola Pada 1 should be severe."""
        # Can't easily create a chart with Moon in Moola, but test the logic
        from daivai_engine.compute.namkaran import _GAND_MOOL_SEVERITY

        assert _GAND_MOOL_SEVERITY["Moola"][1] == "severe"


class TestNameNumerology:
    def test_name_number(self) -> None:
        result = compute_name_number("Manish")
        assert 1 <= result.name_number <= 9
        assert result.raw_sum > 0

    def test_empty_name(self) -> None:
        result = compute_name_number("")
        assert result.name_number == 1  # Minimum

    def test_has_interpretation(self) -> None:
        result = compute_name_number("DaivAI")
        assert result.interpretation
