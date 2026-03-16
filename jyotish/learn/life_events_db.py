"""SQLite-based life events database — zero external dependencies.

Stores charts, life events, and enables pattern matching across charts.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from jyotish.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class LifeEvent:
    """A life event record."""
    id: int | None = None
    chart_id: int | None = None
    event_date: str = ""
    event_type: str = ""      # marriage, career, health, child, education, property
    description: str = ""
    dasha_lord: str = ""      # MD running at event time
    antardasha_lord: str = ""  # AD running at event time
    houses_involved: str = "" # Comma-separated house numbers
    planets_involved: str = "" # Comma-separated planet names
    outcome: str = ""         # positive, negative, neutral
    created_at: str = ""


@dataclass
class ChartRecord:
    """A chart record in the database."""
    id: int | None = None
    name: str = ""
    dob: str = ""
    tob: str = ""
    place: str = ""
    lagna: str = ""
    moon_sign: str = ""
    moon_nakshatra: str = ""
    gender: str = ""
    is_anonymous: bool = False
    created_at: str = ""


class LifeEventsDB:
    """SQLite database for life events and charts."""

    def __init__(self, db_path: str | Path = "data/life_events.db"):
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        """Create tables if they don't exist."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS charts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                dob TEXT NOT NULL,
                tob TEXT NOT NULL,
                place TEXT DEFAULT '',
                lagna TEXT DEFAULT '',
                moon_sign TEXT DEFAULT '',
                moon_nakshatra TEXT DEFAULT '',
                gender TEXT DEFAULT '',
                is_anonymous INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chart_id INTEGER NOT NULL,
                event_date TEXT NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT DEFAULT '',
                dasha_lord TEXT DEFAULT '',
                antardasha_lord TEXT DEFAULT '',
                houses_involved TEXT DEFAULT '',
                planets_involved TEXT DEFAULT '',
                outcome TEXT DEFAULT 'neutral',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chart_id) REFERENCES charts(id)
            );

            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chart_id INTEGER NOT NULL,
                prediction_date TEXT NOT NULL,
                category TEXT NOT NULL,
                prediction TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                dasha_lord TEXT DEFAULT '',
                outcome TEXT DEFAULT 'pending',
                outcome_date TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chart_id) REFERENCES charts(id)
            );

            CREATE INDEX IF NOT EXISTS idx_events_chart ON events(chart_id);
            CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
            CREATE INDEX IF NOT EXISTS idx_predictions_chart ON predictions(chart_id);
        """)
        self._conn.commit()

    def add_chart(self, chart: ChartRecord) -> int:
        """Add a chart and return its ID."""
        cursor = self._conn.execute(
            "INSERT INTO charts (name, dob, tob, place, lagna, moon_sign, moon_nakshatra, gender, is_anonymous) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (chart.name, chart.dob, chart.tob, chart.place, chart.lagna,
             chart.moon_sign, chart.moon_nakshatra, chart.gender, int(chart.is_anonymous)),
        )
        self._conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def add_event(self, event: LifeEvent) -> int:
        """Add a life event and return its ID."""
        cursor = self._conn.execute(
            "INSERT INTO events (chart_id, event_date, event_type, description, "
            "dasha_lord, antardasha_lord, houses_involved, planets_involved, outcome) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (event.chart_id, event.event_date, event.event_type, event.description,
             event.dasha_lord, event.antardasha_lord, event.houses_involved,
             event.planets_involved, event.outcome),
        )
        self._conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def get_events(self, chart_id: int) -> list[LifeEvent]:
        """Get all events for a chart."""
        rows = self._conn.execute(
            "SELECT * FROM events WHERE chart_id = ? ORDER BY event_date", (chart_id,)
        ).fetchall()
        return [LifeEvent(**dict(r)) for r in rows]

    def find_similar_events(
        self, event_type: str, dasha_lord: str = "", limit: int = 20,
    ) -> list[LifeEvent]:
        """Find similar events across all charts for pattern matching."""
        if dasha_lord:
            rows = self._conn.execute(
                "SELECT * FROM events WHERE event_type = ? AND dasha_lord = ? "
                "ORDER BY event_date DESC LIMIT ?",
                (event_type, dasha_lord, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM events WHERE event_type = ? "
                "ORDER BY event_date DESC LIMIT ?",
                (event_type, limit),
            ).fetchall()
        return [LifeEvent(**dict(r)) for r in rows]

    def get_pattern_stats(self, event_type: str) -> dict[str, Any]:
        """Get statistics for an event type across all charts.

        Returns:
            Dict with dasha_distribution, house_distribution, outcome_distribution.
        """
        rows = self._conn.execute(
            "SELECT dasha_lord, outcome, COUNT(*) as cnt FROM events "
            "WHERE event_type = ? GROUP BY dasha_lord, outcome",
            (event_type,),
        ).fetchall()

        dasha_dist: dict[str, int] = {}
        outcome_dist: dict[str, int] = {}
        for r in rows:
            dl = r["dasha_lord"] or "Unknown"
            out = r["outcome"] or "neutral"
            dasha_dist[dl] = dasha_dist.get(dl, 0) + r["cnt"]
            outcome_dist[out] = outcome_dist.get(out, 0) + r["cnt"]

        total = sum(dasha_dist.values())
        return {
            "event_type": event_type,
            "total_events": total,
            "dasha_distribution": dasha_dist,
            "outcome_distribution": outcome_dist,
        }

    def get_chart(self, chart_id: int) -> ChartRecord | None:
        """Get a chart by ID."""
        row = self._conn.execute(
            "SELECT * FROM charts WHERE id = ?", (chart_id,)
        ).fetchone()
        if row:
            return ChartRecord(**dict(row))
        return None

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def __del__(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass
