"""Tests for golden_period, prohibited_stones, and accuracy_cert renderers."""
from __future__ import annotations

import pytest

from jyotish_engine.compute.chart import compute_chart
from jyotish_engine.compute.dasha import compute_mahadashas
from jyotish_engine.models.chart import ChartData
from jyotish_products.interpret.context import build_lordship_context
from jyotish_products.plugins.kundali.accuracy_cert import render_accuracy_cert
from jyotish_products.plugins.kundali.golden_period import render_golden_period
from jyotish_products.plugins.kundali.prohibited_stones import render_prohibited_stones
from jyotish_products.plugins.remedies.gemstone import compute_gemstone_weights


@pytest.fixture
def manish_chart() -> ChartData:
    return compute_chart(
        name="Manish Chaurasia", dob="13/03/1989", tob="12:17",
        lat=25.3176, lon=83.0067, tz_name="Asia/Kolkata", gender="Male",
    )


@pytest.fixture
def mithuna_ctx() -> dict:
    return build_lordship_context("Mithuna")


class TestGoldenPeriod:
    def test_returns_flowables(self, manish_chart: ChartData, mithuna_ctx: dict) -> None:
        mahadashas = compute_mahadashas(manish_chart)
        elements = render_golden_period(manish_chart, mahadashas, mithuna_ctx)
        assert isinstance(elements, list)
        assert len(elements) >= 2  # heading + card

    def test_finds_benefic_period(self, manish_chart: ChartData, mithuna_ctx: dict) -> None:
        """Should find at least one benefic period for Mithuna (Mercury, Venus, Saturn)."""
        mahadashas = compute_mahadashas(manish_chart)
        elements = render_golden_period(manish_chart, mahadashas, mithuna_ctx)
        # Should have card element (not just "no period found")
        assert len(elements) >= 2

    def test_handles_empty_context(self, manish_chart: ChartData) -> None:
        mahadashas = compute_mahadashas(manish_chart)
        elements = render_golden_period(manish_chart, mahadashas, {})
        assert isinstance(elements, list)
        assert len(elements) >= 1


class TestProhibitedStones:
    def test_returns_flowables(self, manish_chart: ChartData) -> None:
        results = compute_gemstone_weights(manish_chart, 78.0)
        elements = render_prohibited_stones(results, "Mithuna")
        assert isinstance(elements, list)
        assert len(elements) >= 3  # heading + table + alternatives

    @pytest.mark.safety
    def test_pukhraj_in_prohibited_table(self, manish_chart: ChartData) -> None:
        """Pukhraj must appear in the prohibited section."""
        results = compute_gemstone_weights(manish_chart, 78.0)
        elements = render_prohibited_stones(results, "Mithuna")
        # Check table data contains Pukhraj
        table_found = False
        for elem in elements:
            if hasattr(elem, "_cellvalues"):
                for row in elem._cellvalues:
                    for cell in row:
                        if "Yellow Sapphire" in str(cell):
                            table_found = True
        assert table_found, "Pukhraj (Yellow Sapphire) not found in prohibited table"

    def test_includes_free_alternatives(self, manish_chart: ChartData) -> None:
        results = compute_gemstone_weights(manish_chart, 78.0)
        elements = render_prohibited_stones(results, "Mithuna")
        assert len(elements) >= 4  # heading + table + alt heading + alt items

    def test_handles_no_prohibited(self) -> None:
        """Should handle case where no stones are prohibited."""
        elements = render_prohibited_stones([], "Test")
        assert len(elements) >= 1


class TestAccuracyCert:
    def test_returns_flowables(self, manish_chart: ChartData) -> None:
        elements = render_accuracy_cert(manish_chart)
        assert isinstance(elements, list)
        assert len(elements) >= 5  # heading + table + verification + disclaimer + github

    def test_includes_ayanamsha(self, manish_chart: ChartData) -> None:
        """Certificate should include ayanamsha value."""
        elements = render_accuracy_cert(manish_chart)
        # Check table has ayanamsha row
        table_found = False
        for elem in elements:
            if hasattr(elem, "_cellvalues"):
                for row in elem._cellvalues:
                    for cell in row:
                        if "Lahiri" in str(cell):
                            table_found = True
        assert table_found

    def test_includes_coordinates(self, manish_chart: ChartData) -> None:
        """Certificate should include birth coordinates."""
        elements = render_accuracy_cert(manish_chart)
        table_found = False
        for elem in elements:
            if hasattr(elem, "_cellvalues"):
                for row in elem._cellvalues:
                    for cell in row:
                        if "25." in str(cell) and "83." in str(cell):
                            table_found = True
        assert table_found
