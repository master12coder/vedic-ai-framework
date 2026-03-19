"""CLI commands — registered on the main Click group."""
from __future__ import annotations

import click
from rich.console import Console

from jyotish_app.cli.main import _load_chart_from_args, main


console = Console()


# ── Daily command ──────────────────────────────────────────────────────────

@main.command()
@click.option("--name", default=None)
@click.option("--dob", default=None)
@click.option("--tob", default=None)
@click.option("--place", default=None)
@click.option("--gender", default="Male")
@click.option("--chart", default=None, help="Saved chart JSON path")
def daily(
    name: str | None, dob: str | None, tob: str | None,
    place: str | None, gender: str, chart: str | None,
) -> None:
    """Get today's personalized daily suggestion."""
    chart_data = _load_chart_from_args(name, dob, tob, place, gender, chart)

    from rich.panel import Panel
    from rich.table import Table

    from jyotish_engine.compute.daily import compute_daily_suggestion

    suggestion = compute_daily_suggestion(chart_data)

    console.print(Panel(f"Daily Suggestion — {chart_data.name}", style="bold cyan"))
    console.print(f"{suggestion.date}\n")

    table = Table()
    table.add_column("Item")
    table.add_column("Value")
    table.add_row("Day", suggestion.vara)
    table.add_row("Nakshatra", suggestion.nakshatra)
    table.add_row("Tithi", suggestion.tithi)
    table.add_row("Color", suggestion.recommended_color)
    table.add_row("Mantra", suggestion.recommended_mantra)
    table.add_row("Rahu Kaal", suggestion.rahu_kaal)
    table.add_row("Day Rating", f"{'⭐' * suggestion.day_rating} ({suggestion.day_rating}/10)")
    table.add_row("Health Focus", suggestion.health_focus)
    console.print(table)

    if suggestion.good_for:
        console.print("\n[bold green]Good For Today[/bold green]")
        for item in suggestion.good_for:
            console.print(f" • {item}")

    if suggestion.avoid:
        console.print("\n[bold red]Avoid Today[/bold red]")
        for item in suggestion.avoid:
            console.print(f" • {item}")


# ── Transit command ────────────────────────────────────────────────────────

@main.command()
@click.option("--name", default=None)
@click.option("--dob", default=None)
@click.option("--tob", default=None)
@click.option("--place", default=None)
@click.option("--gender", default="Male")
@click.option("--chart", default=None, help="Saved chart JSON path")
@click.option("--months", default=6, help="Forecast period in months")
def transit(
    name: str | None, dob: str | None, tob: str | None,
    place: str | None, gender: str, chart: str | None, months: int,
) -> None:
    """Show current transits for a chart."""
    chart_data = _load_chart_from_args(name, dob, tob, place, gender, chart)

    from rich.panel import Panel
    from rich.table import Table

    from jyotish_engine.compute.transit import compute_transits

    transits = compute_transits(chart_data)

    console.print(Panel(
        f"Transits — {chart_data.name} — {transits.date}",
        style="bold cyan",
    ))
    console.print(f"Natal Lagna: {chart_data.lagna_sign} Forecast period: {months} month(s)\n")

    table = Table()
    for col in ["Planet", "Sign", "Natal House", "Retrograde"]:
        table.add_column(col)
    for t in transits.planets:
        table.add_row(t.planet, t.sign, str(t.natal_house), "R" if t.is_retrograde else "")
    console.print(table)


# ── Muhurta command ────────────────────────────────────────────────────────

@main.command()
@click.option("--purpose", required=True, help="Purpose (marriage, business_start, etc.)")
@click.option("--chart", required=True, help="Saved chart JSON path")
@click.option("--from", "from_date", required=True, help="Start date (DD/MM/YYYY)")
@click.option("--to", "to_date", required=True, help="End date (DD/MM/YYYY)")
def muhurta(purpose: str, chart: str, from_date: str, to_date: str) -> None:
    """Find auspicious dates (muhurta)."""
    chart_data = _load_chart_from_args(chart=chart)

    from rich.panel import Panel
    from rich.table import Table

    from jyotish_engine.compute.datetime_utils import parse_birth_datetime
    from jyotish_engine.compute.muhurta import find_muhurta

    tz = chart_data.timezone_name
    start = parse_birth_datetime(from_date, "00:00", tz)
    end = parse_birth_datetime(to_date, "23:59", tz)
    purpose_clean = purpose.replace("_", " ").replace("-", " ")

    results = find_muhurta(
        purpose=purpose_clean,
        lat=chart_data.latitude, lon=chart_data.longitude,
        tz_name=tz, start_date=start, end_date=end,
    )

    console.print(Panel(f"Muhurta for {purpose_clean.title()}", style="bold cyan"))
    console.print(f"Search: {from_date} to {to_date}\n")

    table = Table()
    for col in ["#", "Date", "Day", "Nakshatra", "Tithi", "Score", "Reasons"]:
        table.add_column(col)
    for i, r in enumerate(results[:10], 1):
        table.add_row(
            str(i), r.date, r.day, r.nakshatra, r.tithi,
            f"{r.score:.1f}", "; ".join(r.reasons),
        )
    console.print(table)


# ── Pooja command ──────────────────────────────────────────────────────────

@main.command()
@click.option("--name", default=None)
@click.option("--dob", default=None)
@click.option("--tob", default=None)
@click.option("--place", default=None)
@click.option("--gender", default="Male")
@click.option("--chart", default=None, help="Saved chart JSON path")
def pooja(
    name: str | None, dob: str | None, tob: str | None,
    place: str | None, gender: str, chart: str | None,
) -> None:
    """Generate personalized weekly pooja plan."""
    chart_data = _load_chart_from_args(name, dob, tob, place, gender, chart)

    try:
        from jyotish_products.plugins.kundali.report import generate_report
        result = generate_report(chart_data, sections=["gemstones"])
        console.print(result)
    except ImportError:
        console.print("[yellow]Pooja planner requires jyotish-products.[/yellow]")


