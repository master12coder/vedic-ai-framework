"""Tests for chart_selector — divisional chart selection per query type."""

from __future__ import annotations

from daivai_engine.models.analysis import FullChartAnalysis
from daivai_products.decision.chart_selector import select_charts
from daivai_products.decision.models import ChartSelection


class TestSelectCharts:
    """Tests for select_charts()."""

    def test_career_query_includes_d10(self, manish_analysis: FullChartAnalysis) -> None:
        """Career query must have D10 as primary chart."""
        result = select_charts("career", manish_analysis)
        assert isinstance(result, ChartSelection)
        assert result.primary_chart == "D10"
        assert result.query_type == "career"

    def test_marriage_query_includes_d9_d7(self, manish_analysis: FullChartAnalysis) -> None:
        """Marriage query must have D9 primary and D7 in supporting."""
        result = select_charts("marriage", manish_analysis)
        assert result.primary_chart == "D9"
        assert "D7" in result.supporting_charts

    def test_health_query_includes_d1(self, manish_analysis: FullChartAnalysis) -> None:
        """Health query must include D1 in supporting charts."""
        result = select_charts("health", manish_analysis)
        assert result.primary_chart == "D30"
        assert "D1" in result.supporting_charts

    def test_general_query_returns_d1_d9(self, manish_analysis: FullChartAnalysis) -> None:
        """General query should use D1 primary with D9 in supporting."""
        result = select_charts("general", manish_analysis)
        assert result.primary_chart == "D1"
        assert "D9" in result.supporting_charts

    def test_unknown_query_falls_back_to_general(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Unknown query types must fall back to general (D1 primary)."""
        result = select_charts("astral_projection", manish_analysis)
        assert result.primary_chart == "D1"
        assert "D9" in result.supporting_charts
        # Normalized query type should reflect the input, but selection = general
        assert result.query_type == "astral_projection"

    def test_all_query_types_return_valid_charts(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Every known query type must return a valid ChartSelection."""
        known_types = [
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
        for qt in known_types:
            result = select_charts(qt, manish_analysis)
            assert isinstance(result, ChartSelection), f"Failed for query type: {qt}"
            assert result.primary_chart, f"Empty primary chart for {qt}"
            assert result.supporting_charts, f"No supporting charts for {qt}"
            assert result.reason, f"No reason string for {qt}"

    def test_reason_includes_query_context(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Reason string should mention the query type and primary chart."""
        result = select_charts("career", manish_analysis)
        assert "career" in result.reason.lower()
        assert "D10" in result.reason

    def test_whitespace_query_normalized(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Leading/trailing whitespace and case should be normalized."""
        result = select_charts("  Career  ", manish_analysis)
        assert result.query_type == "career"
        assert result.primary_chart == "D10"

    def test_children_query_primary_d7(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Children query must have D7 as primary chart."""
        result = select_charts("children", manish_analysis)
        assert result.primary_chart == "D7"

    def test_education_query_primary_d24(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Education query must have D24 as primary chart."""
        result = select_charts("education", manish_analysis)
        assert result.primary_chart == "D24"
