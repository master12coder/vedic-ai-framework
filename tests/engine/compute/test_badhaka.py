"""Tests for Badhaka Sthana computation.

Source: BPHS Ch.44-45, Jaimini Sutras.
"""

from __future__ import annotations

import pytest

from daivai_engine.compute.badhaka import (
    _determine_severity,
    _get_modality,
    _planet_aspects_house,
    compute_badhaka,
)
from daivai_engine.models.badhaka import BadhakaResult
from daivai_engine.models.chart import ChartData


class TestBadhakaStructure:
    """Tests for the overall structure of BadhakaResult output."""

    def test_returns_model_instance(self, manish_chart: ChartData) -> None:
        """compute_badhaka returns a BadhakaResult."""
        result = compute_badhaka(manish_chart)
        assert isinstance(result, BadhakaResult)

    def test_badhaka_house_valid(self, manish_chart: ChartData) -> None:
        """Badhaka house is 7, 9, or 11."""
        result = compute_badhaka(manish_chart)
        assert result.badhaka_house in (7, 9, 11)

    def test_modality_valid(self, manish_chart: ChartData) -> None:
        """Lagna modality is one of the three types."""
        result = compute_badhaka(manish_chart)
        assert result.lagna_modality in ("movable", "fixed", "dual")

    def test_severity_valid(self, manish_chart: ChartData) -> None:
        """Obstruction severity is mild, moderate, or severe."""
        result = compute_badhaka(manish_chart)
        assert result.obstruction_severity in ("mild", "moderate", "severe")

    def test_badhakesh_is_valid_planet(self, manish_chart: ChartData) -> None:
        """Badhakesh is a recognized planet."""
        valid = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        result = compute_badhaka(manish_chart)
        assert result.badhakesh in valid

    def test_badhakesh_house_in_range(self, manish_chart: ChartData) -> None:
        """Badhakesh house is 1-12."""
        result = compute_badhaka(manish_chart)
        assert 1 <= result.badhakesh_house <= 12

    def test_summary_non_empty(self, manish_chart: ChartData) -> None:
        """Summary string is non-empty."""
        result = compute_badhaka(manish_chart)
        assert result.summary


class TestModality:
    """Tests for sign modality classification."""

    @pytest.mark.parametrize(
        "sign_index,expected",
        [
            (0, "movable"),  # Aries
            (1, "fixed"),  # Taurus
            (2, "dual"),  # Gemini
            (3, "movable"),  # Cancer
            (4, "fixed"),  # Leo
            (5, "dual"),  # Virgo
            (6, "movable"),  # Libra
            (7, "fixed"),  # Scorpio
            (8, "dual"),  # Sagittarius
            (9, "movable"),  # Capricorn
            (10, "fixed"),  # Aquarius
            (11, "dual"),  # Pisces
        ],
    )
    def test_modality_classification(self, sign_index: int, expected: str) -> None:
        """Each sign maps to the correct modality."""
        assert _get_modality(sign_index) == expected


class TestBadhakaHouseByModality:
    """Tests for the badhaka house assignment per modality."""

    @pytest.mark.parametrize(
        "sign_index,expected_house",
        [
            (0, 11),  # Aries (movable) → 11th
            (3, 11),  # Cancer (movable) → 11th
            (6, 11),  # Libra (movable) → 11th
            (9, 11),  # Capricorn (movable) → 11th
            (1, 9),  # Taurus (fixed) → 9th
            (4, 9),  # Leo (fixed) → 9th
            (7, 9),  # Scorpio (fixed) → 9th
            (10, 9),  # Aquarius (fixed) → 9th
            (2, 7),  # Gemini (dual) → 7th
            (5, 7),  # Virgo (dual) → 7th
            (8, 7),  # Sagittarius (dual) → 7th
            (11, 7),  # Pisces (dual) → 7th
        ],
    )
    def test_badhaka_house_for_sign(self, sign_index: int, expected_house: int) -> None:
        """Badhaka house matches BPHS rules for each lagna type."""
        modality = _get_modality(sign_index)
        badhaka_map = {"movable": 11, "fixed": 9, "dual": 7}
        assert badhaka_map[modality] == expected_house


