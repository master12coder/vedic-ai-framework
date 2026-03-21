"""Tests for Jaimini Raj Yoga detection — Upadesha Sutras."""

from __future__ import annotations

from daivai_engine.compute.jaimini import (
    compute_arudha_padas,
    compute_chara_karakas,
    compute_jaimini,
    detect_jaimini_raj_yogas,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.jaimini import JaiminiResult


class TestJaiminiRajYogas:
    def test_detect_returns_list(self, manish_chart: ChartData) -> None:
        karakas = compute_chara_karakas(manish_chart)
        padas = compute_arudha_padas(manish_chart)
        yogas = detect_jaimini_raj_yogas(manish_chart, karakas, padas)
        assert isinstance(yogas, list)
        assert len(yogas) >= 4  # At least 4 yoga checks always run

    def test_each_yoga_has_name(self, manish_chart: ChartData) -> None:
        karakas = compute_chara_karakas(manish_chart)
        padas = compute_arudha_padas(manish_chart)
        yogas = detect_jaimini_raj_yogas(manish_chart, karakas, padas)
        for y in yogas:
            assert y.name, "Yoga has empty name"
            assert y.name_hi, f"Yoga {y.name} has empty Hindi name"

    def test_yoga_strength_values_valid(self, manish_chart: ChartData) -> None:
        karakas = compute_chara_karakas(manish_chart)
        padas = compute_arudha_padas(manish_chart)
        yogas = detect_jaimini_raj_yogas(manish_chart, karakas, padas)
        valid_strengths = {"strong", "moderate", "weak", "none"}
        for y in yogas:
            assert y.strength in valid_strengths, (
                f"{y.name}: invalid strength '{y.strength}'"
            )

    def test_description_not_empty(self, manish_chart: ChartData) -> None:
        karakas = compute_chara_karakas(manish_chart)
        padas = compute_arudha_padas(manish_chart)
        yogas = detect_jaimini_raj_yogas(manish_chart, karakas, padas)
        for y in yogas:
            assert len(y.description) > 10, f"{y.name}: description too short"

    def test_ak_amk_yoga_detected(self, manish_chart: ChartData) -> None:
        """AK-AmK Yoga check should always be in results."""
        karakas = compute_chara_karakas(manish_chart)
        padas = compute_arudha_padas(manish_chart)
        yogas = detect_jaimini_raj_yogas(manish_chart, karakas, padas)
        names = [y.name for y in yogas]
        assert "AK-AmK Yoga" in names

    def test_karakamsha_yoga_detected(self, manish_chart: ChartData) -> None:
        karakas = compute_chara_karakas(manish_chart)
        padas = compute_arudha_padas(manish_chart)
        yogas = detect_jaimini_raj_yogas(manish_chart, karakas, padas)
        names = [y.name for y in yogas]
        assert "Karakamsha Raj Yoga" in names

    def test_compute_jaimini_includes_raj_yogas(self, manish_chart: ChartData) -> None:
        result = compute_jaimini(manish_chart)
        assert isinstance(result, JaiminiResult)
        assert isinstance(result.raj_yogas, list)
        assert len(result.raj_yogas) >= 4

    def test_present_yoga_planets_match_chart(self, manish_chart: ChartData) -> None:
        """Planets listed in a yoga should exist in the chart."""
        valid_planets = set(manish_chart.planets.keys())
        karakas = compute_chara_karakas(manish_chart)
        padas = compute_arudha_padas(manish_chart)
        yogas = detect_jaimini_raj_yogas(manish_chart, karakas, padas)
        for y in yogas:
            for p in y.planets_involved:
                assert p in valid_planets, f"{y.name}: planet '{p}' not in chart"
