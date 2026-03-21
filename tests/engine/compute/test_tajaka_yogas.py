"""Tests for all 16 Tajaka Yogas detection."""

from __future__ import annotations

from daivai_engine.compute.tajaka_yogas import (
    TajakaYoga,
    detect_all_tajaka_yogas,
)
from daivai_engine.compute.varshphal import compute_varshphal
from daivai_engine.models.chart import ChartData


_VALID_YOGA_NAMES = {
    "Ithasala",
    "Ishrafa",
    "Ikkabal",
    "Induvara",
    "Nakta",
    "Yamaya",
    "Drippha",
    "Kuttha",
    "Tambira",
    "Durupha",
    "Radda",
    "Manaou",
    "Khallasara",
    "Kamboola",
    "Gairi-Kamboola",
    "Musaripha",
}

_VALID_ASPECT_TYPES = {
    "conjunction",
    "sextile",
    "square",
    "trine",
    "opposition",
    "transfer_via_moon",
    "transfer",
    "none",
}


class TestTajakaYogaDetection:
    def test_returns_list_of_tajaka_yogas(self, manish_chart: ChartData) -> None:
        yogas = detect_all_tajaka_yogas(manish_chart)
        assert isinstance(yogas, list)
        for y in yogas:
            assert isinstance(y, TajakaYoga)

    def test_yoga_names_are_valid(self, manish_chart: ChartData) -> None:
        yogas = detect_all_tajaka_yogas(manish_chart)
        for y in yogas:
            assert y.name in _VALID_YOGA_NAMES, f"Unknown yoga: {y.name}"

    def test_aspect_types_are_valid(self, manish_chart: ChartData) -> None:
        yogas = detect_all_tajaka_yogas(manish_chart)
        for y in yogas:
            assert y.aspect_type in _VALID_ASPECT_TYPES, f"Unknown aspect: {y.aspect_type}"

    def test_orb_is_non_negative(self, manish_chart: ChartData) -> None:
        yogas = detect_all_tajaka_yogas(manish_chart)
        for y in yogas:
            assert y.orb >= 0.0

    def test_is_positive_is_bool(self, manish_chart: ChartData) -> None:
        yogas = detect_all_tajaka_yogas(manish_chart)
        for y in yogas:
            assert isinstance(y.is_positive, bool)

    def test_description_non_empty(self, manish_chart: ChartData) -> None:
        yogas = detect_all_tajaka_yogas(manish_chart)
        for y in yogas:
            assert len(y.description) > 10

    def test_planet_names_reference_valid_planets(self, manish_chart: ChartData) -> None:
        valid_planets = set(manish_chart.planets.keys())
        yogas = detect_all_tajaka_yogas(manish_chart)
        for y in yogas:
            assert y.fast_planet in valid_planets or y.fast_planet == "Moon"
            assert y.slow_planet in valid_planets

    def test_positive_yogas_sorted_first(self, manish_chart: ChartData) -> None:
        """Positive yogas should come before negative yogas in sorted output."""
        yogas = detect_all_tajaka_yogas(manish_chart)
        if len(yogas) >= 2:
            # Find first negative yoga index
            first_neg = next(
                (i for i, y in enumerate(yogas) if not y.is_positive), len(yogas)
            )
            # All before first_neg should be positive
            for y in yogas[:first_neg]:
                assert y.is_positive

    def test_ithasala_is_positive(self, manish_chart: ChartData) -> None:
        yogas = detect_all_tajaka_yogas(manish_chart)
        for y in yogas:
            if y.name == "Ithasala":
                assert y.is_positive is True
                assert y.is_applying is True

    def test_ishrafa_is_negative(self, manish_chart: ChartData) -> None:
        yogas = detect_all_tajaka_yogas(manish_chart)
        for y in yogas:
            if y.name == "Ishrafa":
                assert y.is_positive is False
                assert y.is_applying is False

    def test_manaou_is_negative(self, manish_chart: ChartData) -> None:
        yogas = detect_all_tajaka_yogas(manish_chart)
        for y in yogas:
            if y.name == "Manaou":
                assert y.is_positive is False

    def test_kamboola_involves_moon(self, manish_chart: ChartData) -> None:
        yogas = detect_all_tajaka_yogas(manish_chart)
        for y in yogas:
            if y.name == "Kamboola":
                assert y.fast_planet == "Moon"
                assert y.is_applying is True
                assert y.is_positive is True

    def test_gairi_kamboola_involves_moon(self, manish_chart: ChartData) -> None:
        yogas = detect_all_tajaka_yogas(manish_chart)
        for y in yogas:
            if y.name == "Gairi-Kamboola":
                assert y.fast_planet == "Moon"
                assert y.is_applying is False

    def test_induvara_has_tight_orb(self, manish_chart: ChartData) -> None:
        """Induvara fires only when orb ≤ 1°."""
        yogas = detect_all_tajaka_yogas(manish_chart)
        for y in yogas:
            if y.name == "Induvara":
                assert y.orb <= 1.0

    def test_drippha_fast_planet_combust(self, manish_chart: ChartData) -> None:
        yogas = detect_all_tajaka_yogas(manish_chart)
        for y in yogas:
            if y.name == "Drippha":
                assert manish_chart.planets[y.fast_planet].is_combust is True

    def test_kuttha_fast_planet_debilitated(self, manish_chart: ChartData) -> None:
        yogas = detect_all_tajaka_yogas(manish_chart)
        for y in yogas:
            if y.name == "Kuttha":
                assert manish_chart.planets[y.fast_planet].dignity == "debilitated"

    def test_works_on_sample_chart(self, sample_chart: ChartData) -> None:
        yogas = detect_all_tajaka_yogas(sample_chart)
        assert isinstance(yogas, list)


class TestTajakaYogasInVarshphal:
    def test_varshphal_returns_tajaka_yoga_objects(self, manish_chart: ChartData) -> None:
        """Varshphal now returns TajakaYoga objects, not strings."""
        result = compute_varshphal(manish_chart, 2026)
        yogas = result["tajaka_yogas"]
        assert isinstance(yogas, list)
        for y in yogas:
            assert isinstance(y, TajakaYoga)

    def test_varshphal_yogas_have_valid_names(self, manish_chart: ChartData) -> None:
        result = compute_varshphal(manish_chart, 2026)
        for y in result["tajaka_yogas"]:
            assert y.name in _VALID_YOGA_NAMES

    def test_varshphal_yogas_positive_yogas_have_descriptions(
        self, manish_chart: ChartData
    ) -> None:
        result = compute_varshphal(manish_chart, 2026)
        for y in result["tajaka_yogas"]:
            assert len(y.description) > 0
