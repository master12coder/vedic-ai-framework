"""Tests for extended dosha detection — Guru Chandal, Shrapit, Grahan, etc."""

from __future__ import annotations

from daivai_engine.compute.dosha_extended import (
    detect_angarak_dosha,
    detect_daridra_dosha,
    detect_extended_doshas,
    detect_grahan_dosha,
    detect_guru_chandal,
    detect_shakata_dosha,
    detect_shrapit_dosha,
)
from daivai_engine.models.dosha import DoshaResult


class TestDoshaResultStructure:
    """Verify DoshaResult model structure from each detector."""

    def test_guru_chandal_returns_dosha_result(self, manish_chart) -> None:
        result = detect_guru_chandal(manish_chart)
        assert isinstance(result, DoshaResult)

    def test_shrapit_returns_dosha_result(self, manish_chart) -> None:
        result = detect_shrapit_dosha(manish_chart)
        assert isinstance(result, DoshaResult)

    def test_grahan_returns_dosha_result(self, manish_chart) -> None:
        result = detect_grahan_dosha(manish_chart)
        assert isinstance(result, DoshaResult)

    def test_angarak_returns_dosha_result(self, manish_chart) -> None:
        result = detect_angarak_dosha(manish_chart)
        assert isinstance(result, DoshaResult)

    def test_shakata_returns_dosha_result(self, manish_chart) -> None:
        result = detect_shakata_dosha(manish_chart)
        assert isinstance(result, DoshaResult)

    def test_daridra_returns_dosha_result(self, manish_chart) -> None:
        result = detect_daridra_dosha(manish_chart)
        assert isinstance(result, DoshaResult)


class TestDoshaNames:
    """Verify dosha names and Hindi names are set correctly."""

    def test_guru_chandal_name(self, manish_chart) -> None:
        result = detect_guru_chandal(manish_chart)
        assert "Guru Chandal" in result.name

    def test_shrapit_name(self, manish_chart) -> None:
        result = detect_shrapit_dosha(manish_chart)
        assert "Shrapit" in result.name

    def test_grahan_name(self, manish_chart) -> None:
        result = detect_grahan_dosha(manish_chart)
        assert "Grahan" in result.name

    def test_angarak_name(self, manish_chart) -> None:
        result = detect_angarak_dosha(manish_chart)
        assert "Angarak" in result.name

    def test_shakata_name(self, manish_chart) -> None:
        result = detect_shakata_dosha(manish_chart)
        assert "Shakata" in result.name

    def test_daridra_name(self, manish_chart) -> None:
        result = detect_daridra_dosha(manish_chart)
        assert "Daridra" in result.name


class TestDoshaPresence:
    """Tests for is_present field logic."""

    def test_absent_dosha_has_is_present_false(self, manish_chart) -> None:
        # If Jupiter and Rahu are not conjunct, Guru Chandal should be absent
        result = detect_guru_chandal(manish_chart)
        jup = manish_chart.planets["Jupiter"]
        rahu = manish_chart.planets["Rahu"]
        expected = jup.sign_index == rahu.sign_index
        assert result.is_present == expected

    def test_shrapit_present_when_saturn_rahu_conjunct(self, manish_chart) -> None:
        result = detect_shrapit_dosha(manish_chart)
        sat = manish_chart.planets["Saturn"]
        rahu = manish_chart.planets["Rahu"]
        expected = sat.sign_index == rahu.sign_index
        assert result.is_present == expected

    def test_severity_is_valid_string_when_present(self, manish_chart) -> None:
        valid_severities = {"full", "partial", "mild", "moderate", "severe"}
        for detector in [
            detect_guru_chandal,
            detect_shrapit_dosha,
            detect_grahan_dosha,
            detect_angarak_dosha,
            detect_shakata_dosha,
        ]:
            result = detector(manish_chart)
            if result.is_present:
                assert result.severity in valid_severities, f"{result.name}: {result.severity}"


class TestExtendedDoshas:
    """Tests for detect_extended_doshas() — the aggregate function."""

    def test_returns_list(self, manish_chart) -> None:
        results = detect_extended_doshas(manish_chart)
        assert isinstance(results, list)

    def test_returns_six_doshas(self, manish_chart) -> None:
        results = detect_extended_doshas(manish_chart)
        assert len(results) == 6

    def test_all_are_dosha_results(self, manish_chart) -> None:
        results = detect_extended_doshas(manish_chart)
        for r in results:
            assert isinstance(r, DoshaResult)

    def test_no_duplicate_names(self, manish_chart) -> None:
        results = detect_extended_doshas(manish_chart)
        names = [r.name for r in results]
        assert len(names) == len(set(names))

    def test_houses_in_range_when_present(self, manish_chart) -> None:
        results = detect_extended_doshas(manish_chart)
        for r in results:
            if r.is_present:
                for h in r.houses_involved:
                    assert 1 <= h <= 12, f"{r.name} house {h}"


class TestGrahanDosha:
    """Specific tests for Grahan Dosha (Sun/Moon + Rahu/Ketu)."""

    def test_grahan_involves_nodes(self, manish_chart) -> None:
        result = detect_grahan_dosha(manish_chart)
        if result.is_present:
            planets = set(result.planets_involved)
            assert planets & {"Rahu", "Ketu"}, "Grahan must involve Rahu or Ketu"


class TestShakataDoshaLogic:
    """Tests for Shakata Dosha (Moon in 6/8/12 from Jupiter)."""

    def test_shakata_involves_moon_and_jupiter(self, manish_chart) -> None:
        result = detect_shakata_dosha(manish_chart)
        if result.is_present:
            assert "Moon" in result.planets_involved or "Jupiter" in result.planets_involved
