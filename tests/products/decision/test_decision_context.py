"""Tests for decision context bridge (Phase 4 wiring)."""

from __future__ import annotations

from daivai_engine.models.analysis import FullChartAnalysis
from daivai_products.interpret.decision_context import build_decision_context


class TestBuildDecisionContext:
    """Verify build_decision_context returns complete, well-formed dicts."""

    def test_decision_context_has_all_keys(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Every call must produce the five standard decision keys."""
        ctx = build_decision_context("career_analysis", manish_analysis)
        expected_keys = {
            "decision_confidence_narrative",
            "decision_confidence_score",
            "decision_house_highlights",
            "decision_cross_chart",
            "decision_chart_selection",
            "decision_gemstone",
        }
        assert expected_keys.issubset(ctx.keys())

    def test_gemstone_context_included_for_gemstone_query(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Gemstone summary must be non-empty for gemstone query types."""
        ctx = build_decision_context("remedy_generation", manish_analysis)
        gemstone = ctx.get("decision_gemstone", "")
        assert gemstone, "Gemstone context must be non-empty for remedy queries"
        assert "Lagna:" in gemstone
        assert "RECOMMENDED" in gemstone or "PROHIBITED" in gemstone

    def test_gemstone_context_empty_for_career_query(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Gemstone summary must be empty for non-gemstone query types."""
        ctx = build_decision_context("career_analysis", manish_analysis)
        assert ctx.get("decision_gemstone") == ""

    def test_confidence_narrative_present(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Confidence narrative must contain score and level text."""
        ctx = build_decision_context("health_analysis", manish_analysis)
        narrative = ctx["decision_confidence_narrative"]
        assert "/100" in narrative
        assert any(w in narrative for w in ("High", "Moderate", "Low"))

    def test_house_highlights_contain_house_numbers(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """House highlights for career must mention career-relevant houses."""
        ctx = build_decision_context("career_analysis", manish_analysis)
        highlights = ctx["decision_house_highlights"]
        assert "H10" in highlights or "H1" in highlights

    def test_cross_chart_present(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Cross-chart validation must produce a non-empty summary."""
        ctx = build_decision_context("chart_overview", manish_analysis)
        cross = ctx["decision_cross_chart"]
        assert cross, "Cross-chart summary should not be empty"
        assert "D1-D9" in cross
