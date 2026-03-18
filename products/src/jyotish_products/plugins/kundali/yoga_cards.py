"""Yoga card renderer — active yogas as styled ReportLab flowable cards.

Takes pre-computed YogaResult objects and renders present yogas as
visually styled cards with Hindi + English labels, classification icons,
and forming planet/house details. Maximum 7 cards shown.
"""

from __future__ import annotations

from typing import Any

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from jyotish_engine.models.yoga import YogaResult
from jyotish_products.plugins.kundali.theme import (
    DEEP_GREEN,
    DEEP_RED,
    GOLD,
    INDIGO,
    LIGHT_SAFFRON,
    TEXT_DARK,
    register_fonts,
)


_MAX_CARDS = 7
_DESC_TRUNCATE = 120

# Effect → (border color, label Hindi, label English)
_EFFECT_MAP: dict[str, tuple[Any, str, str]] = {
    "benefic": (DEEP_GREEN, "\u0936\u0941\u092d", "Benefic"),
    "malefic": (DEEP_RED, "\u0905\u0936\u0941\u092d", "Malefic"),
    "mixed": (GOLD, "\u092e\u093f\u0936\u094d\u0930", "Mixed"),
}


def render_yoga_cards(yogas: list[YogaResult]) -> list[Any]:
    """Render active yogas as styled card flowables.

    Args:
        yogas: Pre-computed yoga detection results.

    Returns:
        List of ReportLab flowable elements (heading + cards).
        Empty list if no yogas are present.
    """
    register_fonts()
    font = _get_font()

    present = [y for y in yogas if y.is_present]
    if not present:
        return _empty_section(font)

    # Limit to most significant cards
    display = present[:_MAX_CARDS]

    elements: list[Any] = [_heading(font)]

    for yoga in display:
        card = _build_card(yoga, font)
        elements.append(card)
        elements.append(Spacer(1, 0.2 * cm))

    return elements


def _heading(font: str) -> Paragraph:
    """Section heading for yoga cards."""
    style = ParagraphStyle(
        "YogaHeading",
        fontName=font,
        fontSize=14,
        textColor=INDIGO,
        spaceAfter=8,
        spaceBefore=12,
    )
    return Paragraph(
        "\u092f\u094b\u0917 \u0935\u093f\u0936\u094d\u0932\u0947\u0937\u0923 \u2014 Yoga Analysis",
        style,
    )


def _empty_section(font: str) -> list[Any]:
    """Return heading + 'no yogas' message when none are present."""
    body_style = ParagraphStyle(
        "YogaEmpty",
        fontName=font,
        fontSize=10,
        textColor=TEXT_DARK,
        spaceAfter=6,
    )
    return [
        _heading(font),
        Paragraph("No significant yogas detected in this chart.", body_style),
    ]


def _build_card(yoga: YogaResult, font: str) -> Table:
    """Build a single yoga card as a ReportLab Table with colored left border.

    Layout (single row, two columns):
      [color strip] | [card content paragraph]
    """
    border_color, effect_hi, effect_en = _EFFECT_MAP.get(
        yoga.effect,
        (GOLD, "\u092e\u093f\u0936\u094d\u0930", "Mixed"),
    )

    # Card content as styled HTML paragraph
    content_parts = [
        f"<b>{yoga.name_hindi}</b>  <i>({yoga.name})</i>",
        f'<br/><font size="8" color="#757575">'
        f"{_effect_badge(effect_hi, effect_en)}"
        f" | {_planets_label(yoga.planets_involved)}"
        f" | {_houses_label(yoga.houses_involved)}"
        f"</font>",
        f'<br/><font size="9">{_truncate(yoga.description)}</font>',
    ]

    content_style = ParagraphStyle(
        "YogaCardContent",
        fontName=font,
        fontSize=10,
        textColor=TEXT_DARK,
        leading=14,
        spaceAfter=2,
    )
    content_para = Paragraph("".join(content_parts), content_style)

    # Color strip cell (narrow column) + content cell
    data = [["", content_para]]
    col_widths = [0.25 * cm, 16.75 * cm]
    table = Table(data, colWidths=col_widths)
    table.setStyle(_card_style(border_color, font))

    return table


def _card_style(border_color: Any, font: str) -> TableStyle:
    """TableStyle for a single yoga card."""
    return TableStyle(
        [
            # Left color strip
            ("BACKGROUND", (0, 0), (0, -1), border_color),
            # Card background
            ("BACKGROUND", (1, 0), (-1, -1), LIGHT_SAFFRON),
            # Font
            ("FONTNAME", (0, 0), (-1, -1), font),
            # Padding
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (1, 0), (1, -1), 8),
            ("RIGHTPADDING", (1, 0), (1, -1), 8),
            ("LEFTPADDING", (0, 0), (0, -1), 0),
            ("RIGHTPADDING", (0, 0), (0, -1), 0),
            # Alignment
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            # Subtle border
            ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            # Round appearance via grid removal on strip
            ("LINEAFTER", (0, 0), (0, -1), 0, colors.white),
        ]
    )


def _effect_badge(effect_hi: str, effect_en: str) -> str:
    """Format the effect classification badge."""
    return f"{effect_hi} ({effect_en})"


def _planets_label(planets: list[str]) -> str:
    """Format involved planets."""
    if not planets:
        return ""
    return "Planets: " + ", ".join(planets)


def _houses_label(houses: list[int]) -> str:
    """Format involved houses."""
    if not houses:
        return ""
    return "Houses: " + ", ".join(str(h) for h in houses)


def _truncate(text: str) -> str:
    """Truncate description to max length."""
    if len(text) <= _DESC_TRUNCATE:
        return text
    return text[: _DESC_TRUNCATE - 3] + "..."


def _get_font() -> str:
    """Return available font name."""
    try:
        from reportlab.pdfbase.pdfmetrics import getFont

        getFont("NotoDevanagari")
        return "NotoDevanagari"
    except KeyError:
        return "Helvetica"
