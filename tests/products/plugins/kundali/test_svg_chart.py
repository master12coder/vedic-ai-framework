"""Tests for the SVG diamond chart renderer."""

from __future__ import annotations

from daivai_engine.models.chart import ChartData
from daivai_products.interpret.context import build_lordship_context
from daivai_products.plugins.kundali.svg_chart import (
    render_d1_svg,
    render_divisional_svg,
)


class TestRenderD1Svg:
    def test_svg_returns_string(self, manish_chart: ChartData) -> None:
        ctx = build_lordship_context(manish_chart.lagna_sign)
        svg = render_d1_svg(manish_chart, ctx)
        assert isinstance(svg, str)
        assert svg.startswith("<svg")
        assert svg.strip().endswith("</svg>")

    def test_svg_contains_all_nine_planets(self, manish_chart: ChartData) -> None:
        """All 9 planets should appear in the SVG."""
        ctx = build_lordship_context(manish_chart.lagna_sign)
        svg = render_d1_svg(manish_chart, ctx)
        planet_abbrs = ["सू", "चं", "मं", "बु", "गु", "शु", "श", "रा", "के"]
        for abbr in planet_abbrs:
            assert abbr in svg, f"Planet abbreviation '{abbr}' missing from SVG"

    def test_svg_has_correct_viewbox(self, manish_chart: ChartData) -> None:
        ctx = build_lordship_context(manish_chart.lagna_sign)
        svg = render_d1_svg(manish_chart, ctx)
        assert 'viewBox="0 0 500 500"' in svg

    def test_svg_has_lagna_marker(self, manish_chart: ChartData) -> None:
        ctx = build_lordship_context(manish_chart.lagna_sign)
        svg = render_d1_svg(manish_chart, ctx)
        assert "लग्न" in svg

    def test_svg_has_color_coding(self, manish_chart: ChartData) -> None:
        """Benefic/malefic/yogakaraka planets should have different colors."""
        ctx = build_lordship_context(manish_chart.lagna_sign)
        svg = render_d1_svg(manish_chart, ctx)
        # At least green (benefic) and red (malefic) should appear
        assert "#2E7D32" in svg  # green
        assert "#C62828" in svg  # red

    def test_svg_has_retrograde_marker(self, manish_chart: ChartData) -> None:
        """If any planet is retrograde, the marker should appear."""
        ctx = build_lordship_context(manish_chart.lagna_sign)
        svg = render_d1_svg(manish_chart, ctx)
        has_retro = any(p.is_retrograde for p in manish_chart.planets.values())
        if has_retro:
            assert "वक्री" in svg

    def test_svg_has_house_labels(self, manish_chart: ChartData) -> None:
        ctx = build_lordship_context(manish_chart.lagna_sign)
        svg = render_d1_svg(manish_chart, ctx)
        # Check that at least some house labels appear
        assert "तनु" in svg  # House 1
        assert "कर्म" in svg  # House 10

    def test_svg_has_diamond_structure(self, manish_chart: ChartData) -> None:
        ctx = build_lordship_context(manish_chart.lagna_sign)
        svg = render_d1_svg(manish_chart, ctx)
        assert "<polygon" in svg
        assert "<line" in svg


class TestRenderDivisionalSvg:
    def test_divisional_returns_svg(self, manish_chart: ChartData) -> None:
        from daivai_engine.compute.divisional import compute_navamsha

        ctx = build_lordship_context(manish_chart.lagna_sign)
        d9 = compute_navamsha(manish_chart)
        svg = render_divisional_svg(manish_chart, d9, "D9 नवमांश", ctx)
        assert isinstance(svg, str)
        assert "<svg" in svg
        assert "D9" in svg

    def test_divisional_has_planets(self, manish_chart: ChartData) -> None:
        from daivai_engine.compute.divisional import compute_navamsha

        ctx = build_lordship_context(manish_chart.lagna_sign)
        d9 = compute_navamsha(manish_chart)
        svg = render_divisional_svg(manish_chart, d9, "D9 नवमांश", ctx)
        # Should contain at least some planet abbreviations
        found = sum(1 for abbr in ["सू", "चं", "गु"] if abbr in svg)
        assert found >= 2
