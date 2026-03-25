"""Tests for gemstone conjunction penalty computation."""

from __future__ import annotations

from daivai_engine.compute.conjunction_penalty import compute_conjunction_penalty
from daivai_engine.models.chart import ChartData


def test_conjunction_penalty_returns_result(manish_chart: ChartData):
    """compute_conjunction_penalty returns a valid ConjunctionPenalty."""
    result = compute_conjunction_penalty(manish_chart, "Mercury")
    assert result.planet == "Mercury"
    assert isinstance(result.has_penalty, bool)
    assert 0 <= result.penalty_factor <= 1.0
    assert isinstance(result.conjunct_with, list)
    assert len(result.reasoning) > 0


def test_no_penalty_when_no_malefic_conjunction(manish_chart: ChartData):
    """A planet not conjunct any malefic should have penalty_factor = 1.0."""
    # Test all planets; at least some should have no penalty
    no_penalty_found = False
    for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        result = compute_conjunction_penalty(manish_chart, planet)
        if not result.has_penalty:
            assert result.penalty_factor == 1.0
            assert result.conjunct_with == []
            no_penalty_found = True
    # At least one planet should have no penalty in a typical chart
    assert no_penalty_found


def test_penalty_factor_within_bounds(manish_chart: ChartData):
    """Penalty factor should be between 0.50 and 1.0."""
    for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        result = compute_conjunction_penalty(manish_chart, planet)
        assert 0.50 <= result.penalty_factor <= 1.0


def test_penalty_reasoning_includes_conjuncts(manish_chart: ChartData):
    """When penalty exists, reasoning should mention conjunct partners."""
    for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        result = compute_conjunction_penalty(manish_chart, planet)
        if result.has_penalty:
            for partner in result.conjunct_with:
                # Partner name or label should appear in reasoning
                assert partner.split(" ")[0] in result.reasoning or "reduce" in result.reasoning.lower()
