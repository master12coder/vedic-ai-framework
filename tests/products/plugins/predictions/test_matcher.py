"""Tests for the dasha-event matcher."""

from __future__ import annotations

from daivai_engine.compute.full_analysis import compute_full_analysis
from daivai_engine.models.analysis import FullChartAnalysis
from daivai_engine.models.chart import ChartData
from daivai_products.plugins.predictions.engine import summarize_matches
from daivai_products.plugins.predictions.matcher import (
    DashaEventMatch,
    match_events_to_dashas,
)
from daivai_products.store.events import LifeEvent


def _make_analysis(chart: ChartData) -> FullChartAnalysis:
    """Build a full analysis from a chart fixture."""
    from daivai_products.interpret.context import build_lordship_context

    ctx = build_lordship_context(chart.lagna_sign)
    return compute_full_analysis(chart, lordship_context=ctx)


class TestMatchEventsToDashas:
    def test_match_events_returns_matches(self, manish_chart: ChartData) -> None:
        """match_events_to_dashas should return a DashaEventMatch per event."""
        analysis = _make_analysis(manish_chart)

        events = [
            LifeEvent(
                chart_id=1,
                event_date="2015-06-15",
                event_type="career",
                description="First full-time job",
            ),
            LifeEvent(
                chart_id=1,
                event_date="2020-03-01",
                event_type="career",
                description="Job promotion",
            ),
        ]

        matches = match_events_to_dashas(analysis, events)
        assert len(matches) == 2
        for m in matches:
            assert isinstance(m, DashaEventMatch)
            assert m.dasha_lord != "Unknown"
            assert m.antardasha_lord != "Unknown"
            assert m.event_type == "career"

    def test_match_quality_values_valid(self, manish_chart: ChartData) -> None:
        """Every match quality should be one of strong/moderate/weak."""
        analysis = _make_analysis(manish_chart)

        events = [
            LifeEvent(
                chart_id=1,
                event_date="2012-07-01",
                event_type="education",
                description="College graduation",
            ),
            LifeEvent(
                chart_id=1,
                event_date="2018-01-10",
                event_type="health",
                description="Surgery",
            ),
        ]

        matches = match_events_to_dashas(analysis, events)
        valid_qualities = {"strong", "moderate", "weak"}
        for m in matches:
            assert m.match_quality in valid_qualities

    def test_empty_events_returns_empty(self, manish_chart: ChartData) -> None:
        """Empty events list should return empty matches."""
        analysis = _make_analysis(manish_chart)
        matches = match_events_to_dashas(analysis, [])
        assert matches == []

    def test_summarize_matches_output(self, manish_chart: ChartData) -> None:
        """summarize_matches should produce a formatted report."""
        analysis = _make_analysis(manish_chart)
        events = [
            LifeEvent(
                chart_id=1,
                event_date="2015-06-15",
                event_type="career",
                description="First full-time job",
            ),
        ]
        matches = match_events_to_dashas(analysis, events)
        report = summarize_matches(matches)
        assert "Dasha-Event Match Report" in report
        assert "First full-time job" in report

    def test_summarize_empty_matches(self) -> None:
        """summarize_matches with empty list should return informative message."""
        report = summarize_matches([])
        assert "No event-dasha matches" in report

    def test_unparseable_date_skipped(self, manish_chart: ChartData) -> None:
        """Events with unparseable dates should be silently skipped."""
        analysis = _make_analysis(manish_chart)
        events = [
            LifeEvent(
                chart_id=1,
                event_date="not-a-date",
                event_type="career",
                description="Bad date event",
            ),
        ]
        matches = match_events_to_dashas(analysis, events)
        assert matches == []
