"""CLI entry point — click-based command interface."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="jyotish")
def main():
    """Vedic AI Framework — AI-powered Vedic astrology computation and interpretation."""
    pass


@main.command()
@click.option("--name", required=True, help="Full name")
@click.option("--dob", required=True, help="Date of birth (DD/MM/YYYY)")
@click.option("--tob", required=True, help="Time of birth (HH:MM)")
@click.option("--place", required=True, help="Place of birth")
@click.option("--gender", default="Male", help="Gender (Male/Female)")
@click.option("--format", "fmt", default="terminal", type=click.Choice(["terminal", "json"]))
def chart(name: str, dob: str, tob: str, place: str, gender: str, fmt: str):
    """Compute a Vedic birth chart."""
    from jyotish.compute.chart import compute_chart
    from jyotish.interpret.formatter import format_chart_terminal, format_chart_json

    try:
        chart_data = compute_chart(name=name, dob=dob, tob=tob, place=place, gender=gender)
    except Exception as e:
        console.print(f"[red]Error computing chart: {e}[/red]")
        sys.exit(1)

    if fmt == "json":
        click.echo(format_chart_json(chart_data))
    else:
        md = Markdown(format_chart_terminal(chart_data))
        console.print(md)


@main.command()
@click.option("--name", required=True, help="Full name")
@click.option("--dob", required=True, help="Date of birth (DD/MM/YYYY)")
@click.option("--tob", required=True, help="Time of birth (HH:MM)")
@click.option("--place", required=True, help="Place of birth")
@click.option("--gender", default="Male", help="Gender")
@click.option("--llm", default=None, help="LLM backend (ollama/groq/claude/openai/none)")
@click.option("--output", default=None, help="Output file path")
@click.option("--events", default=None, help="Life events JSON file")
def report(name: str, dob: str, tob: str, place: str, gender: str, llm: str, output: str, events: str):
    """Generate full chart report with interpretation."""
    from jyotish.compute.chart import compute_chart
    from jyotish.interpret.interpreter import interpret_chart, interpret_with_events
    from jyotish.interpret.formatter import format_report_markdown, format_chart_terminal
    from jyotish.interpret.llm_backend import get_backend

    try:
        chart_data = compute_chart(name=name, dob=dob, tob=tob, place=place, gender=gender)
    except Exception as e:
        console.print(f"[red]Error computing chart: {e}[/red]")
        sys.exit(1)

    backend = get_backend(llm) if llm else get_backend("none")

    if backend.name() == "none":
        content = format_chart_terminal(chart_data)
    else:
        try:
            if events:
                event_data = json.loads(Path(events).read_text())
                content = interpret_with_events(chart_data, event_data, backend)
            else:
                interpretations = interpret_chart(chart_data, backend)
                content = format_report_markdown(chart_data, interpretations)
        except Exception as e:
            console.print(f"[yellow]LLM interpretation failed: {e}[/yellow]")
            console.print("[yellow]Falling back to computation-only output.[/yellow]")
            content = format_chart_terminal(chart_data)

    if output:
        Path(output).write_text(content, encoding="utf-8")
        console.print(f"[green]Report saved to {output}[/green]")
    else:
        md = Markdown(content)
        console.print(md)


@main.command()
@click.option("--chart-file", "chart_file", required=True, help="Path to saved chart JSON")
def transit(chart_file: str):
    """Show current transits for a saved chart."""
    from jyotish.compute.chart import compute_chart
    from jyotish.compute.transit import compute_transits

    chart_path = Path(chart_file)
    if not chart_path.exists():
        console.print(f"[red]Chart file not found: {chart_file}[/red]")
        sys.exit(1)

    data = json.loads(chart_path.read_text())
    chart_info = data.get("chart", data)
    chart_data = compute_chart(
        name=chart_info["name"], dob=chart_info["dob"],
        tob=chart_info["tob"], place=chart_info["place"],
    )

    transit_data = compute_transits(chart_data)

    lines = [f"# Transits for {transit_data.natal_chart_name} — {transit_data.target_date}"]
    lines.append(f"Natal Lagna: {transit_data.natal_lagna_sign}")
    lines.append("")
    lines.append("| Planet | Sign | Natal House | Retrograde |")
    lines.append("|--------|------|-------------|------------|")
    for t in transit_data.transits:
        r = "R" if t.is_retrograde else ""
        lines.append(f"| {t.name} | {t.sign} | {t.natal_house_activated} | {r} |")
    lines.append("")
    lines.append("## Major Transits")
    for mt in transit_data.major_transits:
        lines.append(f"- {mt}")

    md = Markdown("\n".join(lines))
    console.print(md)


@main.command()
@click.option("--chart-file", "chart_file", required=True, help="Path to saved chart JSON")
@click.option("--llm", default=None, help="LLM backend")
def daily(chart_file: str, llm: str):
    """Get daily suggestion for a chart."""
    from jyotish.compute.chart import compute_chart
    from jyotish.interpret.interpreter import get_daily_suggestion
    from jyotish.interpret.llm_backend import get_backend

    chart_path = Path(chart_file)
    if not chart_path.exists():
        console.print(f"[red]Chart file not found: {chart_file}[/red]")
        sys.exit(1)

    data = json.loads(chart_path.read_text())
    chart_info = data.get("chart", data)
    chart_data = compute_chart(
        name=chart_info["name"], dob=chart_info["dob"],
        tob=chart_info["tob"], place=chart_info["place"],
    )

    backend = get_backend(llm) if llm else get_backend()
    suggestion = get_daily_suggestion(chart_data, backend)
    md = Markdown(suggestion)
    console.print(md)


@main.command(name="match")
@click.option("--person1", required=True, help="Person 1 chart JSON")
@click.option("--person2", required=True, help="Person 2 chart JSON")
def match_cmd(person1: str, person2: str):
    """Ashtakoot (36 guna) matching between two charts."""
    from jyotish.compute.chart import compute_chart
    from jyotish.compute.matching import compute_ashtakoot
    from jyotish.deliver.markdown_report import generate_matching_report

    def _load_chart(path_str: str):
        path = Path(path_str)
        if not path.exists():
            console.print(f"[red]File not found: {path_str}[/red]")
            sys.exit(1)
        data = json.loads(path.read_text())
        ci = data.get("chart", data)
        return compute_chart(name=ci["name"], dob=ci["dob"], tob=ci["tob"], place=ci["place"])

    c1 = _load_chart(person1)
    c2 = _load_chart(person2)

    result = compute_ashtakoot(
        person1_nakshatra_index=c1.planets["Moon"].nakshatra_index,
        person1_moon_sign=c1.planets["Moon"].sign_index,
        person2_nakshatra_index=c2.planets["Moon"].nakshatra_index,
        person2_moon_sign=c2.planets["Moon"].sign_index,
    )

    report = generate_matching_report(result, c1.name, c2.name)
    md = Markdown(report)
    console.print(md)


@main.command()
@click.option("--purpose", required=True, type=click.Choice(["marriage", "business", "travel", "property"]))
@click.option("--place", required=True, help="Location for muhurta")
@click.option("--from-date", "from_date", required=True, help="Start date (DD/MM/YYYY)")
@click.option("--to-date", "to_date", required=True, help="End date (DD/MM/YYYY)")
def muhurta(purpose: str, place: str, from_date: str, to_date: str):
    """Find auspicious dates (muhurta)."""
    from jyotish.utils.geo import resolve_place
    from jyotish.utils.datetime_utils import parse_birth_datetime
    from jyotish.compute.muhurta import find_muhurta

    geo = resolve_place(place)
    start = parse_birth_datetime(from_date, "00:00", geo.timezone_name)
    end = parse_birth_datetime(to_date, "23:59", geo.timezone_name)

    candidates = find_muhurta(purpose, geo.latitude, geo.longitude, start, end, geo.timezone_name)

    lines = [f"# Muhurta for {purpose.title()} — {place}"]
    lines.append(f"Search: {from_date} to {to_date}")
    lines.append("")
    if candidates:
        lines.append("| # | Date | Day | Nakshatra | Tithi | Score | Key Reasons |")
        lines.append("|---|------|-----|-----------|-------|-------|-------------|")
        for i, c in enumerate(candidates, 1):
            reasons = "; ".join(c.reasons[:2])
            lines.append(f"| {i} | {c.date} | {c.day} | {c.nakshatra} | {c.tithi} | {c.score} | {reasons} |")
    else:
        lines.append("No suitable muhurta found in the given range.")

    md = Markdown("\n".join(lines))
    console.print(md)


@main.command()
@click.option("--chart-name", "chart_name", required=True, help="Chart name")
@click.option("--category", required=True, help="Category (gemstone/house_reading/dasha/remedy/yoga/dosha)")
@click.option("--ai-said", "ai_said", required=True, help="What the AI said")
@click.option("--pandit-said", "pandit_said", required=True, help="What Pandit Ji said")
@click.option("--reasoning", default="", help="Pandit Ji's reasoning")
@click.option("--pandit", default="Pandit Ji", help="Pandit name")
def correct(chart_name: str, category: str, ai_said: str, pandit_said: str, reasoning: str, pandit: str):
    """Add a Pandit Ji correction."""
    from jyotish.learn.corrections import PanditCorrection, PanditCorrectionStore

    store = PanditCorrectionStore()
    correction = PanditCorrection(
        pandit_name=pandit,
        chart_name=chart_name,
        category=category,
        ai_said=ai_said,
        pandit_said=pandit_said,
        pandit_reasoning=reasoning,
        correction_type="override",
    )
    cid = store.add_correction(correction)
    console.print(f"[green]Correction added with ID: {cid}[/green]")
    console.print(f"Status: pending (validate to learn from it)")


@main.command(name="learn-audio")
@click.option("--file", "audio_file", required=True, help="Audio file path")
@click.option("--chart-name", "chart_name", required=True, help="Chart name")
@click.option("--pandit", default="Pandit Ji", help="Pandit name")
@click.option("--method", default="groq", type=click.Choice(["groq", "local"]))
def learn_audio(audio_file: str, chart_name: str, pandit: str, method: str):
    """Process Pandit Ji audio recording for corrections."""
    from jyotish.learn.audio_processor import process_audio_session
    from jyotish.learn.corrections import PanditCorrectionStore

    try:
        result, corrections = process_audio_session(audio_file, chart_name, pandit, method)
    except Exception as e:
        console.print(f"[red]Error processing audio: {e}[/red]")
        sys.exit(1)

    console.print(f"[green]Transcribed {result.duration_seconds:.0f}s of audio[/green]")
    console.print(f"Language: {result.language}")
    console.print(f"Extracted {len(corrections)} potential corrections")

    if corrections:
        store = PanditCorrectionStore()
        for c in corrections:
            cid = store.add_correction(c)
            console.print(f"  [{cid}] {c.pandit_said[:60]}...")
        console.print("[yellow]All corrections saved as 'pending'. Review and validate them.[/yellow]")


@main.command()
@click.option("--lagna", default=None, help="Filter by lagna")
@click.option("--category", default=None, help="Filter by category")
def rules(lagna: str, category: str):
    """Show learned rules from Pandit Ji corrections."""
    from jyotish.learn.rule_extractor import RuleExtractor

    extractor = RuleExtractor()
    learned_rules = extractor.extract_rules()

    if lagna:
        learned_rules = [r for r in learned_rules if r.lagna == lagna or not r.lagna]
    if category:
        learned_rules = [r for r in learned_rules if r.category == category]

    if not learned_rules:
        console.print("[yellow]No learned rules yet. Add corrections and validate them first.[/yellow]")
        return

    lines = ["# Learned Rules"]
    for r in learned_rules:
        lines.append(f"## [{r.category}] {r.lagna or 'General'}")
        lines.append(f"**Rule:** {r.rule_text}")
        lines.append(f"**Reasoning:** {r.reasoning}")
        lines.append(f"**Confidence:** {r.confidence} | **Sources:** {r.occurrence_count}")
        lines.append("")

    md = Markdown("\n".join(lines))
    console.print(md)


@main.command(name="panchang")
@click.option("--place", required=True, help="Place name")
@click.option("--date", "date_str", default=None, help="Date (DD/MM/YYYY), default today")
def panchang_cmd(place: str, date_str: str):
    """Show Panchang for a date and place."""
    from jyotish.utils.geo import resolve_place
    from jyotish.compute.panchang import compute_panchang
    from datetime import datetime

    geo = resolve_place(place)

    if date_str is None:
        from jyotish.utils.datetime_utils import now_ist
        date_str = now_ist().strftime("%d/%m/%Y")

    panchang = compute_panchang(date_str, geo.latitude, geo.longitude, geo.timezone_name, place)

    lines = [f"# Panchang — {place} — {date_str}"]
    lines.append(f"| Element | Value |")
    lines.append(f"|---------|-------|")
    lines.append(f"| Vara | {panchang.vara} ({panchang.vara_hi}) — {panchang.vara_planet} |")
    lines.append(f"| Tithi | {panchang.tithi_name} ({panchang.paksha} Paksha) |")
    lines.append(f"| Nakshatra | {panchang.nakshatra_name} |")
    lines.append(f"| Yoga | {panchang.yoga_name} |")
    lines.append(f"| Karana | {panchang.karana_name} |")
    lines.append(f"| Sunrise | {panchang.sunrise} |")
    lines.append(f"| Sunset | {panchang.sunset} |")
    lines.append(f"| Rahu Kaal | {panchang.rahu_kaal} |")
    lines.append(f"| Yamaghanda | {panchang.yamaghanda} |")
    lines.append(f"| Gulika | {panchang.gulika} |")

    md = Markdown("\n".join(lines))
    console.print(md)


@main.command(name="export")
@click.option("--name", required=True, help="Full name")
@click.option("--dob", required=True, help="Date of birth (DD/MM/YYYY)")
@click.option("--tob", required=True, help="Time of birth (HH:MM)")
@click.option("--place", required=True, help="Place of birth")
@click.option("--gender", default="Male", help="Gender")
@click.option("--format", "fmt", default="json", type=click.Choice(["json", "markdown"]))
@click.option("--output", default=None, help="Output file path")
def export_cmd(name: str, dob: str, tob: str, place: str, gender: str, fmt: str, output: str):
    """Export chart as JSON or Markdown."""
    from jyotish.compute.chart import compute_chart
    from jyotish.deliver.json_export import export_chart_json
    from jyotish.deliver.markdown_report import generate_markdown_report

    chart_data = compute_chart(name=name, dob=dob, tob=tob, place=place, gender=gender)

    if fmt == "json":
        content = export_chart_json(chart_data, output)
    else:
        content = generate_markdown_report(chart_data, output_path=output)

    if output:
        console.print(f"[green]Exported to {output}[/green]")
    else:
        click.echo(content)


@main.command(name="ashtakavarga")
@click.option("--name", required=True, help="Full name")
@click.option("--dob", required=True, help="Date of birth (DD/MM/YYYY)")
@click.option("--tob", required=True, help="Time of birth (HH:MM)")
@click.option("--place", required=True, help="Place of birth")
def ashtakavarga_cmd(name: str, dob: str, tob: str, place: str):
    """Compute Ashtakavarga bindu table."""
    from jyotish.compute.chart import compute_chart
    from jyotish.compute.ashtakavarga import compute_ashtakavarga

    chart_data = compute_chart(name=name, dob=dob, tob=tob, place=place)
    result = compute_ashtakavarga(chart_data)

    from jyotish.utils.constants import SIGNS
    lines = [f"# Ashtakavarga — {name}", ""]
    lines.append("## Sarvashtakavarga (Total: {})".format(result.total))
    lines.append("| Sign | Bindus |")
    lines.append("|------|--------|")
    for i, b in enumerate(result.sarva):
        lines.append(f"| {SIGNS[i]} | {b} |")
    lines.append("")
    lines.append("## Bhinnashtakavarga")
    for planet, bindus in result.bhinna.items():
        lines.append(f"### {planet}")
        lines.append("| " + " | ".join(SIGNS) + " |")
        lines.append("| " + " | ".join(["---"] * 12) + " |")
        lines.append("| " + " | ".join(str(b) for b in bindus) + " |")
        lines.append("")

    md = Markdown("\n".join(lines))
    console.print(md)


@main.command(name="kp")
@click.option("--name", required=True, help="Full name")
@click.option("--dob", required=True, help="Date of birth (DD/MM/YYYY)")
@click.option("--tob", required=True, help="Time of birth (HH:MM)")
@click.option("--place", required=True, help="Place of birth")
def kp_cmd(name: str, dob: str, tob: str, place: str):
    """Compute KP (Krishnamurti) sub-lord positions."""
    from jyotish.compute.chart import compute_chart
    from jyotish.compute.kp import compute_kp_positions

    chart_data = compute_chart(name=name, dob=dob, tob=tob, place=place)
    positions = compute_kp_positions(chart_data)

    lines = [f"# KP Sub-Lord Positions — {name}", ""]
    lines.append("| Planet | Nakshatra | Star Lord | Sub Lord | Sub-Sub Lord |")
    lines.append("|--------|-----------|-----------|----------|--------------|")
    for p in positions:
        lines.append(f"| {p.name} | {p.nakshatra} | {p.nakshatra_lord} | {p.sub_lord} | {p.sub_sub_lord} |")

    md = Markdown("\n".join(lines))
    console.print(md)


@main.command(name="predictions")
@click.option("--category", default=None, help="Filter by category")
def predictions_cmd(category: str):
    """Show prediction accuracy dashboard."""
    from jyotish.learn.prediction_tracker import PredictionTracker

    tracker = PredictionTracker()
    dashboard = tracker.get_accuracy_dashboard()
    tracker.close()

    lines = ["# Prediction Accuracy Dashboard", ""]
    lines.append(f"**Total predictions:** {dashboard['total_predictions']}")
    lines.append(f"**Pending:** {dashboard['pending']}")
    lines.append(f"**Overall accuracy:** {dashboard['overall_accuracy']}%")
    lines.append("")

    if dashboard["categories"]:
        lines.append("| Category | Confirmed | Total Decided | Accuracy |")
        lines.append("|----------|-----------|---------------|----------|")
        for cat, data in dashboard["categories"].items():
            if category and cat != category:
                continue
            lines.append(f"| {cat} | {data['confirmed']} | {data['total_decided']} | {data['accuracy']}% |")
    else:
        lines.append("No decided predictions yet.")

    md = Markdown("\n".join(lines))
    console.print(md)


if __name__ == "__main__":
    main()
