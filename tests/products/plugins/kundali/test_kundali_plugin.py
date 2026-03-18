"""Tests for the kundali report plugin."""
from __future__ import annotations

import pytest

from jyotish_engine.compute.chart import compute_chart
from jyotish_engine.models.chart import ChartData
from jyotish_products.plugins.kundali.diamond_text import render_chart_summary, render_diamond_text
from jyotish_products.plugins.kundali.report import REPORT_SECTIONS, generate_report


@pytest.fixture
def manish_chart() -> ChartData:
    return compute_chart(
        name="Manish Chaurasia", dob="13/03/1989", tob="12:17",
        lat=25.3176, lon=83.0067, tz_name="Asia/Kolkata", gender="Male",
    )


class TestDiamondChart:
    def test_renders_text(self, manish_chart: ChartData) -> None:
        result = render_diamond_text(manish_chart)
        assert isinstance(result, str)
        assert "Manish" in result
        assert "Mithuna" in result

    def test_chart_summary_has_planets(self, manish_chart: ChartData) -> None:
        result = render_chart_summary(manish_chart)
        assert "Sun" in result
        assert "Moon" in result
        assert "Jupiter" in result


class TestKundaliReport:
    def test_full_report_has_content(self, manish_chart: ChartData) -> None:
        report = generate_report(manish_chart)
        assert len(report) > 500
        assert "Mithuna" in report

    def test_report_has_18_sections(self) -> None:
        assert len(REPORT_SECTIONS) == 18

    def test_gemstone_section_shows_safety(self, manish_chart: ChartData) -> None:
        report = generate_report(manish_chart, sections=["gemstones"])
        assert "RECOMMENDED" in report or "recommended" in report.lower()
        assert "PROHIBITED" in report or "prohibited" in report.lower()

    def test_yogas_section(self, manish_chart: ChartData) -> None:
        report = generate_report(manish_chart, sections=["yogas"])
        assert "Gajakesari" in report or "yoga" in report.lower()

    def test_dasha_section(self, manish_chart: ChartData) -> None:
        report = generate_report(manish_chart, sections=["mahadasha_timeline"])
        assert "Jupiter" in report
        assert "CURRENT" in report

    def test_house_lords_section(self, manish_chart: ChartData) -> None:
        report = generate_report(manish_chart, sections=["house_lords"])
        assert "House" in report
        assert "Mercury" in report  # Lagnesh
