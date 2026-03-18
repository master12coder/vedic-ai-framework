"""Golden period highlight renderer — best upcoming dasha period.

Identifies the most favorable dasha period in the next 10-20 years based on
functional benefic status and generates a highlighted card for the PDF.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from jyotish_engine.models.chart import ChartData
from jyotish_engine.models.dasha import DashaPeriod
from jyotish_products.plugins.kundali.theme import (
    DEEP_GREEN,
    GOLD,
    INDIGO,
    LIGHT_SAFFRON,
    PLANET_HI,
    TEXT_DARK,
    register_fonts,
)


def render_golden_period(
    chart: ChartData,
    mahadashas: list[DashaPeriod],
    lordship_ctx: dict[str, Any],
) -> list[Any]:
    """Render the golden period highlight card as ReportLab flowables.

    Finds the best upcoming MD/AD period based on functional benefic planets.

    Args:
        chart: Birth chart for metadata.
        mahadashas: All 9 Mahadasha periods.
        lordship_ctx: Lordship context for benefic classification.

    Returns:
        List of ReportLab flowable elements.
    """
    register_fonts()
    font = _get_font()

    benefics = {e["planet"] for e in lordship_ctx.get("functional_benefics", [])}
    yk = lordship_ctx.get("yogakaraka", {})
    yogakaraka = yk.get("planet", "") if isinstance(yk, dict) else ""

    # Find best upcoming period
    now = datetime.now(tz=mahadashas[0].start.tzinfo) if mahadashas else datetime.now()
    golden = _find_golden_period(mahadashas, benefics, yogakaraka, now)

    heading_style = _make_style(font, 14, INDIGO, space_after=8, space_before=12)
    elements: list[Any] = [
        Paragraph("स्वर्ण काल — Golden Period", heading_style),
    ]

    if golden is None:
        elements.append(Paragraph(
            "No strongly benefic period found in the next 20 years. "
            "Focus on remedies and mantra practice.",
            _make_style(font, 10, TEXT_DARK),
        ))
        return elements

    lord_hi = PLANET_HI.get(golden.lord, golden.lord)
    start = golden.start.strftime("%b %Y")
    end = golden.end.strftime("%b %Y")

    # Golden card table
    card_data = [
        [f"आपका स्वर्ण काल: {lord_hi} ({golden.lord}) महादशा"],
        [f"{start} — {end}"],
        [_period_advice(golden.lord, yogakaraka)],
    ]

    card = Table(card_data, colWidths=[15 * cm])
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_SAFFRON),
        ("BOX", (0, 0), (-1, -1), 2, GOLD),
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTSIZE", (0, 0), (0, 0), 13),
        ("FONTSIZE", (0, 1), (0, 1), 11),
        ("FONTSIZE", (0, 2), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, 0), INDIGO),
        ("TEXTCOLOR", (0, 1), (0, 1), DEEP_GREEN),
        ("TEXTCOLOR", (0, 2), (-1, -1), TEXT_DARK),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(card)
    elements.append(Spacer(1, 0.3 * cm))

    return elements


def _find_golden_period(
    mahadashas: list[DashaPeriod],
    benefics: set[str],
    yogakaraka: str,
    now: datetime,
) -> DashaPeriod | None:
    """Find the best benefic MD starting within 20 years from now."""
    candidates: list[tuple[int, DashaPeriod]] = []
    cutoff = now.replace(year=now.year + 20)

    for md in mahadashas:
        if md.end < now:
            continue
        if md.start > cutoff:
            break
        score = 0
        if md.lord == yogakaraka:
            score = 3
        elif md.lord in benefics:
            score = 2
        if score > 0:
            candidates.append((score, md))

    if not candidates:
        return None
    candidates.sort(key=lambda x: (-x[0], x[1].start))
    return candidates[0][1]


def _period_advice(lord: str, yogakaraka: str) -> str:
    """Generate brief advice for the golden period."""
    if lord == yogakaraka:
        return ("योगकारक ग्रह की दशा — career growth, spiritual progress, "
                "and material gains are all favorable. Start long-term projects now.")
    return ("शुभ दशा — favorable for education, relationships, and health. "
            "Strengthen this planet with its gemstone and mantra.")


def _get_font() -> str:
    """Return available font name."""
    try:
        from reportlab.pdfbase.pdfmetrics import getFont
        getFont("NotoDevanagari")
        return "NotoDevanagari"
    except KeyError:
        return "Helvetica"


def _make_style(font: str, size: int, color: Any, space_after: int = 4,
                space_before: int = 0) -> Any:
    """Create a simple ParagraphStyle."""
    from reportlab.lib.styles import ParagraphStyle
    return ParagraphStyle(
        f"GP_{size}_{id(color)}", fontName=font, fontSize=size,
        textColor=color, spaceAfter=space_after, spaceBefore=space_before,
    )
