"""Gemstone recommendation card renderer — PDF flowables for kundali report.

Renders multi-factor gemstone weight results as ReportLab flowable elements.
Shows recommended stones with ratti, prohibited stones with reasons,
free alternatives, and an honesty disclaimer.

IMPORTANT: This renderer does NOT import from plugins/remedies/.
It receives pre-computed data and accesses fields by attribute name.
"""

from __future__ import annotations

from typing import Any

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from jyotish_products.plugins.kundali.theme import (
    DEEP_GREEN,
    DEEP_RED,
    GOLD,
    INDIGO,
    LIGHT_SAFFRON,
    SAFFRON,
    TEXT_DARK,
    TEXT_LIGHT,
    register_fonts,
)


def render_gemstone_card(results: list[Any]) -> list[Any]:
    """Render gemstone recommendations as ReportLab flowable elements.

    Args:
        results: List of GemstoneWeightResult objects (from remedies plugin).
            Each has: .planet, .stone_name, .stone_name_hi, .status,
            .base_ratti, .recommended_ratti, .factors, .website_comparisons,
            .pros_cons, .free_alternatives, .prohibition_reason

    Returns:
        List of ReportLab flowable elements for PDF composition.
    """
    register_fonts()
    font = _get_font()
    styles = _card_styles(font)

    elements: list[Any] = []
    elements.append(
        Paragraph(
            "रत्न सुझाव — Gemstone Recommendations",
            styles["heading"],
        )
    )
    elements.append(Spacer(1, 0.3 * cm))

    recommended = [r for r in results if r.status == "recommended"]
    caution = [r for r in results if r.status == "test_with_caution"]
    prohibited = [r for r in results if r.status == "prohibited"]

    # Section 1: Recommended stones
    if recommended or caution:
        elements.append(Paragraph("Recommended Stones", styles["section"]))
        elements.append(Spacer(1, 0.15 * cm))
        for r in recommended:
            elements.extend(_recommended_block(r, styles))
        for r in caution:
            elements.extend(_recommended_block(r, styles))

    # Section 2: Prohibited stones
    if prohibited:
        elements.append(Spacer(1, 0.2 * cm))
        elements.append(Paragraph("Prohibited Stones", styles["section_red"]))
        elements.append(Spacer(1, 0.15 * cm))
        elements.extend(_prohibited_table(prohibited, styles, font))

    # Section 3: Free alternatives
    alt_stones = recommended + caution
    if alt_stones:
        elements.append(Spacer(1, 0.2 * cm))
        elements.append(
            Paragraph(
                "Free Alternatives (Mantra / Daan / Color)",
                styles["section"],
            )
        )
        elements.append(Spacer(1, 0.15 * cm))
        elements.extend(_free_alternatives_table(alt_stones, styles, font))

    # Section 4: Honesty note
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(
        Paragraph(
            "No shastra prescribes exact weight — these are computed estimates "
            "based on 10 chart factors. Consult your pandit ji before wearing.",
            styles["disclaimer"],
        )
    )
    elements.append(Spacer(1, 0.3 * cm))

    return elements


# ── Recommended stone block ─────────────────────────────────────────────


def _recommended_block(result: Any, styles: dict[str, ParagraphStyle]) -> list[Any]:
    """Build flowables for one recommended/caution stone."""
    elements: list[Any] = []

    status_label = "RECOMMENDED" if result.status == "recommended" else "TEST WITH CAUTION"
    stone_line = (
        f"<b>{result.stone_name_hi} ({result.stone_name})</b> — {result.planet} | {status_label}"
    )
    elements.append(Paragraph(stone_line, styles["stone_name"]))

    # Weight line with key factors
    top_factors = _top_factors(result.factors, limit=3)
    factor_text = ", ".join(f"{f.name}: {f.raw_value}" for f in top_factors)
    weight_line = (
        f"Recommended: <b>{result.recommended_ratti:.2f} ratti</b> (base: {result.base_ratti:.1f}r)"
    )
    if factor_text:
        weight_line += f" | Key factors: {factor_text}"
    elements.append(Paragraph(weight_line, styles["body"]))

    # Website comparison
    comparisons = getattr(result, "website_comparisons", {})
    if comparisons:
        avg_website = sum(comparisons.values()) / len(comparisons)
        comp_line = (
            f"Our engine: {result.recommended_ratti:.1f} ratti "
            f"vs Avg website: {avg_website:.1f} ratti"
        )
        elements.append(Paragraph(comp_line, styles["comparison"]))

    elements.append(Spacer(1, 0.15 * cm))
    return elements


