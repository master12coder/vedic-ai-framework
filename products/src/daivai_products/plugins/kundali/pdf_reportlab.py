"""ReportLab PDF fallback — legacy assembler extracted from pdf.py.

Generates a kundali PDF using ReportLab + matplotlib PNG charts.
Used as fallback when WeasyPrint is not installed.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer

from daivai_engine.compute.ashtakavarga import compute_ashtakavarga
from daivai_engine.compute.dasha import (
    compute_antardashas,
    compute_mahadashas,
    find_current_dasha,
)
from daivai_engine.compute.divisional import compute_dasamsha, compute_navamsha
from daivai_engine.compute.strength import compute_shadbala
from daivai_engine.compute.yoga import detect_all_yogas
from daivai_engine.models.chart import ChartData
from daivai_products.interpret.context import build_lordship_context
from daivai_products.plugins.kundali.theme import (
    pdf_styles,
    register_fonts,
)


logger = logging.getLogger(__name__)


def generate_pdf_reportlab(
    chart: ChartData,
    output_path: str | Path | None = None,
    fmt: str = "detailed",
    body_weight_kg: float = 0,
    chart_image_bytes: bytes | None = None,
    gemstone_results: list[Any] | None = None,
) -> bytes | None:
    """Generate a kundali PDF using ReportLab (legacy fallback).

    Args:
        chart: Computed birth chart.
        output_path: Save path or None for bytes.
        fmt: 'summary', 'detailed', or 'pandit'.
        body_weight_kg: Unused (kept for backward compat).
        chart_image_bytes: Legacy: pre-rendered chart PNG.
        gemstone_results: Pre-computed gemstone weight results.

    Returns:
        PDF bytes if output_path is None, else None.
    """
    register_fonts()
    st = pdf_styles()

    # ── Compute all data ──
    ctx = build_lordship_context(chart.lagna_sign)
    mahadashas = compute_mahadashas(chart)
    md, ad, _pd = find_current_dasha(chart)
    antardashas = compute_antardashas(md)
    yogas = detect_all_yogas(chart)
    shadbala = compute_shadbala(chart)
    ashtakavarga = compute_ashtakavarga(chart)
    navamsha = compute_navamsha(chart)

    if gemstone_results is None:
        gemstone_results = []

    # ── Build story ──
    story: list[Any] = []

    # Title page (all formats)
    story.extend(_title_page(chart, md, ad, st))
    story.append(PageBreak())

    # D1 chart
    d1_bytes = _render_d1(chart, ctx)
    if d1_bytes:
        story.append(_embed_image(d1_bytes, 5.5 * inch))
    story.append(PageBreak())

    if fmt in ("detailed", "pandit"):
        d9_bytes = _render_divisional(chart, navamsha, "D9 Navamsha", "नवमांश")
        if d9_bytes:
            story.append(_embed_image(d9_bytes, 5.5 * inch))
        story.append(PageBreak())

    if fmt == "pandit":
        dasamsha = compute_dasamsha(chart)
        d10_bytes = _render_divisional(chart, dasamsha, "D10 Dasamsha", "दशमांश")
        if d10_bytes:
            story.append(_embed_image(d10_bytes, 5.5 * inch))
        story.append(PageBreak())

    if fmt in ("detailed", "pandit"):
        from daivai_products.plugins.kundali.graha_table import render_graha_table

        story.extend(render_graha_table(chart, shadbala, ctx))
        story.append(PageBreak())

        dasha_bytes = _render_dasha(chart, mahadashas, md, ad, antardashas, ctx)
        if dasha_bytes:
            story.append(_embed_image(dasha_bytes, 6.5 * inch))
        story.append(PageBreak())

        avk_bytes = _render_avk(chart, ashtakavarga)
        if avk_bytes:
            story.append(_embed_image(avk_bytes, 6 * inch))
        story.append(PageBreak())

    from daivai_products.plugins.kundali.yoga_cards import render_yoga_cards

    story.extend(render_yoga_cards(yogas))
    story.append(PageBreak())

    if fmt in ("detailed", "pandit"):
        sb_bytes = _render_shadbala(chart, shadbala)
        if sb_bytes:
            story.append(_embed_image(sb_bytes, 5.5 * inch))
        story.append(PageBreak())

        from daivai_products.plugins.kundali.golden_period import render_golden_period

        story.extend(render_golden_period(chart, mahadashas, ctx))

    if gemstone_results:
        from daivai_products.plugins.kundali.gemstone_card import render_gemstone_card

        story.extend(render_gemstone_card(gemstone_results))
        story.append(PageBreak())

        from daivai_products.plugins.kundali.prohibited_stones import (
            render_prohibited_stones,
        )

        story.extend(render_prohibited_stones(gemstone_results, chart.lagna_sign))
        story.append(PageBreak())

    from daivai_products.plugins.kundali.accuracy_cert import render_accuracy_cert

    story.extend(render_accuracy_cert(chart))

    return _build_pdf(story, output_path)


# ── Page builders ────────────────────────────────────────────────────────


def _title_page(chart: ChartData, md: Any, ad: Any, st: dict) -> list[Any]:
    """Build title page elements."""
    return [
        Spacer(1, 1.5 * inch),
        Paragraph("ॐ", st["om"]),
        Paragraph(f"{chart.name}", st["title"]),
        Paragraph(
            f"जन्म: {chart.dob} | {chart.tob} | {chart.place}",
            st["subtitle"],
        ),
        Spacer(1, 0.3 * inch),
        Paragraph(
            f"लग्न: {chart.lagna_sign_hi} ({chart.lagna_sign_en}) — {chart.lagna_degree:.1f}°",
            st["body_hi"],
        ),
        Paragraph(
            f"चन्द्र: {chart.planets['Moon'].nakshatra} Pada {chart.planets['Moon'].pada}",
            st["body_hi"],
        ),
        Paragraph(
            f"वर्तमान दशा: {md.lord} > {ad.lord}",
            st["body_hi"],
        ),
        Spacer(1, 1 * inch),
        Paragraph("DaivAI", st["footer"]),
    ]


def _embed_image(png_bytes: bytes, width: float) -> Image:
    """Wrap PNG bytes into a ReportLab Image element."""
    buf = io.BytesIO(png_bytes)
    return Image(buf, width=width, height=width * 0.9)


# ── Renderer wrappers ────────────────────────────────────────────────────


def _render_d1(chart: ChartData, ctx: dict) -> bytes | None:
    try:
        from daivai_products.plugins.kundali.diamond import render_d1_chart

        return render_d1_chart(chart, ctx)
    except Exception as e:
        logger.warning("D1 render failed: %s", e)
        return None


def _render_divisional(chart: ChartData, positions: list, name: str, label: str) -> bytes | None:
    try:
        from daivai_products.plugins.kundali.divisional import render_divisional_chart

        return render_divisional_chart(chart, positions, name, label)
    except Exception as e:
        logger.warning("Divisional render failed: %s", e)
        return None


def _render_dasha(
    chart: ChartData, mds: list, md: Any, ad: Any, ads: list, ctx: dict
) -> bytes | None:
    try:
        from daivai_products.plugins.kundali.dasha_gantt import render_dasha_gantt

        return render_dasha_gantt(chart, mds, md, ad, ads, ctx)
    except Exception as e:
        logger.warning("Dasha render failed: %s", e)
        return None


def _render_avk(chart: ChartData, avk: Any) -> bytes | None:
    try:
        from daivai_products.plugins.kundali.ashtakavarga_heatmap import (
            render_ashtakavarga_heatmap,
        )

        return render_ashtakavarga_heatmap(chart, avk)
    except Exception as e:
        logger.warning("Ashtakavarga render failed: %s", e)
        return None


def _render_shadbala(chart: ChartData, sb: list) -> bytes | None:
    try:
        from daivai_products.plugins.kundali.shadbala_chart import (
            render_shadbala_chart,
        )

        return render_shadbala_chart(chart, sb)
    except Exception as e:
        logger.warning("Shadbala render failed: %s", e)
        return None


def _build_pdf(story: list[Any], output_path: str | Path | None) -> bytes | None:
    """Build the final PDF document."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    doc.build(story)
    pdf_bytes = buf.getvalue()

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(pdf_bytes)
        logger.info("PDF saved: %s (%d bytes)", path, len(pdf_bytes))
        return None
    return pdf_bytes
