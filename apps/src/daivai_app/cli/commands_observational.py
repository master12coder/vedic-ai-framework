"""CLI commands for observational/transit functions: daily, transit, muhurta."""

from __future__ import annotations

import click
from rich.console import Console

from daivai_app.cli.main import _load_chart_from_args, main


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
    name: str | None,
    dob: str | None,
    tob: str | None,
    place: str | None,
    gender: str,
    chart: str | None,
) -> None:
    """Get today's personalized daily suggestion."""
    chart_data = _load_chart_from_args(name, dob, tob, place, gender, chart)

    from rich.panel import Panel
    from rich.table import Table

    from daivai_engine.compute.daily import compute_daily_suggestion

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
    name: str | None,
    dob: str | None,
    tob: str | None,
    place: str | None,
    gender: str,
    chart: str | None,
    months: int,
) -> None:
    """Show current transits for a chart."""
    chart_data = _load_chart_from_args(name, dob, tob, place, gender, chart)

    from rich.panel import Panel
    from rich.table import Table

    from daivai_engine.compute.transit import compute_transits

    transits = compute_transits(chart_data)

    console.print(
        Panel(
            f"Transits — {chart_data.name} — {transits.target_date}",
            style="bold cyan",
        )
    )
    console.print(f"Natal Lagna: {chart_data.lagna_sign} Forecast period: {months} month(s)\n")

    table = Table()
    for col in ["Planet", "Sign", "Natal House", "Retrograde"]:
        table.add_column(col)
    for t in transits.transits:
        table.add_row(t.name, t.sign, str(t.natal_house_activated), "R" if t.is_retrograde else "")
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

    from daivai_engine.compute.datetime_utils import parse_birth_datetime
    from daivai_engine.compute.muhurta import find_muhurta

    tz = chart_data.timezone_name
    start = parse_birth_datetime(from_date, "00:00", tz)
    end = parse_birth_datetime(to_date, "23:59", tz)
    purpose_clean = purpose.replace("_", " ").replace("-", " ")

    results = find_muhurta(
        purpose=purpose_clean,
        lat=chart_data.latitude,
        lon=chart_data.longitude,
        tz_name=tz,
        start_date=start,
        end_date=end,
    )

    console.print(Panel(f"Muhurta for {purpose_clean.title()}", style="bold cyan"))
    console.print(f"Search: {from_date} to {to_date}\n")

    table = Table()
    for col in ["#", "Date", "Day", "Nakshatra", "Tithi", "Score", "Reasons"]:
        table.add_column(col)
    for i, r in enumerate(results[:10], 1):
        table.add_row(
            str(i),
            r.date,
            r.day,
            r.nakshatra,
            r.tithi,
            f"{r.score:.1f}",
            "; ".join(r.reasons),
        )
    console.print(table)
