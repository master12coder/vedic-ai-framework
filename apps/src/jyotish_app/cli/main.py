"""Main CLI entry point — core commands + auto-import of commands.py."""
from __future__ import annotations

import logging
import sys

import click
from rich.console import Console

from jyotish_engine.compute.chart import compute_chart
from jyotish_engine.models.chart import ChartData


logger = logging.getLogger(__name__)
console = Console()


def _load_chart_from_args(
    name: str | None = None,
    dob: str | None = None,
    tob: str | None = None,
    place: str | None = None,
    gender: str = "Male",
    chart: str | None = None,
) -> ChartData:
    """Load chart from saved JSON or compute from birth details."""
    if chart:
        import json
        from pathlib import Path

        path = Path(chart)
        if not path.exists():
            console.print(f"[red]Chart file not found: {chart}[/red]")
            sys.exit(1)
        data = json.loads(path.read_text())
        return ChartData.model_validate(data)

    if not all([name, dob, tob]):
        console.print("[red]Provide --name, --dob, --tob (and --place or --chart)[/red]")
        sys.exit(1)

    return compute_chart(name=name, dob=dob, tob=tob, place=place, gender=gender)


@click.group()
@click.version_option(version="1.0.0", prog_name="jyotish")
def main() -> None:
    """Vedic AI Framework — AI-powered Vedic astrology."""
    logging.basicConfig(level=logging.WARNING)


@main.command()
@click.option("--name", required=True, help="Full name")
@click.option("--dob", required=True, help="Date of birth (DD/MM/YYYY)")
@click.option("--tob", required=True, help="Time of birth (HH:MM)")
@click.option("--place", default=None, help="Place of birth")
@click.option("--gender", default="Male", help="Gender (Male/Female)")
def chart(name: str, dob: str, tob: str, place: str | None, gender: str) -> None:
    """Compute and display a Vedic birth chart."""
    from rich.panel import Panel
    from rich.table import Table

    from jyotish_engine.compute.dosha import detect_all_doshas
    from jyotish_engine.compute.yoga import detect_all_yogas

    chart_data = compute_chart(name=name, dob=dob, tob=tob, place=place, gender=gender)

    console.print(Panel(f"Vedic Birth Chart — {chart_data.name}", style="bold cyan"))
    console.print(
        f"DOB: {chart_data.dob}  TOB: {chart_data.tob}  "
        f"Place: {chart_data.place} "
        f"Lagna: {chart_data.lagna_sign} ({chart_data.lagna_sign_en}) — "
        f"{chart_data.lagna_degree:.1f}°"
    )

    table = Table(title="Planetary Positions")
    for col in ["Planet", "Sign", "House", "Degree", "Nakshatra", "Pada", "Dignity", "R", "C"]:
        table.add_column(col)
    for p in chart_data.planets.values():
        table.add_row(
            p.name, p.sign, str(p.house), f"{p.degree_in_sign:.1f}°",
            p.nakshatra, str(p.pada), p.dignity,
            "R" if p.is_retrograde else "", "C" if p.is_combust else "",
        )
    console.print(table)

    yogas = detect_all_yogas(chart_data)
    if yogas:
        console.print("\n[bold]Yogas Detected[/bold]")
        for y in yogas:
            pfx = "[+]" if y.effect == "benefic" else "[-]" if y.effect == "malefic" else "[~]"
            console.print(f"{pfx} {y.name} ({y.name_hindi}) — {y.description}")

    doshas = detect_all_doshas(chart_data)
    if doshas:
        console.print("\n[bold]Doshas[/bold]")
        for d in doshas:
            console.print(f"{'⚠️' if d.is_present else '✓'} {d.name} — {d.description}")


@main.command()
@click.option("--name", required=True)
@click.option("--dob", required=True)
@click.option("--tob", required=True)
@click.option("--place", default=None)
@click.option("--gender", default="Male")
@click.option("-o", "--output", required=True, help="Output JSON file path")
def save(name: str, dob: str, tob: str, place: str | None, gender: str, output: str) -> None:
    """Compute and save chart as JSON for later reuse."""
    from pathlib import Path

    chart_data = compute_chart(name=name, dob=dob, tob=tob, place=place, gender=gender)
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(chart_data.model_dump_json(indent=2))
    console.print(f"Chart saved to {output}")
    console.print(f"Lagna: {chart_data.lagna_sign} ({chart_data.lagna_sign_en})")


@main.command()
@click.option("--name", default=None)
@click.option("--dob", default=None)
@click.option("--tob", default=None)
@click.option("--place", default=None)
@click.option("--gender", default="Male")
@click.option("--chart", default=None, help="Saved chart JSON path")
@click.option("--llm", default="none", help="LLM backend")
def report(
    name: str | None, dob: str | None, tob: str | None,
    place: str | None, gender: str, chart: str | None, llm: str,
) -> None:
    """Generate full chart report with interpretation."""
    chart_data = _load_chart_from_args(name, dob, tob, place, gender, chart)

    try:
        from jyotish_products.plugins.kundali.report import generate_report
        result = generate_report(chart_data)
        console.print(result)
    except ImportError:
        console.print("[yellow]Report requires jyotish-products.[/yellow]")

    if llm != "none":
        try:
            from jyotish_products.interpret.factory import get_backend
            from jyotish_products.interpret.renderer import interpret_chart

            backend = get_backend(llm)
            if not backend.is_available():
                console.print(f"[red]LLM backend '{llm}' not available. Check API key.[/red]")
                return

            console.print(f"\n[bold cyan]AI Interpretation ({backend.name()})[/bold cyan]")
            sections = interpret_chart(chart_data, backend=backend)
            for section_name, text in sections.items():
                console.print(f"\n[bold]{section_name.replace('_', ' ').title()}[/bold]")
                console.print(text)
        except ImportError:
            console.print("[yellow]LLM not available. Install jyotish-products.[/yellow]")
        except Exception as e:
            console.print(f"[red]LLM error: {e}[/red]")


def cli() -> None:
    """Entry point that registers all commands then runs main."""
    import jyotish_app.cli.commands  # noqa: F401 — registers commands on main group
    main()


if __name__ == "__main__":
    cli()
