"""PDF kundali assembler — HTML-first with WeasyPrint, ReportLab fallback.

Primary path: Jinja2 HTML → WeasyPrint PDF (beautiful, print-ready).
Fallback path: ReportLab + matplotlib (if weasyprint not installed).
Also provides generate_html() for browser preview.
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from daivai_engine.models.chart import ChartData
from daivai_products.plugins.kundali.html_context import build_kundali_context
from daivai_products.plugins.kundali.theme import get_font_path


logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def generate_html(
    chart: ChartData,
    fmt: str = "detailed",
    gemstone_results: list[Any] | None = None,
    standalone: bool = False,
    full_analysis: Any | None = None,
) -> str:
    """Generate complete HTML kundali report.

    Args:
        chart: Computed birth chart.
        fmt: 'summary', 'detailed', or 'pandit'.
        gemstone_results: Pre-computed gemstone weight results.
        standalone: If True, embed font as base64 data URI for PDF.
        full_analysis: Optional FullChartAnalysis — avoids recomputing engine modules.

    Returns:
        Complete HTML string.
    """
    ctx = build_kundali_context(
        chart, fmt=fmt, gemstone_results=gemstone_results, full_analysis=full_analysis
    )

    # Font embedding for standalone/PDF mode
    font_data_uri = ""
    if standalone:
        font_data_uri = _font_data_uri()

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=False,
    )
    template = env.get_template("kundali.html")
    return template.render(
        standalone=standalone,
        font_data_uri=font_data_uri,
        **ctx,
    )


def generate_pdf(
    chart: ChartData,
    output_path: str | Path | None = None,
    fmt: str = "detailed",
    body_weight_kg: float = 0,
    chart_image_bytes: bytes | None = None,
    gemstone_results: list[Any] | None = None,
    full_analysis: Any | None = None,
) -> bytes | None:
    """Generate a complete kundali PDF report.

    Tries WeasyPrint first (HTML-based, beautiful output).
    Falls back to ReportLab if WeasyPrint is not installed.

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
    # Try WeasyPrint first
    try:
        pdf_bytes = _generate_weasyprint(chart, fmt, gemstone_results, full_analysis)
        logger.info("PDF generated via WeasyPrint (%d bytes)", len(pdf_bytes))
    except ImportError:
        logger.info("WeasyPrint not available, falling back to ReportLab")
        from daivai_products.plugins.kundali.pdf_reportlab import (
            generate_pdf_reportlab,
        )

        return generate_pdf_reportlab(
            chart,
            output_path=output_path,
            fmt=fmt,
            body_weight_kg=body_weight_kg,
            chart_image_bytes=chart_image_bytes,
            gemstone_results=gemstone_results,
        )
    except Exception:
        logger.exception("WeasyPrint failed, falling back to ReportLab")
        from daivai_products.plugins.kundali.pdf_reportlab import (
            generate_pdf_reportlab,
        )

        return generate_pdf_reportlab(
            chart,
            output_path=output_path,
            fmt=fmt,
            body_weight_kg=body_weight_kg,
            chart_image_bytes=chart_image_bytes,
            gemstone_results=gemstone_results,
        )

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(pdf_bytes)
        logger.info("PDF saved: %s", path)
        return None
    return pdf_bytes


def _generate_weasyprint(
    chart: ChartData,
    fmt: str,
    gemstone_results: list[Any] | None,
    full_analysis: Any | None = None,
) -> bytes:
    """Generate PDF bytes via WeasyPrint (raises ImportError if missing)."""
    from weasyprint import HTML

    html_str = generate_html(
        chart,
        fmt=fmt,
        gemstone_results=gemstone_results,
        standalone=True,
        full_analysis=full_analysis,
    )
    result: bytes = HTML(string=html_str).write_pdf()  # type: ignore[assignment]
    return result


def _font_data_uri() -> str:
    """Build a base64 data URI for the Devanagari font."""
    font_path = get_font_path()
    if font_path and font_path.exists():
        data = font_path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:font/truetype;base64,{b64}"
    return ""
