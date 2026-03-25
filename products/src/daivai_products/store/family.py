"""Family chart management — save and load multiple charts."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import cast

from daivai_engine.compute.chart import compute_chart
from daivai_engine.models.chart import ChartData


logger = logging.getLogger(__name__)

DEFAULT_FAMILY_DIR = Path("charts")
FAMILY_INDEX = "family.json"


def _get_family_path(family_dir: Path | None = None) -> Path:
    """Get the family index file path."""
    base = family_dir or DEFAULT_FAMILY_DIR
    base.mkdir(parents=True, exist_ok=True)
    return base / FAMILY_INDEX


def add_member(
    name: str,
    dob: str,
    tob: str,
    place: str | None = None,
    gender: str = "Male",
    relation: str = "self",
    lat: float | None = None,
    lon: float | None = None,
    tz_name: str = "Asia/Kolkata",
    family_dir: Path | None = None,
) -> ChartData:
    """Add a family member — compute chart and save.

    Returns:
        Computed ChartData for the new member.
    """
    chart = compute_chart(
        name=name,
        dob=dob,
        tob=tob,
        place=place,
        gender=gender,
        lat=lat,
        lon=lon,
        tz_name=tz_name,
    )

    base = family_dir or DEFAULT_FAMILY_DIR
    base.mkdir(parents=True, exist_ok=True)

    # Save chart JSON
    slug = name.lower().replace(" ", "_")
    chart_path = base / f"{slug}.json"
    chart_path.write_text(chart.model_dump_json(indent=2))

    # Update family index
    index_path = _get_family_path(family_dir)
    index: list[dict[str, str]] = []
    if index_path.exists():
        index = json.loads(index_path.read_text())

    # Remove existing entry for same name
    index = [m for m in index if m.get("name") != name]
    index.append(
        {
            "name": name,
            "relation": relation,
            "dob": dob,
            "gender": gender,
            "chart_file": str(chart_path),
            "lagna": chart.lagna_sign,
        }
    )
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False))

    logger.info("Added family member: %s (%s) — %s", name, relation, chart.lagna_sign)
    return chart


def list_members(family_dir: Path | None = None) -> list[dict[str, str]]:
    """List all family members."""
    index_path = _get_family_path(family_dir)
    if not index_path.exists():
        return []
    result: list[dict[str, str]] = json.loads(index_path.read_text())
    return result


def load_member(name: str, family_dir: Path | None = None) -> ChartData | None:
    """Load a family member's chart by name."""
    members = list_members(family_dir)
    for m in members:
        if m["name"].lower() == name.lower():
            chart_path = Path(m["chart_file"])
            if chart_path.exists():
                return cast(ChartData, ChartData.model_validate_json(chart_path.read_text()))
    return None


def run_daily_for_all(
    family_dir: Path | None = None,
    level: str = "simple",
) -> dict[str, str]:
    """Generate daily guidance for all family members.

    Returns:
        Dict of name -> daily message.
    """
    from daivai_products.plugins.daily.engine import DailyLevel, run_daily

    try:
        dl = DailyLevel(level)
    except ValueError:
        dl = DailyLevel.SIMPLE

    results: dict[str, str] = {}
    for member in list_members(family_dir):
        chart = load_member(member["name"], family_dir)
        if chart:
            results[member["name"]] = run_daily(chart, dl)
    return results
