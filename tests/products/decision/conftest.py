"""Shared fixtures for decision engine tests."""

from __future__ import annotations

import pytest

from daivai_engine.compute.full_analysis import compute_full_analysis
from daivai_engine.models.analysis import FullChartAnalysis
from daivai_engine.models.chart import ChartData
from daivai_products.interpret.context import build_lordship_context


@pytest.fixture
def manish_analysis(manish_chart: ChartData) -> FullChartAnalysis:
    """Full pre-computed analysis for Manish Chaurasia's chart.

    Mithuna lagna, Mercury lagnesh, Jupiter 7th-lord maraka.
    """
    lordship_ctx = build_lordship_context(manish_chart.lagna_sign)
    return compute_full_analysis(manish_chart, lordship_context=lordship_ctx)
