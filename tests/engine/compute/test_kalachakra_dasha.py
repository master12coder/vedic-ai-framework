"""Tests for Kalachakra Dasha — BPHS Chapter 46.

Verifies the 108-pada mapping, 4 nakshatra groups, variable Paramayus,
DEHA/JEEVA anchors, balance calculation, and Gati jumps.
"""

from __future__ import annotations

from daivai_engine.compute.kalachakra_dasha import (
    _SIGN_YEARS,
    compute_kalachakra_dasha,
)
from daivai_engine.models.chart import ChartData


class TestNakshatraGrouping:
    def test_manish_rohini_is_apasavya_i(self, manish_chart: ChartData) -> None:
        """Rohini is in the Apasavya-I group (BPHS Ch.46 v8)."""
        result = compute_kalachakra_dasha(manish_chart)
        assert result.group == "apasavya_i"
        assert result.nakshatra == "Rohini"

    def test_pada_is_correct(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        assert result.pada == 2


class TestParamayus:
    def test_paramayus_is_valid(self, manish_chart: ChartData) -> None:
        """Paramayus must be 83, 85, 86, or 100 (BPHS Ch.46)."""
        result = compute_kalachakra_dasha(manish_chart)
        assert result.paramayus in (83, 85, 86, 100)

    def test_manish_pada_2_apasavya_i_is_83(self, manish_chart: ChartData) -> None:
        """Apasavya-I Pada 2: Vir,Lib,Sco,Pis,Aqu,Cap,Sag,Sco,Lib = 83y."""
        result = compute_kalachakra_dasha(manish_chart)
        assert result.paramayus == 83

    def test_paramayus_matches_sum(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        total = sum(_SIGN_YEARS[p.sign_index] for p in result.periods)
        assert total == result.paramayus


class TestSequence:
    def test_nine_periods(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        assert len(result.periods) == 9

    def test_manish_sequence_correct(self, manish_chart: ChartData) -> None:
        """Apasavya-I Pada 2 sequence from BPHS."""
        result = compute_kalachakra_dasha(manish_chart)
        expected = [5, 6, 7, 11, 10, 9, 8, 7, 6]
        actual = [p.sign_index for p in result.periods]
        assert actual == expected

    def test_uses_all_12_signs(self, manish_chart: ChartData) -> None:
        """Sequence includes signs beyond Sagittarius (Cap/Aqu/Pis)."""
        result = compute_kalachakra_dasha(manish_chart)
        signs = {p.sign_index for p in result.periods}
        assert any(s >= 9 for s in signs)

    def test_periods_consecutive(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        for i in range(1, len(result.periods)):
            gap = abs((result.periods[i].start - result.periods[i - 1].end).total_seconds())
            assert gap < 1

    def test_valid_year_values(self, manish_chart: ChartData) -> None:
        valid = {4, 5, 7, 9, 10, 16, 21}
        result = compute_kalachakra_dasha(manish_chart)
        for p in result.periods:
            assert p.years in valid


class TestDehaJeeva:
    def test_deha_is_first_sign(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        assert result.deha_sign == result.periods[0].sign_index

    def test_jeeva_is_last_sign(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        assert result.jeeva_sign == result.periods[-1].sign_index


class TestBalance:
    def test_balance_positive(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        assert result.balance_years > 0

    def test_balance_within_first_sign(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        assert result.balance_years <= result.periods[0].years


class TestDeterminism:
    def test_deterministic(self, manish_chart: ChartData) -> None:
        r1 = compute_kalachakra_dasha(manish_chart)
        r2 = compute_kalachakra_dasha(manish_chart)
        assert r1.group == r2.group
        assert r1.paramayus == r2.paramayus
        assert r1.balance_years == r2.balance_years
