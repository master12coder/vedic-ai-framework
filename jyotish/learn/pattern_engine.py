"""Statistical pattern engine — discovers correlations in life events data.

Queries the SQLite life-events database and computes statistical patterns
linking planetary placements, yogas, dasha periods, and remedies to outcomes.
"""

from __future__ import annotations

import math
import sqlite3
from pathlib import Path

from jyotish.domain.models.pattern import PatternResult
from jyotish.utils.logging_config import get_logger

logger = get_logger(__name__)
DEFAULT_MIN_SAMPLE = 3


def _connect(db_path: str) -> sqlite3.Connection:
    """Open a connection to the life events database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _compute_confidence(sample_size: int, dominant_count: int) -> float:
    """Compute confidence (0.0-1.0) from outcome consistency and sample size."""
    if sample_size == 0:
        return 0.0
    consistency = dominant_count / sample_size
    size_factor = min(1.0, math.log2(sample_size + 1) / math.log2(31))
    return round(consistency * size_factor, 3)


def _tally_outcomes(rows: list[sqlite3.Row]) -> tuple[int, int, int]:
    """Count positive, negative, and neutral outcomes from rows."""
    pos = neg = neu = 0
    for r in rows:
        outcome = (r["outcome"] or "neutral").lower()
        if outcome == "positive":
            pos += 1
        elif outcome == "negative":
            neg += 1
        else:
            neu += 1
    return pos, neg, neu


def _build_result(
    rows: list[sqlite3.Row], pattern_type: str, description: str, min_sample: int,
) -> PatternResult | None:
    """Build a PatternResult from query rows, or None if below min_sample."""
    if len(rows) < min_sample:
        return None
    pos, neg, neu = _tally_outcomes(rows)
    return PatternResult(
        pattern_type=pattern_type, description=description,
        sample_size=len(rows), positive_count=pos, negative_count=neg, neutral_count=neu,
        confidence=_compute_confidence(len(rows), max(pos, neg, neu)),
        details=f"{description}: {pos} positive, {neg} negative, {neu} neutral out of {len(rows)} events",
    )


def _query_and_build(
    db_path: str, sql: str, params: tuple[str, ...],
    pattern_type: str, description: str, min_sample: int,
) -> PatternResult | None:
    """Execute a query and build a PatternResult from matching rows."""
    conn = _connect(db_path)
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return _build_result(rows, pattern_type, description, min_sample)


def _parse_csv_field(rows: list[sqlite3.Row], column: str) -> set[str]:
    """Extract unique values from a comma-separated column across rows."""
    values: set[str] = set()
    for r in rows:
        for item in r[column].split(","):
            stripped = item.strip()
            if stripped:
                values.add(stripped)
    return values


# --- Public API ---

def analyze_planet_house_patterns(
    db_path: str, planet: str, house: int, min_sample: int = DEFAULT_MIN_SAMPLE,
) -> PatternResult | None:
    """Analyse outcomes for events involving a planet in a specific house.

    Args:
        db_path: Path to the SQLite life events database.
        planet: Planet name, e.g. "Jupiter".
        house: House number 1-12.
        min_sample: Minimum events required to produce a result.
    """
    return _query_and_build(
        db_path,
        "SELECT outcome FROM events WHERE planets_involved LIKE ? AND houses_involved LIKE ?",
        (f"%{planet}%", f"%{house}%"),
        "planet_house", f"{planet} in house {house}", min_sample,
    )


def analyze_yoga_patterns(
    db_path: str, yoga_name: str, min_sample: int = DEFAULT_MIN_SAMPLE,
) -> PatternResult | None:
    """Analyse outcomes for events whose description references a yoga.

    Args:
        db_path: Path to the SQLite life events database.
        yoga_name: Yoga name, e.g. "Gajakesari".
        min_sample: Minimum events required to produce a result.
    """
    return _query_and_build(
        db_path,
        "SELECT outcome FROM events WHERE description LIKE ?",
        (f"%{yoga_name}%",),
        "yoga_outcome", f"Yoga: {yoga_name}", min_sample,
    )


def analyze_dasha_patterns(
    db_path: str, planet: str, min_sample: int = DEFAULT_MIN_SAMPLE,
) -> PatternResult | None:
    """Analyse outcomes during a planet's Mahadasha.

    Args:
        db_path: Path to the SQLite life events database.
        planet: Dasha lord name, e.g. "Jupiter".
        min_sample: Minimum events required to produce a result.
    """
    return _query_and_build(
        db_path,
        "SELECT outcome FROM events WHERE dasha_lord = ?",
        (planet,),
        "dasha_event", f"Mahadasha of {planet}", min_sample,
    )


def analyze_remedy_effectiveness(
    db_path: str, min_sample: int = DEFAULT_MIN_SAMPLE,
) -> PatternResult | None:
    """Analyse remedy-related events for overall effectiveness.

    Args:
        db_path: Path to the SQLite life events database.
        min_sample: Minimum events required to produce a result.
    """
    return _query_and_build(
        db_path,
        "SELECT outcome FROM events WHERE event_type = 'remedy'",
        (),
        "remedy_effectiveness", "Remedy effectiveness (all remedies)", min_sample,
    )


def get_all_patterns(
    db_path: str, min_sample: int = DEFAULT_MIN_SAMPLE,
) -> list[PatternResult]:
    """Discover all patterns meeting the minimum sample threshold.

    Iterates over distinct planets, houses, dasha lords, and remedy events
    found in the database and collects every qualifying pattern.

    Args:
        db_path: Path to the SQLite life events database.
        min_sample: Minimum events required per pattern.

    Returns:
        PatternResult list sorted by confidence descending.
    """
    if not Path(db_path).exists():
        logger.warning("Life events database not found at %s", db_path)
        return []

    conn = _connect(db_path)
    try:
        dasha_lords = [
            r["dasha_lord"] for r in conn.execute(
                "SELECT DISTINCT dasha_lord FROM events WHERE dasha_lord != ''"
            ).fetchall()
        ]
        planet_rows = conn.execute(
            "SELECT DISTINCT planets_involved FROM events WHERE planets_involved != ''"
        ).fetchall()
        planets = _parse_csv_field(planet_rows, "planets_involved")

        house_rows = conn.execute(
            "SELECT DISTINCT houses_involved FROM events WHERE houses_involved != ''"
        ).fetchall()
        houses = {int(h) for h in _parse_csv_field(house_rows, "houses_involved") if h.isdigit()}
    finally:
        conn.close()

    results: list[PatternResult] = []
    for planet in planets:
        for house in houses:
            result = analyze_planet_house_patterns(db_path, planet, house, min_sample)
            if result is not None:
                results.append(result)
    for lord in dasha_lords:
        result = analyze_dasha_patterns(db_path, lord, min_sample)
        if result is not None:
            results.append(result)
    remedy = analyze_remedy_effectiveness(db_path, min_sample)
    if remedy is not None:
        results.append(remedy)

    results.sort(key=lambda r: r.confidence, reverse=True)
    logger.info("Discovered %d patterns (min_sample=%d)", len(results), min_sample)
    return results


def format_pattern_report(patterns: list[PatternResult]) -> str:
    """Format patterns into a human-readable Markdown report.

    Args:
        patterns: PatternResult objects to include.

    Returns:
        Markdown string, or a "no patterns" message when empty.
    """
    if not patterns:
        return "No statistical patterns found (insufficient data)."

    lines = [
        "# Statistical Pattern Report",
        "",
        f"**Patterns discovered:** {len(patterns)}",
        "",
        "| # | Type | Description | Sample | +/- /= | Confidence |",
        "|---|------|-------------|--------|--------|------------|",
    ]
    for i, p in enumerate(patterns, 1):
        lines.append(
            f"| {i} | {p.pattern_type} | {p.description} | {p.sample_size} "
            f"| {p.positive_count}/{p.negative_count}/{p.neutral_count} "
            f"| {p.confidence:.2f} |"
        )
    lines.append("")
    lines.append("---")
    for p in patterns:
        lines.append(f"- {p.details}")
    return "\n".join(lines)