class TestAspectCheck:
    """Tests for planet aspects on houses."""

    def test_all_planets_aspect_7th(self) -> None:
        """Every planet aspects the 7th house from its position."""
        for house in range(1, 13):
            target = ((house - 1 + 6) % 12) + 1  # 7th house from position
            assert _planet_aspects_house("Sun", house, target)

    def test_mars_aspects_4th_and_8th(self) -> None:
        """Mars has special aspects on 4th and 8th houses."""
        # Mars in house 1 aspects house 4 and house 8
        assert _planet_aspects_house("Mars", 1, 4)
        assert _planet_aspects_house("Mars", 1, 8)

    def test_jupiter_aspects_5th_and_9th(self) -> None:
        """Jupiter has special aspects on 5th and 9th houses."""
        assert _planet_aspects_house("Jupiter", 1, 5)
        assert _planet_aspects_house("Jupiter", 1, 9)

    def test_saturn_aspects_3rd_and_10th(self) -> None:
        """Saturn has special aspects on 3rd and 10th houses."""
        assert _planet_aspects_house("Saturn", 1, 3)
        assert _planet_aspects_house("Saturn", 1, 10)

    def test_sun_does_not_aspect_3rd(self) -> None:
        """Sun has no special aspect on the 3rd house."""
        assert not _planet_aspects_house("Sun", 1, 3)


class TestSeverity:
    """Tests for severity determination logic."""

    def test_severe_dusthana_plus_nodes(self) -> None:
        """Badhakesh in dusthana + nodes involved = severe."""
        result = _determine_severity(6, True, False, False, False, False)
        assert result == "severe"

    def test_moderate_dusthana_only(self) -> None:
        """Badhakesh in dusthana but no nodes = moderate."""
        result = _determine_severity(8, False, False, False, False, False)
        assert result == "moderate"

    def test_moderate_nodes_only(self) -> None:
        """Nodes involved but not in dusthana = moderate."""
        result = _determine_severity(1, True, False, False, False, False)
        assert result == "moderate"

    def test_moderate_aspects_lagna(self) -> None:
        """Badhakesh aspecting lagna = moderate."""
        result = _determine_severity(1, False, False, False, False, True)
        assert result == "moderate"

    def test_mild_no_affliction(self) -> None:
        """No affliction = mild."""
        result = _determine_severity(5, False, False, False, False, False)
        assert result == "mild"


class TestBadhakaManish:
    """Tests with the known Manish chart (Mithuna lagna = dual)."""

    def test_mithuna_is_dual(self, manish_chart: ChartData) -> None:
        """Manish has Mithuna (Gemini) lagna which is dual."""
        result = compute_badhaka(manish_chart)
        assert result.lagna_modality == "dual"

    def test_mithuna_badhaka_7th(self, manish_chart: ChartData) -> None:
        """Dual lagna: badhaka house is 7th."""
        result = compute_badhaka(manish_chart)
        assert result.badhaka_house == 7

    def test_badhaka_sign_is_sagittarius(self, manish_chart: ChartData) -> None:
        """Mithuna lagna: 7th house = Sagittarius (Dhanu)."""
        result = compute_badhaka(manish_chart)
        # Gemini=2, 7th house sign = (2+6)%12 = 8 = Sagittarius
        assert result.badhaka_sign_index == 8
        assert result.badhaka_sign == "Sagittarius"

    def test_badhakesh_is_jupiter(self, manish_chart: ChartData) -> None:
        """Lord of Sagittarius is Jupiter."""
        result = compute_badhaka(manish_chart)
        assert result.badhakesh == "Jupiter"

    def test_domains_non_empty(self, manish_chart: ChartData) -> None:
        """Obstruction domains list is non-empty."""
        result = compute_badhaka(manish_chart)
        assert len(result.obstruction_domains) >= 1

    def test_different_charts_may_differ(
        self, manish_chart: ChartData, sample_chart: ChartData
    ) -> None:
        """Two different charts likely produce different badhaka results."""
        r1 = compute_badhaka(manish_chart)
        r2 = compute_badhaka(sample_chart)
        # Different lagnas should give different results
        assert isinstance(r2, BadhakaResult)
        # At least lagna or badhakesh should differ if lagnas differ
        if r1.lagna_sign_index != r2.lagna_sign_index:
            assert r1.badhaka_sign_index != r2.badhaka_sign_index or r1.badhakesh != r2.badhakesh
