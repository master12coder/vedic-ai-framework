"""Tests for Hora (D2) chart analysis."""

from __future__ import annotations

from daivai_engine.compute.hora_analysis import analyze_hora
from daivai_engine.models.chart import ChartData
from daivai_engine.models.hora import HoraPlanet, HoraResult


class TestHoraStructure:
    def test_returns_nine_hora_planets(self, manish_chart: ChartData) -> None:
        """analyze_hora returns exactly 9 HoraPlanet entries."""
        result = analyze_hora(manish_chart)
        assert len(result.planets) == 9

    def test_result_is_hora_model(self, manish_chart: ChartData) -> None:
        result = analyze_hora(manish_chart)
        assert isinstance(result, HoraResult)

    def test_all_planet_entries_are_hora_planet(self, manish_chart: ChartData) -> None:
        result = analyze_hora(manish_chart)
        for p in result.planets:
            assert isinstance(p, HoraPlanet)

    def test_all_planets_in_sun_or_moon_hora(self, manish_chart: ChartData) -> None:
        result = analyze_hora(manish_chart)
        for p in result.planets:
            assert p.hora in ("Sun", "Moon"), f"{p.planet}.hora = '{p.hora}'"

    def test_hora_sign_index_is_3_or_4(self, manish_chart: ChartData) -> None:
        """D2 hora sign index must be 3 (Cancer) or 4 (Leo)."""
        result = analyze_hora(manish_chart)
        for p in result.planets:
            assert p.hora_sign_index in (3, 4), f"{p.planet}.hora_sign_index = {p.hora_sign_index}"

    def test_hora_counts_sum_to_nine(self, manish_chart: ChartData) -> None:
        result = analyze_hora(manish_chart)
        total = len(result.sun_hora_planets) + len(result.moon_hora_planets)
        assert total == 9

    def test_no_planet_in_both_horas(self, manish_chart: ChartData) -> None:
        result = analyze_hora(manish_chart)
        overlap = set(result.sun_hora_planets) & set(result.moon_hora_planets)
        assert not overlap, f"Planets in both horas: {overlap}"


class TestHoraLogic:
    def test_dominant_hora_valid(self, manish_chart: ChartData) -> None:
        result = analyze_hora(manish_chart)
        assert result.dominant_hora in ("Sun", "Moon")

    def test_dominant_hora_is_majority(self, manish_chart: ChartData) -> None:
        """Dominant hora is the one with more planets (or Sun on tie)."""
        result = analyze_hora(manish_chart)
        sun_count = len(result.sun_hora_planets)
        moon_count = len(result.moon_hora_planets)
        if sun_count >= moon_count:
            assert result.dominant_hora == "Sun"
        else:
            assert result.dominant_hora == "Moon"

    def test_lord_horas_are_sun_or_moon(self, manish_chart: ChartData) -> None:
        result = analyze_hora(manish_chart)
        assert result.lagna_lord_hora in ("Sun", "Moon"), (
            f"lagna_lord_hora = '{result.lagna_lord_hora}'"
        )
        assert result.second_lord_hora in ("Sun", "Moon")
        assert result.eleventh_lord_hora in ("Sun", "Moon")

    def test_hora_sign_matches_hora_name(self, manish_chart: ChartData) -> None:
        """Leo (4) == Sun Hora; Cancer (3) == Moon Hora."""
        result = analyze_hora(manish_chart)
        for p in result.planets:
            if p.hora_sign_index == 4:
                assert p.hora == "Sun"
            elif p.hora_sign_index == 3:
                assert p.hora == "Moon"

    def test_summary_populated(self, manish_chart: ChartData) -> None:
        result = analyze_hora(manish_chart)
        assert result.summary.strip()
        assert result.dominant_wealth_type.strip()

    def test_sun_hora_naturals(self, manish_chart: ChartData) -> None:
        """Sun, Mars, Jupiter in Sun Hora should be flagged as natural."""
        result = analyze_hora(manish_chart)
        for p in result.planets:
            if p.planet in ("Sun", "Mars", "Jupiter") and p.hora == "Sun":
                assert p.is_natural_hora is True

    def test_moon_hora_naturals(self, manish_chart: ChartData) -> None:
        """Moon, Venus, Saturn in Moon Hora should be flagged as natural."""
        result = analyze_hora(manish_chart)
        for p in result.planets:
            if p.planet in ("Moon", "Venus", "Saturn") and p.hora == "Moon":
                assert p.is_natural_hora is True
