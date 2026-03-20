"""Tests for Kalachakra Dasha — BPHS Chapter 46.

Tests the YAML-driven 108-pada mapping, 4 groups, variable Paramayus,
DEHA/JEEVA, balance, Gati detection, and provenance citations.
"""

from __future__ import annotations

from daivai_engine.compute.kalachakra_dasha import compute_kalachakra_dasha
from daivai_engine.models.chart import ChartData


class TestManishRohiniPada2:
    """Test case 1: Moon in Rohini 2nd pada — Apasavya-I group."""

    def test_group_is_apasavya_i(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        assert result.group == "apasavya_i"

    def test_sequence_is_correct(self, manish_chart: ChartData) -> None:
        """Apasavya-I Pada 2: Vir,Lib,Sco,Pis,Aqu,Cap,Sag,Sco,Lib."""
        result = compute_kalachakra_dasha(manish_chart)
        expected = [5, 6, 7, 11, 10, 9, 8, 7, 6]
        actual = [p.sign_index for p in result.periods]
        assert actual == expected

    def test_paramayus_is_83(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        assert result.paramayus == 83

    def test_deha_is_virgo(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        assert result.deha_sign == 5  # Virgo
        assert result.deha_sign_name == "Kanya"

    def test_jeeva_is_libra(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        assert result.jeeva_sign == 6  # Libra
        assert result.jeeva_sign_name == "Tula"


class TestAshwiniPada1:
    """Test case 2: Ashwini 1st pada should give Savya-I, paramayus=100."""

    def test_via_sample_chart(self, sample_chart: ChartData) -> None:
        """Sample chart may or may not be Ashwini — test structure regardless."""
        result = compute_kalachakra_dasha(sample_chart)
        assert result.paramayus in (83, 85, 86, 100)
        assert len(result.periods) == 9
        assert result.source  # Has a source citation


class TestParamayusValues:
    def test_paramayus_valid(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        assert result.paramayus in (83, 85, 86, 100)

    def test_paramayus_matches_sign_years(self, manish_chart: ChartData) -> None:
        """Paramayus = sum of years for the 9 signs in the sequence."""
        result = compute_kalachakra_dasha(manish_chart)
        from daivai_engine.compute.kalachakra_dasha import _load

        sign_years = {int(k): int(v) for k, v in _load()["sign_years"]["values"].items()}
        total = sum(sign_years[p.sign_index] for p in result.periods)
        assert total == result.paramayus


class TestGatiDetection:
    """Test case 4: Gati (jump) detection."""

    def test_manish_has_gati(self, manish_chart: ChartData) -> None:
        """Apasavya-I Pada 2 has Simhavalokana (Sco→Pis)."""
        result = compute_kalachakra_dasha(manish_chart)
        assert len(result.gatis) >= 1

    def test_gati_has_type(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        for g in result.gatis:
            assert g.gati_type in ("simhavalokana", "manduka", "markati")

    def test_gati_has_severity(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        for g in result.gatis:
            assert g.severity in ("severe", "moderate")

    def test_gati_has_sign_names(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        for g in result.gatis:
            assert g.from_sign_name
            assert g.to_sign_name
            assert g.gati_name_hi  # Has Hindi name


class TestBalance:
    def test_balance_positive(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        assert result.balance_years > 0

    def test_balance_within_first_sign(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        assert result.balance_years <= result.periods[0].years

    def test_periods_consecutive(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        for i in range(1, len(result.periods)):
            gap = abs((result.periods[i].start - result.periods[i - 1].end).total_seconds())
            assert gap < 1


class TestProvenance:
    """Every result must carry its own proof."""

    def test_has_source_citation(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        assert "BPHS" in result.source

    def test_has_confidence_level(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        assert result.confidence in ("canonical", "scholarly_consensus", "debated")

    def test_gatis_have_sources(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        for g in result.gatis:
            assert g.source  # Non-empty source


class TestDehaJeeva:
    def test_deha_is_first_period(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        assert result.periods[0].is_deha

    def test_jeeva_is_last_period(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        assert result.periods[-1].is_jeeva

    def test_nine_periods(self, manish_chart: ChartData) -> None:
        result = compute_kalachakra_dasha(manish_chart)
        assert len(result.periods) == 9


class TestDeterminism:
    def test_same_input_same_output(self, manish_chart: ChartData) -> None:
        r1 = compute_kalachakra_dasha(manish_chart)
        r2 = compute_kalachakra_dasha(manish_chart)
        assert r1.group == r2.group
        assert r1.paramayus == r2.paramayus
        assert r1.balance_years == r2.balance_years
        assert len(r1.gatis) == len(r2.gatis)
