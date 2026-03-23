"""Tests for HTML generation and PDF generation with fallback."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from daivai_engine.compute.chart import compute_chart
from daivai_engine.models.chart import ChartData
from daivai_products.plugins.kundali.pdf import generate_html, generate_pdf


class TestGenerateHtml:
    def test_html_returns_string(self, manish_chart: ChartData) -> None:
        html = generate_html(manish_chart)
        assert isinstance(html, str)
        assert len(html) > 1000

    def test_html_is_valid_document(self, manish_chart: ChartData) -> None:
        html = generate_html(manish_chart)
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
        assert "<head>" in html
        assert "<body>" in html

    def test_html_contains_chart_name(self, manish_chart: ChartData) -> None:
        html = generate_html(manish_chart)
        assert "Manish Chaurasia" in html

    def test_html_contains_om(self, manish_chart: ChartData) -> None:
        html = generate_html(manish_chart)
        assert "ॐ" in html

    def test_html_contains_svg_chart(self, manish_chart: ChartData) -> None:
        html = generate_html(manish_chart)
        assert "<svg" in html
        assert "viewBox" in html

    def test_html_contains_planet_table(self, manish_chart: ChartData) -> None:
        html = generate_html(manish_chart)
        assert "ग्रह स्थिति" in html
        assert "सू" in html  # Sun
        assert "चं" in html  # Moon

    def test_html_contains_dasha_section(self, manish_chart: ChartData) -> None:
        html = generate_html(manish_chart)
        assert "विमशोत्तरी दशा" in html

    def test_html_contains_ashtakavarga(self, manish_chart: ChartData) -> None:
        html = generate_html(manish_chart)
        assert "अष्टकवर्ग" in html

    def test_html_contains_yogas(self, manish_chart: ChartData) -> None:
        html = generate_html(manish_chart)
        assert "योग" in html

    def test_html_contains_gemstones(self, manish_chart: ChartData) -> None:
        html = generate_html(manish_chart)
        assert "रत्न" in html

    def test_html_contains_certificate(self, manish_chart: ChartData) -> None:
        html = generate_html(manish_chart)
        assert "गणना प्रमाणपत्र" in html
        assert "Swiss Ephemeris" in html

    def test_html_summary_format(self, manish_chart: ChartData) -> None:
        html = generate_html(manish_chart, fmt="summary")
        assert "<!DOCTYPE html>" in html
        # Summary should NOT have graha table section
        assert "ग्रह स्थिति" not in html

    def test_html_standalone_has_font_embed(self, manish_chart: ChartData) -> None:
        html = generate_html(manish_chart, standalone=True)
        # Should have @font-face (even if font not found, the style block should be there)
        assert "@font-face" in html

    def test_html_different_chart(self) -> None:
        chart = compute_chart(
            name="Test Person",
            dob="01/01/2000",
            tob="06:00",
            lat=28.6139,
            lon=77.2090,
            tz_name="Asia/Kolkata",
            gender="Female",
        )
        html = generate_html(chart, fmt="detailed")
        assert "Test Person" in html
        assert "<svg" in html


class TestGeneratePdf:
    def test_pdf_returns_bytes(self, manish_chart: ChartData) -> None:
        """PDF generation should work (via either WeasyPrint or ReportLab)."""
        result = generate_pdf(manish_chart, fmt="detailed")
        assert result is not None
        assert result[:5] == b"%PDF-"

    def test_pdf_saves_to_file(self, manish_chart: ChartData) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.pdf"
            generate_pdf(manish_chart, output_path=str(path), fmt="detailed")
            assert path.exists()
            assert path.stat().st_size > 5000

    def test_pdf_summary_format(self, manish_chart: ChartData) -> None:
        result = generate_pdf(manish_chart, fmt="summary")
        assert result is not None
        assert result[:5] == b"%PDF-"


class TestReportLabFallback:
    def test_fallback_works_when_weasyprint_missing(self, manish_chart: ChartData) -> None:
        """When WeasyPrint import fails, should fall back to ReportLab."""
        with patch(
            "daivai_products.plugins.kundali.pdf._generate_weasyprint",
            side_effect=ImportError("weasyprint not installed"),
        ):
            result = generate_pdf(manish_chart, fmt="detailed")
            assert result is not None
            assert result[:5] == b"%PDF-"

    def test_fallback_on_weasyprint_error(self, manish_chart: ChartData) -> None:
        """When WeasyPrint raises any error, should fall back to ReportLab."""
        with patch(
            "daivai_products.plugins.kundali.pdf._generate_weasyprint",
            side_effect=RuntimeError("something broke"),
        ):
            result = generate_pdf(manish_chart, fmt="detailed")
            assert result is not None
            assert result[:5] == b"%PDF-"
