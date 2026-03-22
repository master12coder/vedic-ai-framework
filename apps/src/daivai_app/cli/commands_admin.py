"""CLI commands for admin/management functions: pooja, events, dashboard, family."""

from __future__ import annotations

import click
from rich.console import Console

from daivai_app.cli.main import _load_chart_from_args, main


console = Console()


# ── Pooja command ──────────────────────────────────────────────────────────


@main.command()
@click.option("--name", default=None)
@click.option("--dob", default=None)
@click.option("--tob", default=None)
@click.option("--place", default=None)
@click.option("--gender", default="Male")
@click.option("--chart", default=None, help="Saved chart JSON path")
def pooja(
    name: str | None,
    dob: str | None,
    tob: str | None,
    place: str | None,
    gender: str,
    chart: str | None,
) -> None:
    """Generate personalized weekly pooja plan."""
    chart_data = _load_chart_from_args(name, dob, tob, place, gender, chart)

    try:
        from daivai_products.plugins.kundali.report import generate_report

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
        from daivai_products.store.events import LifeEventsDB

        db = LifeEventsDB()
        chart_db_id = db.get_or_create_chart_from_data(chart_data)
        event_id = db.add_event_simple(
            chart_id=chart_db_id,
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
        from daivai_products.store.predictions import PredictionTracker

        tracker = PredictionTracker()
        stats = tracker.get_accuracy_dashboard()
        console.print(Panel("Prediction Accuracy Dashboard", style="bold cyan"))
        console.print(
            f"Total predictions: {stats.get('total_predictions', 0)} "
            f"Pending: {stats.get('pending', 0)} "
            f"Overall accuracy: {stats.get('overall_accuracy', 0):.1f}%"
        )
        if stats.get("total_predictions", 0) == 0:
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
def family_add(
    name: str, dob: str, tob: str, place: str | None, gender: str, relation: str
) -> None:
    """Add a family member."""
    from daivai_products.store.family import add_member

    chart = add_member(name=name, dob=dob, tob=tob, place=place, gender=gender, relation=relation)
    console.print(f"Added: {name} ({relation}) — Lagna: {chart.lagna_sign}")


@family.command("list")
def family_list() -> None:
    """List all family members."""
    from daivai_products.store.family import list_members

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
    from daivai_products.store.family import run_daily_for_all

    results = run_daily_for_all(level=level)
    for name, msg in results.items():
        console.print(f"\n[bold cyan]{name}[/bold cyan]")
        console.print(msg)
