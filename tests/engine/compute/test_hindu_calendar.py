"""Tests for Hindu calendar computations."""

from __future__ import annotations

from datetime import date

from daivai_engine.compute.hindu_calendar import (
    get_choghadiya,
    get_sankranti_dates,
    gregorian_to_samvat,
)


class TestSamvat:
    def test_vikram_samvat(self) -> None:
        result = gregorian_to_samvat(date(2026, 5, 1))
        assert result["vikram_samvat"] == 2083  # 2026 + 57

    def test_shaka_samvat(self) -> None:
        result = gregorian_to_samvat(date(2026, 1, 1))
        assert result["shaka_samvat"] == 1948  # 2026 - 78

    def test_kali_yuga(self) -> None:
        result = gregorian_to_samvat(date(2026, 1, 1))
        assert result["kali_yuga"] == 5127  # 2026 + 3101


class TestSankranti:
    def test_returns_twelve(self) -> None:
        dates = get_sankranti_dates(2026)
        assert len(dates) == 12

    def test_makar_sankranti_in_january(self) -> None:
        dates = get_sankranti_dates(2026)
        makar = next((d for d in dates if "Makar" in d.name), None)
        assert makar is not None
        assert makar.date.startswith("2026-01")

    def test_sorted_by_date(self) -> None:
        dates = get_sankranti_dates(2026)
        date_strs = [d.date for d in dates]
        assert date_strs == sorted(date_strs)


class TestChoghadiya:
    def test_returns_sixteen_periods(self) -> None:
        periods = get_choghadiya(date(2026, 3, 19))
        assert len(periods) == 16

    def test_has_auspicious_periods(self) -> None:
        periods = get_choghadiya(date(2026, 3, 19))
        auspicious = [p for p in periods if p.is_auspicious]
        assert len(auspicious) >= 3

    def test_quality_valid(self) -> None:
        valid = {"udveg", "chal", "labh", "amrit", "kaal", "shubh", "rog"}
        periods = get_choghadiya(date(2026, 3, 19))
        for p in periods:
            assert p.quality in valid
