"""Tests for cross-chart (synastry) planetary interactions."""

from __future__ import annotations

from daivai_engine.compute.cross_chart import compute_cross_chart_interactions
from daivai_engine.models.chart import ChartData


def test_cross_chart_returns_result(manish_chart: ChartData, sample_chart: ChartData):
    """Cross-chart analysis produces a CrossChartResult with valid fields."""
    result = compute_cross_chart_interactions(manish_chart, sample_chart)
    assert result.person_a == manish_chart.name
    assert result.person_b == sample_chart.name
    assert isinstance(result.overlays, list)
    assert 0 <= result.bond_strength <= 100


def test_cross_chart_finds_overlays(manish_chart: ChartData, sample_chart: ChartData):
    """Two different charts should produce at least some overlays."""
    result = compute_cross_chart_interactions(manish_chart, sample_chart)
    # With 9 planets x 9 planets and multiple aspect types, expect some hits
    assert len(result.overlays) > 0


def test_cross_chart_overlay_structure(manish_chart: ChartData, sample_chart: ChartData):
    """Each overlay has required fields populated."""
    result = compute_cross_chart_interactions(manish_chart, sample_chart)
    if result.overlays:
        ov = result.overlays[0]
        assert ov.person_a_name == manish_chart.name
        assert ov.person_b_name == sample_chart.name
        assert ov.planet_a != ""
        assert ov.planet_b != ""
        assert ov.interaction_type in ("conjunction", "opposition", "trine", "square", "sextile")
        assert ov.effect in ("supportive", "challenging", "karmic", "neutral")
        assert ov.orb_degrees >= 0


def test_cross_chart_self_is_maximal(manish_chart: ChartData):
    """A chart crossed with itself should produce many conjunctions."""
    result = compute_cross_chart_interactions(manish_chart, manish_chart)
    conjunctions = [o for o in result.overlays if o.interaction_type == "conjunction"]
    # 9 planets x 9 planets, each self-match is a perfect conjunction
    assert len(conjunctions) >= 9


def test_cross_chart_summary_populated(manish_chart: ChartData, sample_chart: ChartData):
    """Summary string is non-empty."""
    result = compute_cross_chart_interactions(manish_chart, sample_chart)
    assert len(result.summary) > 0
    assert manish_chart.name in result.summary
