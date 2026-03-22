"""CLI commands — registered on the main Click group.

Sub-modules (imported here to trigger Click command registration):
    commands_observational — daily, transit, muhurta
    commands_admin         — pooja, events, dashboard, family
"""

from __future__ import annotations

import click
from rich.console import Console

# Import sub-modules to register their commands on the main group
import daivai_app.cli.commands_admin
import daivai_app.cli.commands_observational  # noqa: F401
from daivai_app.cli.main import _load_chart_from_args, main


console = Console()


# ── Gemstone weight ───────────────────────────────────────────────────


@main.command()
@click.option("--name", default=None)
@click.option("--dob", default=None)
@click.option("--tob", default=None)
@click.option("--place", default=None)
@click.option("--gender", default="Male")
@click.option("--chart", default=None, help="Saved chart JSON path")
@click.option("--weight", "body_weight", required=True, type=float, help="Body weight in kg")
@click.option("--purpose", default="growth", help="protection/growth/maximum")
def gemstone(
    name: str | None,
    dob: str | None,
    tob: str | None,
    place: str | None,
    gender: str,
    chart: str | None,
    body_weight: float,
    purpose: str,
) -> None:
    """Compute personalized gemstone weight using 10 chart factors."""
    chart_data = _load_chart_from_args(name, dob, tob, place, gender, chart)

    from daivai_products.plugins.remedies.formatter import format_gemstone_report
    from daivai_products.plugins.remedies.gemstone import compute_gemstone_weights

    results = compute_gemstone_weights(chart_data, body_weight, purpose)
    report = format_gemstone_report(results, body_weight, chart_data.lagna_sign, chart_data.name)
    console.print(report)


# ── Kundali PDF ───────────────────────────────────────────────────────


@main.command()
@click.option("--name", default=None)
@click.option("--dob", default=None)
@click.option("--tob", default=None)
@click.option("--place", default=None)
@click.option("--gender", default="Male")
@click.option("--chart", default=None, help="Saved chart JSON path")
@click.option("--weight", "body_weight", default=0, type=float, help="Body weight kg")
@click.option("--format", "fmt", default="detailed", help="summary/detailed/pandit")
@click.option("-o", "--output", required=True, help="Output PDF path")
def kundali(
    name: str | None,
    dob: str | None,
    tob: str | None,
    place: str | None,
    gender: str,
    chart: str | None,
    body_weight: float,
    fmt: str,
    output: str,
) -> None:
    """Generate visual kundali PDF with charts, dashas, and gemstones."""
    chart_data = _load_chart_from_args(name, dob, tob, place, gender, chart)

    from daivai_products.plugins.kundali.pdf import generate_pdf

    gem_results = None
    if body_weight > 0:
        from daivai_products.plugins.remedies.gemstone import compute_gemstone_weights

        gem_results = compute_gemstone_weights(chart_data, body_weight)

    generate_pdf(chart_data, output_path=output, fmt=fmt, gemstone_results=gem_results)
    console.print(f"Kundali PDF ({fmt}) saved to {output}")


@main.command()
@click.option("--name", default=None)
@click.option("--dob", default=None)
@click.option("--tob", default=None)
@click.option("--place", default=None)
@click.option("--gender", default="Male")
@click.option("--chart", default=None, help="Saved chart JSON path")
@click.option("-o", "--output", required=True, help="Output PDF path")
def pdf(
    name: str | None,
    dob: str | None,
    tob: str | None,
    place: str | None,
    gender: str,
    chart: str | None,
    output: str,
) -> None:
    """Generate kundali PDF (legacy, use 'kundali' command instead)."""
    chart_data = _load_chart_from_args(name, dob, tob, place, gender, chart)

    from daivai_products.plugins.kundali.pdf import generate_pdf

    generate_pdf(chart_data, output_path=output, fmt="detailed")
    console.print(f"PDF saved to {output}")


# ── Web server ─────────────────────────────────────────────────────────


@main.command()
@click.option("--port", default=8000, help="Port number")
def web(port: int) -> None:
    """Start the web dashboard."""
    try:
        import uvicorn

        from daivai_app.web.app import create_app

        app = create_app()
        console.print(f"Starting web dashboard on http://localhost:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    except ImportError:
        console.print("[yellow]Web requires: pip install 'jyotish[web]'[/yellow]")
