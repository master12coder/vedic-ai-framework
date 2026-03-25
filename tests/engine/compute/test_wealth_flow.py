"""Tests for wealth flow classification."""

from __future__ import annotations

from daivai_engine.compute.wealth_flow import classify_wealth_flow
from daivai_engine.models.chart import ChartData


def test_wealth_flow_returns_profile(manish_chart: ChartData):
    """classify_wealth_flow produces a valid WealthFlowProfile."""
    profile = classify_wealth_flow(manish_chart)
    assert profile.name == manish_chart.name
    assert profile.archetype in ("earner", "accumulator", "distributor", "mixed")
    assert 0 <= profile.wealth_score <= 100
    assert profile.second_lord != ""
    assert profile.tenth_lord != ""
    assert profile.eleventh_lord != ""
    assert 1 <= profile.second_lord_house <= 12
    assert 1 <= profile.tenth_lord_house <= 12
    assert 1 <= profile.eleventh_lord_house <= 12


def test_wealth_flow_description_populated(manish_chart: ChartData):
    """Description contains lord placement details."""
    profile = classify_wealth_flow(manish_chart)
    assert len(profile.description) > 0
    # Description should mention at least one lord
    assert any(lord in profile.description for lord in ["2nd", "10th", "11th"])


def test_wealth_flow_different_charts(manish_chart: ChartData, sample_chart: ChartData):
    """Different charts can produce different archetypes."""
    profile_m = classify_wealth_flow(manish_chart)
    profile_s = classify_wealth_flow(sample_chart)
    # Both should be valid archetypes (may or may not differ)
    assert profile_m.archetype in ("earner", "accumulator", "distributor", "mixed")
    assert profile_s.archetype in ("earner", "accumulator", "distributor", "mixed")
