"""Tests for the main yoga detection engine — detect_all_yogas and helpers."""

from __future__ import annotations

from daivai_engine.compute.yoga import (
    _detect_dhan_yogas,
    _detect_panch_mahapurush,
    _detect_raj_yogas,
    _is_in_kendra,
    _is_in_own_or_exalted,
    detect_all_yogas,
)
from daivai_engine.constants import EXALTATION, KENDRAS
from daivai_engine.models.yoga import YogaResult


class TestIsInKendra:
    """Tests for the _is_in_kendra() helper."""

    def test_house_1_is_kendra(self) -> None:
        assert _is_in_kendra(1)

    def test_house_4_is_kendra(self) -> None:
        assert _is_in_kendra(4)

    def test_house_7_is_kendra(self) -> None:
        assert _is_in_kendra(7)

    def test_house_10_is_kendra(self) -> None:
        assert _is_in_kendra(10)

    def test_house_2_not_kendra(self) -> None:
        assert not _is_in_kendra(2)

    def test_house_5_not_kendra(self) -> None:
        assert not _is_in_kendra(5)

    def test_all_kendras_identified(self) -> None:
        for h in KENDRAS:
            assert _is_in_kendra(h)


class TestIsInOwnOrExalted:
    """Tests for _is_in_own_or_exalted()."""

    def test_sun_in_exaltation_sign(self) -> None:
        # Sun exalted in Aries (sign_index=0)
        assert _is_in_own_or_exalted("Sun", EXALTATION["Sun"])

    def test_sun_in_own_sign_leo(self) -> None:
        # Sun own in Leo (sign_index=4)
        assert _is_in_own_or_exalted("Sun", 4)

    def test_sun_in_neutral_sign_cancer(self) -> None:
        assert not _is_in_own_or_exalted("Sun", 3)

    def test_jupiter_in_own_sign_sagittarius(self) -> None:
        assert _is_in_own_or_exalted("Jupiter", 8)

    def test_jupiter_exalted_in_cancer(self) -> None:
        assert _is_in_own_or_exalted("Jupiter", EXALTATION["Jupiter"])


class TestDetectAllYogas:
    """Integration tests for detect_all_yogas()."""

    def test_returns_list(self, manish_chart) -> None:
        yogas = detect_all_yogas(manish_chart)
        assert isinstance(yogas, list)

    def test_all_elements_are_yoga_results(self, manish_chart) -> None:
        yogas = detect_all_yogas(manish_chart)
        for y in yogas:
            assert isinstance(y, YogaResult)

    def test_all_yogas_marked_present(self, manish_chart) -> None:
        yogas = detect_all_yogas(manish_chart)
        for y in yogas:
            assert y.is_present

    def test_effect_is_valid_value(self, manish_chart) -> None:
        valid_effects = {"benefic", "malefic", "mixed", "neutral"}
        yogas = detect_all_yogas(manish_chart)
        for y in yogas:
            assert y.effect in valid_effects, f"{y.name} has invalid effect: {y.effect}"

    def test_planets_involved_is_list(self, manish_chart) -> None:
        yogas = detect_all_yogas(manish_chart)
        for y in yogas:
            assert isinstance(y.planets_involved, list)

    def test_houses_involved_in_range(self, manish_chart) -> None:
        yogas = detect_all_yogas(manish_chart)
        for y in yogas:
            for h in y.houses_involved:
                assert 1 <= h <= 12, f"{y.name} has house {h}"

    def test_yoga_names_non_empty(self, manish_chart) -> None:
        yogas = detect_all_yogas(manish_chart)
        for y in yogas:
            assert y.name, f"Yoga has empty name: {y}"

    def test_at_least_one_yoga_detected(self, manish_chart) -> None:
        yogas = detect_all_yogas(manish_chart)
        assert len(yogas) >= 1


class TestPanchMahapurush:
    """Tests for _detect_panch_mahapurush()."""

    def test_returns_list(self, manish_chart) -> None:
        yogas = _detect_panch_mahapurush(manish_chart)
        assert isinstance(yogas, list)

    def test_max_five_panch_mahapurush(self, manish_chart) -> None:
        yogas = _detect_panch_mahapurush(manish_chart)
        assert len(yogas) <= 5

    def test_panch_mahapurush_names_valid(self, manish_chart) -> None:
        valid_names = {"Hamsa", "Malavya", "Sasa", "Ruchaka", "Bhadra"}
        yogas = _detect_panch_mahapurush(manish_chart)
        for y in yogas:
            assert y.name in valid_names

    def test_all_panch_are_benefic(self, manish_chart) -> None:
        yogas = _detect_panch_mahapurush(manish_chart)
        for y in yogas:
            assert y.effect == "benefic"


class TestRajYogas:
    """Tests for _detect_raj_yogas()."""

    def test_returns_list(self, manish_chart) -> None:
        yogas = _detect_raj_yogas(manish_chart)
        assert isinstance(yogas, list)

    def test_raj_yogas_all_benefic(self, manish_chart) -> None:
        yogas = _detect_raj_yogas(manish_chart)
        for y in yogas:
            assert y.effect == "benefic"

    def test_raj_yoga_names_contain_raj(self, manish_chart) -> None:
        yogas = _detect_raj_yogas(manish_chart)
        for y in yogas:
            assert "Raj" in y.name or "Dharma" in y.name


class TestDhanYogas:
    """Tests for _detect_dhan_yogas()."""

    def test_returns_list(self, manish_chart) -> None:
        yogas = _detect_dhan_yogas(manish_chart)
        assert isinstance(yogas, list)

    def test_dhan_yoga_names_contain_dhan(self, manish_chart) -> None:
        yogas = _detect_dhan_yogas(manish_chart)
        for y in yogas:
            assert "Dhan" in y.name

    def test_dhan_yogas_all_benefic(self, manish_chart) -> None:
        yogas = _detect_dhan_yogas(manish_chart)
        for y in yogas:
            assert y.effect == "benefic"
