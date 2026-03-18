"""Computation certificate renderer — last page of the PDF.

Shows computation metadata, cross-verification note, and disclaimer.
"""
from __future__ import annotations

from typing import Any

from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from jyotish_engine.models.chart import ChartData
from jyotish_products.plugins.kundali.theme import (
    DEEP_GREEN,
    INDIGO,
    LIGHT_SAFFRON,
    SAFFRON,
    TEXT_DARK,
    TEXT_LIGHT,
    register_fonts,
)


def render_accuracy_cert(chart: ChartData) -> list[Any]:
    """Render computation certificate as ReportLab flowables.

    Args:
        chart: Computed birth chart (for ayanamsha, coordinates, etc.).

    Returns:
        List of ReportLab flowable elements.
    """
    register_fonts()
    font = _get_font()
    elements: list[Any] = []

    heading = _style(font, 14, INDIGO, sa=8, sb=12)
    body = _style(font, 10, TEXT_DARK, sa=4)
    small = _style(font, 9, TEXT_LIGHT, sa=2)
    green = _style(font, 10, DEEP_GREEN, sa=4)

    elements.append(Paragraph("गणना प्रमाणपत्र — Computation Certificate", heading))

    # Metadata table
    data = [
        ["Parameter", "Value"],
        ["Ephemeris", "Swiss Ephemeris (NASA JPL DE431)"],
        ["Ayanamsha", f"Lahiri (Chitrapaksha) — {chart.ayanamsha:.4f}°"],
        ["Coordinates", f"{chart.latitude:.4f}°N, {chart.longitude:.4f}°E"],
        ["Timezone", chart.timezone_name],
        ["Julian Day", f"{chart.julian_day:.6f}"],
        ["House System", "Whole Sign (Rashi-based)"],
        ["Dasha System", "Vimshottari (120-year cycle)"],
        ["Computation", "Sidereal (not Tropical)"],
    ]

    t = Table(data, colWidths=[5 * cm, 12 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SAFFRON),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_SAFFRON]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.4 * cm))

    # Cross-verification
    elements.append(Paragraph("Cross-verification", heading))
    elements.append(Paragraph(
        "Planet longitudes can be verified against DrikPanchang.com or "
        "any Swiss Ephemeris-based software using Lahiri ayanamsha.",
        green,
    ))

    elements.append(Spacer(1, 0.4 * cm))

    # Disclaimer
    elements.append(Paragraph("अस्वीकरण — Disclaimer", heading))
    elements.append(Paragraph(
        "यह computational tool है, Pandit Ji का विकल्प नहीं।",
        body,
    ))
    elements.append(Paragraph(
        "This is a computational tool, not a replacement for an experienced "
        "astrologer. Jyotish is a complex vidya that requires human wisdom "
        "beyond mathematical computation. Use this report as a starting point "
        "for discussion with your Pandit Ji, not as a final answer.",
        small,
    ))
    elements.append(Spacer(1, 0.3 * cm))

    # GitHub
    elements.append(Paragraph(
        "Open source: github.com/vedic-ai-framework",
        _style(font, 8, TEXT_LIGHT, sa=2),
    ))

    return elements


def _get_font() -> str:
    try:
        from reportlab.pdfbase.pdfmetrics import getFont
        getFont("NotoDevanagari")
        return "NotoDevanagari"
    except KeyError:
        return "Helvetica"


def _style(font: str, size: int, color: Any, sa: int = 4, sb: int = 0) -> Any:
    from reportlab.lib.styles import ParagraphStyle
    return ParagraphStyle(
        f"AC_{size}_{id(color)}_{sa}", fontName=font, fontSize=size,
        textColor=color, spaceAfter=sa, spaceBefore=sb,
    )
