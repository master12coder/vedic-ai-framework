"""Tests for house_highlighter — relevant house identification per query type."""

from __future__ import annotations

from daivai_engine.models.analysis import FullChartAnalysis
from daivai_products.decision.house_highlighter import highlight_houses
from daivai_products.decision.models import HouseHighlight


# Valid planet names that can appear as karakas
_VALID_PLANETS = {
    "Sun",
    "Moon",
    "Mars",
    "Mercury",
    "Jupiter",
    "Venus",
    "Saturn",
    "Rahu",
    "Ketu",
}


class TestHighlightHouses:
    """Tests for highlight_houses()."""

    def test_career_highlights_10th_house(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Career query must include house 10 in primary houses."""
        result = highlight_houses("career", manish_analysis)
        assert isinstance(result, HouseHighlight)
        assert 10 in result.primary_houses

    def test_marriage_highlights_7th_house(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Marriage query must include house 7 in primary houses."""
        result = highlight_houses("marriage", manish_analysis)
        assert 7 in result.primary_houses

    def test_primary_houses_never_empty(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Primary houses must never be empty for any query type."""
        query_types = [
            "career",
            "marriage",
            "health",
            "children",
            "education",
            "wealth",
            "spiritual",
            "general",
            "property",
            "longevity",
        ]
        for qt in query_types:
            result = highlight_houses(qt, manish_analysis)
            assert len(result.primary_houses) > 0, f"No primary houses for {qt}"

    def test_karaka_planets_are_valid(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """All karaka planets must be valid planet names."""
        query_types = [
            "career",
            "marriage",
            "health",
            "children",
            "education",
            "wealth",
            "spiritual",
            "general",
            "property",
            "longevity",
        ]
        for qt in query_types:
            result = highlight_houses(qt, manish_analysis)
            for planet in result.karaka_planets:
                assert planet in _VALID_PLANETS, (
                    f"Invalid karaka '{planet}' for query '{qt}'"
                )

    def test_all_query_types_return_valid_highlights(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Every known query type must produce a valid HouseHighlight."""
        query_types = [
            "career",
            "marriage",
            "health",
            "children",
            "education",
            "wealth",
            "spiritual",
            "general",
            "property",
            "longevity",
        ]
        for qt in query_types:
            result = highlight_houses(qt, manish_analysis)
            assert isinstance(result, HouseHighlight), f"Wrong type for {qt}"
            assert result.query_type == qt
            assert result.reason, f"Empty reason for {qt}"
            # Houses should be valid (1-12)
            for h in result.primary_houses + result.supporting_houses:
                assert 1 <= h <= 12, f"Invalid house {h} for {qt}"

    def test_health_includes_6th_and_8th(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Health query must include house 6 and 8 in primary houses."""
        result = highlight_houses("health", manish_analysis)
        assert 6 in result.primary_houses
        assert 8 in result.primary_houses

    def test_wealth_includes_2nd_and_11th(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Wealth query must include house 2 and 11 in primary houses."""
        result = highlight_houses("wealth", manish_analysis)
        assert 2 in result.primary_houses
        assert 11 in result.primary_houses

    def test_unknown_query_falls_back_to_general(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Unknown query types must fall back to general house selection."""
        result = highlight_houses("time_travel", manish_analysis)
        # General has primary houses [1, 7, 10]
        assert 1 in result.primary_houses
        assert 7 in result.primary_houses
        assert 10 in result.primary_houses

    def test_general_resolves_karakas_dynamically(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """General query should dynamically resolve karakas (includes lagna lord)."""
        result = highlight_houses("general", manish_analysis)
        # Manish's lagna lord is Mercury — should appear in karakas
        assert "Mercury" in result.karaka_planets
        # Sun and Moon are also added for general overview
        assert "Sun" in result.karaka_planets
        assert "Moon" in result.karaka_planets

    def test_no_duplicate_houses(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Primary and supporting houses should not overlap."""
        query_types = ["career", "marriage", "health", "wealth"]
        for qt in query_types:
            result = highlight_houses(qt, manish_analysis)
            overlap = set(result.primary_houses) & set(result.supporting_houses)
            assert not overlap, (
                f"Houses {overlap} appear in both primary and supporting for {qt}"
            )
