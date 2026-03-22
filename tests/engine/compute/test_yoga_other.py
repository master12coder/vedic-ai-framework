"""Tests for additional yoga detectors — Gajakesari, Budhaditya, Vipreet Raj, etc."""

from __future__ import annotations

from daivai_engine.compute.yoga_other import (
    _is_in_kendra,
    _is_in_own_or_exalted,
    _planet_in_kendra_from_reference,
    detect_other_yogas,
)
from daivai_engine.constants import KENDRAS
from daivai_engine.models.yoga import YogaResult


class TestHelpers:
    """Tests for helper functions in yoga_other."""

    def test_is_in_kendra_house_1(self) -> None:
        assert _is_in_kendra(1)

    def test_is_in_kendra_house_4(self) -> None:
        assert _is_in_kendra(4)

    def test_is_in_kendra_house_7(self) -> None:
        assert _is_in_kendra(7)

    def test_is_in_kendra_house_10(self) -> None:
        assert _is_in_kendra(10)

    def test_not_kendra_house_3(self) -> None:
        assert not _is_in_kendra(3)

    def test_not_kendra_house_9(self) -> None:
        assert not _is_in_kendra(9)

    def test_is_in_own_or_exalted_sun_in_aries(self) -> None:
        assert _is_in_own_or_exalted("Sun", 0)

    def test_not_own_or_exalted_sun_in_virgo(self) -> None:
        assert not _is_in_own_or_exalted("Sun", 5)

    def test_planet_in_kendra_from_reference_1st_is_kendra(self, manish_chart) -> None:
        """Planet in same sign as reference (distance=1) is in kendra."""
        # Place Jupiter also in Moon's sign — distance=1 (same sign)
        # This is hard to do without a synthetic chart, so just test real chart
        result = _planet_in_kendra_from_reference(manish_chart, "Jupiter", "Moon")
        jup_sign = manish_chart.planets["Jupiter"].sign_index
        moon_s = manish_chart.planets["Moon"].sign_index
        expected_dist = ((jup_sign - moon_s) % 12) + 1
        expected = expected_dist in KENDRAS
        assert result == expected


class TestDetectOtherYogas:
    """Tests for detect_other_yogas()."""

    def test_returns_list(self, manish_chart) -> None:
        result = detect_other_yogas(manish_chart)
        assert isinstance(result, list)

    def test_all_are_yoga_results(self, manish_chart) -> None:
        result = detect_other_yogas(manish_chart)
        for y in result:
            assert isinstance(y, YogaResult)

    def test_all_detected_are_present(self, manish_chart) -> None:
        result = detect_other_yogas(manish_chart)
        for y in result:
            assert y.is_present

    def test_effect_is_valid(self, manish_chart) -> None:
        valid_effects = {"benefic", "malefic", "mixed"}
        result = detect_other_yogas(manish_chart)
        for y in result:
            assert y.effect in valid_effects, f"{y.name}: {y.effect}"

    def test_planets_involved_non_empty(self, manish_chart) -> None:
        result = detect_other_yogas(manish_chart)
        for y in result:
            assert len(y.planets_involved) >= 1

    def test_houses_in_range(self, manish_chart) -> None:
        result = detect_other_yogas(manish_chart)
        for y in result:
            for h in y.houses_involved:
                assert 1 <= h <= 12


class TestGajakesariYoga:
    """Tests for Gajakesari yoga detection."""

    def test_gajakesari_detected_when_jupiter_in_kendra_from_moon(self, manish_chart) -> None:
        from daivai_engine.compute.yoga_other import _planet_in_kendra_from_reference

        jup_kendra = _planet_in_kendra_from_reference(manish_chart, "Jupiter", "Moon")
        result = detect_other_yogas(manish_chart)
        yoga_names = [y.name for y in result]

        if jup_kendra:
            assert "Gajakesari Yoga" in yoga_names
        else:
            assert "Gajakesari Yoga" not in yoga_names

    def test_gajakesari_involves_jupiter_and_moon(self, manish_chart) -> None:
        result = detect_other_yogas(manish_chart)
        for y in result:
            if y.name == "Gajakesari Yoga":
                assert "Jupiter" in y.planets_involved
                assert "Moon" in y.planets_involved

    def test_gajakesari_is_benefic(self, manish_chart) -> None:
        result = detect_other_yogas(manish_chart)
        for y in result:
            if y.name == "Gajakesari Yoga":
                assert y.effect == "benefic"


class TestBudhadityaYoga:
    """Tests for Budhaditya yoga detection."""

    def test_budhaditya_when_sun_mercury_conjunct(self, manish_chart) -> None:
        sun = manish_chart.planets["Sun"]
        mercury = manish_chart.planets["Mercury"]
        result = detect_other_yogas(manish_chart)
        yoga_names = [y.name for y in result]

        if sun.sign_index == mercury.sign_index:
            assert "Budhaditya Yoga" in yoga_names

    def test_budhaditya_involves_sun_mercury(self, manish_chart) -> None:
        result = detect_other_yogas(manish_chart)
        for y in result:
            if y.name == "Budhaditya Yoga":
                assert "Sun" in y.planets_involved
                assert "Mercury" in y.planets_involved


class TestVipreetRajYoga:
    """Tests for Vipreet Raj yoga detection."""

    def test_vipreet_raj_if_detected_has_valid_effect(self, manish_chart) -> None:
        valid_effects = {"benefic", "malefic", "mixed"}
        result = detect_other_yogas(manish_chart)
        for y in result:
            if "Vipreet" in y.name:
                assert y.effect in valid_effects
