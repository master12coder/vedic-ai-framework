"""Tests for planetary conjunction yoga detection."""

from __future__ import annotations

from daivai_engine.compute.yoga_conjunctions import (
    detect_conjunction_yogas,
    detect_daridra_extended,
    detect_sunapha_anapha_specific,
)
from daivai_engine.models.yoga import YogaResult


class TestDetectConjunctionYogas:
    """Tests for detect_conjunction_yogas()."""

    def test_returns_list(self, manish_chart) -> None:
        result = detect_conjunction_yogas(manish_chart)
        assert isinstance(result, list)

    def test_all_are_yoga_results(self, manish_chart) -> None:
        result = detect_conjunction_yogas(manish_chart)
        for y in result:
            assert isinstance(y, YogaResult)

    def test_all_detected_are_present(self, manish_chart) -> None:
        result = detect_conjunction_yogas(manish_chart)
        for y in result:
            assert y.is_present

    def test_effect_is_valid(self, manish_chart) -> None:
        valid_effects = {"benefic", "malefic", "mixed"}
        result = detect_conjunction_yogas(manish_chart)
        for y in result:
            assert y.effect in valid_effects, f"{y.name}: {y.effect}"

    def test_conjunction_requires_same_sign(self, manish_chart) -> None:
        """All detected conjunction yogas must have both planets in same sign."""
        result = detect_conjunction_yogas(manish_chart)
        for y in result:
            if len(y.planets_involved) == 2:
                p1 = manish_chart.planets[y.planets_involved[0]]
                p2 = manish_chart.planets[y.planets_involved[1]]
                assert p1.sign_index == p2.sign_index, (
                    f"{y.name}: {y.planets_involved[0]} in {p1.sign_index}, "
                    f"{y.planets_involved[1]} in {p2.sign_index}"
                )

    def test_yoga_names_include_yoga(self, manish_chart) -> None:
        result = detect_conjunction_yogas(manish_chart)
        for y in result:
            assert "Yoga" in y.name or "Conjunction" in y.name

    def test_houses_in_range(self, manish_chart) -> None:
        result = detect_conjunction_yogas(manish_chart)
        for y in result:
            for h in y.houses_involved:
                assert 1 <= h <= 12

    def test_malefic_in_upachaya_becomes_mixed(self, manish_chart) -> None:
        """Malefic conjunction in 3/6/10/11 should be mixed."""
        result = detect_conjunction_yogas(manish_chart)
        upachaya = {3, 6, 10, 11}
        for y in result:
            if y.effect == "malefic" and y.houses_involved:
                assert y.houses_involved[0] not in upachaya, (
                    f"{y.name} in house {y.houses_involved[0]} should be mixed"
                )


class TestDetectSunaphaAnapha:
    """Tests for detect_sunapha_anapha_specific()."""

    def test_returns_list(self, manish_chart) -> None:
        result = detect_sunapha_anapha_specific(manish_chart)
        assert isinstance(result, list)

    def test_all_are_yoga_results(self, manish_chart) -> None:
        result = detect_sunapha_anapha_specific(manish_chart)
        for y in result:
            assert isinstance(y, YogaResult)

    def test_sunapha_involves_moon(self, manish_chart) -> None:
        result = detect_sunapha_anapha_specific(manish_chart)
        for y in result:
            if "Sunapha" in y.name:
                assert "Moon" in y.planets_involved

    def test_anapha_involves_moon(self, manish_chart) -> None:
        result = detect_sunapha_anapha_specific(manish_chart)
        for y in result:
            if "Anapha" in y.name:
                assert "Moon" in y.planets_involved

    def test_no_sun_in_sunapha_anapha(self, manish_chart) -> None:
        """Sun never appears in Sunapha/Anapha — only Mars/Mercury/Jupiter/Venus/Saturn."""
        result = detect_sunapha_anapha_specific(manish_chart)
        for y in result:
            if "Sunapha" in y.name or "Anapha" in y.name:
                assert "Sun" not in y.planets_involved

    def test_sunapha_in_2nd_from_moon(self, manish_chart) -> None:
        moon = manish_chart.planets["Moon"]
        sign_2nd = (moon.sign_index + 1) % 12
        result = detect_sunapha_anapha_specific(manish_chart)
        for y in result:
            if "Sunapha" in y.name:
                # Planet in 2nd from Moon
                planet_name = next(p for p in y.planets_involved if p != "Moon")
                assert manish_chart.planets[planet_name].sign_index == sign_2nd

    def test_effect_is_valid(self, manish_chart) -> None:
        result = detect_sunapha_anapha_specific(manish_chart)
        valid_effects = {"benefic", "malefic", "mixed"}
        for y in result:
            assert y.effect in valid_effects


class TestDetectDaridrExtended:
    """Tests for detect_daridra_extended()."""

    def test_returns_list(self, manish_chart) -> None:
        result = detect_daridra_extended(manish_chart)
        assert isinstance(result, list)

    def test_all_are_yoga_results(self, manish_chart) -> None:
        result = detect_daridra_extended(manish_chart)
        for y in result:
            assert isinstance(y, YogaResult)

    def test_daridra_are_malefic(self, manish_chart) -> None:
        result = detect_daridra_extended(manish_chart)
        for y in result:
            assert y.effect == "malefic"

    def test_daridra_name_in_yoga_name(self, manish_chart) -> None:
        result = detect_daridra_extended(manish_chart)
        for y in result:
            assert "Daridra" in y.name

    def test_houses_in_range(self, manish_chart) -> None:
        result = detect_daridra_extended(manish_chart)
        for y in result:
            for h in y.houses_involved:
                assert 1 <= h <= 12