# ── Prohibited stones table ─────────────────────────────────────────────


def _prohibited_table(
    prohibited: list[Any],
    styles: dict[str, ParagraphStyle],
    font: str,
) -> list[Any]:
    """Build a table of prohibited stones with X marker and reason."""
    data: list[list[str]] = []
    for r in prohibited:
        reason = r.prohibition_reason or f"{r.planet} stone prohibited for this lagna"
        data.append(
            [
                "X",
                f"{r.stone_name_hi} ({r.stone_name})",
                r.planet,
                reason[:80],
            ]
        )

    if not data:
        return []

    table = Table(data, colWidths=[0.6 * cm, 4 * cm, 2 * cm, 9 * cm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TEXTCOLOR", (0, 0), (0, -1), DEEP_RED),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (1, 0), (1, -1), TEXT_DARK),
                ("TEXTCOLOR", (3, 0), (3, -1), TEXT_LIGHT),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.lightgrey),
            ]
        )
    )

    return [table, Spacer(1, 0.15 * cm)]


# ── Free alternatives table ─────────────────────────────────────────────


def _free_alternatives_table(
    stones: list[Any],
    styles: dict[str, ParagraphStyle],
    font: str,
) -> list[Any]:
    """Build a table of free alternatives (mantra, daan, color) per planet."""
    header = ["Planet", "Mantra", "Daan", "Color"]
    data: list[list[str]] = [header]

    for r in stones:
        alts = getattr(r, "free_alternatives", {})
        if not alts:
            continue
        data.append(
            [
                r.planet,
                alts.get("mantra", "—"),
                alts.get("daan", "—"),
                alts.get("color", "—"),
            ]
        )

    if len(data) <= 1:
        return []

    col_widths = [2 * cm, 5.5 * cm, 5 * cm, 3 * cm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), SAFFRON),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, -1), 7),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_SAFFRON]),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    return [table, Spacer(1, 0.15 * cm)]


# ── Helpers ─────────────────────────────────────────────────────────────


def _top_factors(factors: list[Any], *, limit: int = 3) -> list[Any]:
    """Return the most impactful factors (furthest from 1.0 multiplier)."""
    scored = sorted(factors, key=lambda f: abs(f.multiplier - 1.0), reverse=True)
    return scored[:limit]


def _get_font() -> str:
    """Return the best available font name."""
    try:
        from reportlab.pdfbase.pdfmetrics import getFont

        getFont("NotoDevanagari")
        return "NotoDevanagari"
    except KeyError:
        return "Helvetica"


def _card_styles(font: str) -> dict[str, ParagraphStyle]:
    """Create paragraph styles for the gemstone card."""
    ps = ParagraphStyle
    return {
        "heading": ps(
            "GemH", fontName=font, fontSize=14, textColor=INDIGO, spaceAfter=6, spaceBefore=10
        ),
        "section": ps(
            "GemS", fontName=font, fontSize=11, textColor=DEEP_GREEN, spaceAfter=4, spaceBefore=6
        ),
        "section_red": ps(
            "GemSR", fontName=font, fontSize=11, textColor=DEEP_RED, spaceAfter=4, spaceBefore=6
        ),
        "stone_name": ps(
            "GemSN", fontName=font, fontSize=10, textColor=GOLD, spaceAfter=2, leading=14
        ),
        "body": ps(
            "GemB", fontName=font, fontSize=9, textColor=TEXT_DARK, spaceAfter=2, leading=12
        ),
        "comparison": ps(
            "GemC", fontName=font, fontSize=8, textColor=TEXT_LIGHT, spaceAfter=2, leading=10
        ),
        "disclaimer": ps(
            "GemD",
            fontName=font,
            fontSize=8,
            textColor=TEXT_LIGHT,
            spaceAfter=4,
            leading=11,
            borderColor=SAFFRON,
            borderWidth=0.5,
            borderPadding=6,
        ),
    }
