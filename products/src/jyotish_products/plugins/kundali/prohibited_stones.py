"""Prohibited stones page renderer — full danger list with alternatives.

Renders a full page of prohibited gemstones for this lagna with:
- Stone name + planet + house lordship + one-line reason
- Free alternatives (mantra, daan, color)
- Honest disclaimer about gemstone industry
"""
from __future__ import annotations

from typing import Any

from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from jyotish_products.plugins.kundali.theme import (
    DEEP_RED,
    INDIGO,
    LIGHT_SAFFRON,
    TEXT_DARK,
    TEXT_LIGHT,
    register_fonts,
)


def render_prohibited_stones(
    results: list[Any],
    lagna_sign: str,
) -> list[Any]:
    """Render prohibited stones page as ReportLab flowables.

    Args:
        results: GemstoneWeightResult list (accessed by attribute, no plugin import).
        lagna_sign: Lagna sign name for display.

    Returns:
        List of ReportLab flowable elements.
    """
    register_fonts()
    font = _get_font()
    elements: list[Any] = []

    heading = _style(font, 14, INDIGO, sa=8, sb=12)
    body = _style(font, 10, TEXT_DARK, sa=4)
    small = _style(font, 8, TEXT_LIGHT, sa=2)
    warn = _style(font, 10, DEEP_RED, sa=4)

    elements.append(Paragraph(
        f"निषिद्ध रत्न — Prohibited Stones ({lagna_sign} Lagna)", heading,
    ))

    prohibited = [r for r in results if r.status == "prohibited"]
    if not prohibited:
        elements.append(Paragraph("No prohibited stones for this lagna.", body))
        return elements

    # Prohibition table
    data = [["रत्न / Stone", "ग्रह / Planet", "कारण / Reason"]]
    for r in prohibited:
        reason = r.prohibition_reason or "Functional malefic for this lagna"
        data.append([
            f"{r.stone_name} ({r.stone_name_hi})",
            r.planet,
            reason[:100],
        ])

    t = Table(data, colWidths=[5 * cm, 3 * cm, 9 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DEEP_RED),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_SAFFRON]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.4 * cm))

    # Free alternatives
    elements.append(Paragraph("मुफ्त विकल्प — Free Alternatives", heading))
    elements.append(Paragraph(
        "इन ग्रहों के लिए रत्न न पहनें। इसके बजाय:", body,
    ))

    for r in prohibited:
        alt = r.free_alternatives
        if not alt:
            continue
        mantra = alt.get("mantra", "—")
        daan = alt.get("daan", "—")
        color_alt = alt.get("color", "—")
        elements.append(Paragraph(
            f"<b>{r.planet}:</b> Mantra: {mantra} | Daan: {daan} | Color: {color_alt}",
            body,
        ))

    elements.append(Spacer(1, 0.5 * cm))

    # Industry disclaimer
    elements.append(Paragraph(
        "कोई भी वेबसाइट यह सूची नहीं दिखाती। वे रत्न बेचते हैं।",
        warn,
    ))
    elements.append(Paragraph(
        "No gemstone website shows this list. They sell stones. "
        "This tool shows what is actually safe for YOUR lagna based on "
        "Parashari lordship rules from Brihat Parashara Hora Shastra.",
        small,
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
        f"PS_{size}_{id(color)}_{sa}", fontName=font, fontSize=size,
        textColor=color, spaceAfter=sa, spaceBefore=sb,
    )