# ── Events command ─────────────────────────────────────────────────────────

@main.group()
def events() -> None:
    """Life event tracking commands."""


@events.command("add")
@click.option("--chart", required=True, help="Saved chart JSON path")
@click.option("--type", "event_type", required=True, help="Event type")
@click.option("--date", "event_date", required=True, help="Event date")
@click.option("--desc", default="", help="Description")
def events_add(chart: str, event_type: str, event_date: str, desc: str) -> None:
    """Add a life event."""
    chart_data = _load_chart_from_args(chart=chart)

    try:
        from jyotish_products.store.events import LifeEventsDB

        db = LifeEventsDB()
        event_id = db.add_event(
            chart_id=chart_data.name,
            event_type=event_type,
            event_date=event_date,
            description=desc,
        )
        console.print(f"Event added: {event_id}")
        console.print(f"  Type: {event_type}")
        console.print(f"  Date: {event_date}")
        console.print(f"  Description: {desc}")
    except ImportError:
        console.print("[yellow]Events require jyotish-products.[/yellow]")


# ── Dashboard command ──────────────────────────────────────────────────────

@main.command()
def dashboard() -> None:
    """Show prediction accuracy dashboard."""
    from rich.panel import Panel

    try:
        from jyotish_products.store.predictions import PredictionTracker

        tracker = PredictionTracker()
        stats = tracker.get_stats()
        console.print(Panel("Prediction Accuracy Dashboard", style="bold cyan"))
        console.print(
            f"Total predictions: {stats.get('total', 0)} "
            f"Pending: {stats.get('pending', 0)} "
            f"Overall accuracy: {stats.get('accuracy', 0):.1f}%"
        )
        if stats.get("total", 0) == 0:
            console.print("\nNo decided predictions yet.")
    except ImportError:
        console.print("[yellow]Dashboard requires jyotish-products.[/yellow]")


# ── Family commands ────────────────────────────────────────────────────

@main.group()
def family() -> None:
    """Family chart management."""


@family.command("add")
@click.option("--name", required=True)
@click.option("--dob", required=True)
@click.option("--tob", required=True)
@click.option("--place", default=None)
@click.option("--gender", default="Male")
@click.option("--relation", default="self")
def family_add(name: str, dob: str, tob: str, place: str | None,
               gender: str, relation: str) -> None:
    """Add a family member."""
    from jyotish_products.store.family import add_member
    chart = add_member(name=name, dob=dob, tob=tob, place=place,
                       gender=gender, relation=relation)
    console.print(f"Added: {name} ({relation}) — Lagna: {chart.lagna_sign}")


@family.command("list")
def family_list() -> None:
    """List all family members."""
    from jyotish_products.store.family import list_members
    members = list_members()
    if not members:
        console.print("No family members. Add with: jyotish family add --name ...")
        return
    for m in members:
        console.print(f"  {m['name']:20s} {m['relation']:10s} {m['dob']}  Lagna: {m['lagna']}")


@family.command("daily")
@click.option("--level", default="simple", help="simple/medium/detailed")
def family_daily(level: str) -> None:
    """Run daily for all family members."""
    from jyotish_products.store.family import run_daily_for_all
    results = run_daily_for_all(level=level)
    for name, msg in results.items():
        console.print(f"\n[bold cyan]{name}[/bold cyan]")
        console.print(msg)


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
    name: str | None, dob: str | None, tob: str | None,
    place: str | None, gender: str, chart: str | None,
    body_weight: float, purpose: str,
) -> None:
    """Compute personalized gemstone weight using 10 chart factors."""
    chart_data = _load_chart_from_args(name, dob, tob, place, gender, chart)

    from jyotish_products.plugins.remedies.formatter import format_gemstone_report
    from jyotish_products.plugins.remedies.gemstone import compute_gemstone_weights

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
    name: str | None, dob: str | None, tob: str | None,
    place: str | None, gender: str, chart: str | None,
    body_weight: float, fmt: str, output: str,
) -> None:
    """Generate visual kundali PDF with charts, dashas, and gemstones."""
    chart_data = _load_chart_from_args(name, dob, tob, place, gender, chart)

    from jyotish_products.plugins.kundali.pdf import generate_pdf

    gem_results = None
    if body_weight > 0:
        from jyotish_products.plugins.remedies.gemstone import compute_gemstone_weights
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
def pdf(name: str | None, dob: str | None, tob: str | None,
        place: str | None, gender: str, chart: str | None, output: str) -> None:
    """Generate kundali PDF (legacy, use 'kundali' command instead)."""
    chart_data = _load_chart_from_args(name, dob, tob, place, gender, chart)

    from jyotish_products.plugins.kundali.pdf import generate_pdf

    generate_pdf(chart_data, output_path=output, fmt="detailed")
    console.print(f"PDF saved to {output}")


# ── Web server ─────────────────────────────────────────────────────────

@main.command()
@click.option("--port", default=8000, help="Port number")
def web(port: int) -> None:
    """Start the web dashboard."""
    try:
        import uvicorn

        from jyotish_app.web.app import create_app
        app = create_app()
        console.print(f"Starting web dashboard on http://localhost:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    except ImportError:
        console.print("[yellow]Web requires: pip install 'jyotish[web]'[/yellow]")
