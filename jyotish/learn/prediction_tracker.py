"""Track prediction outcomes — accuracy dashboard by category.

Logs every prediction with confidence score, tracks outcomes:
confirmed / not_occurred / opposite / pending.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from jyotish.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Prediction:
    """A prediction record."""
    id: int | None = None
    chart_id: int | None = None
    prediction_date: str = ""
    category: str = ""          # career, health, marriage, finance, education
    prediction: str = ""
    confidence: float = 0.5
    dasha_lord: str = ""
    outcome: str = "pending"    # pending, confirmed, not_occurred, opposite
    outcome_date: str = ""
    notes: str = ""
    created_at: str = ""


class PredictionTracker:
    """Track and analyze prediction outcomes."""

    def __init__(self, db_path: str | Path = "data/life_events.db"):
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._path))
        self._conn.row_factory = sqlite3.Row
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create predictions table if it doesn't exist."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chart_id INTEGER,
                prediction_date TEXT NOT NULL,
                category TEXT NOT NULL,
                prediction TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                dasha_lord TEXT DEFAULT '',
                outcome TEXT DEFAULT 'pending',
                outcome_date TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._conn.commit()

    def log_prediction(self, prediction: Prediction) -> int:
        """Log a new prediction. Returns prediction ID."""
        cursor = self._conn.execute(
            "INSERT INTO predictions (chart_id, prediction_date, category, prediction, "
            "confidence, dasha_lord, outcome, outcome_date, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (prediction.chart_id, prediction.prediction_date, prediction.category,
             prediction.prediction, prediction.confidence, prediction.dasha_lord,
             prediction.outcome, prediction.outcome_date, prediction.notes),
        )
        self._conn.commit()
        logger.info("Prediction logged", extra={
            "id": cursor.lastrowid, "category": prediction.category,
        })
        return cursor.lastrowid  # type: ignore[return-value]

    def update_outcome(
        self, prediction_id: int, outcome: str, outcome_date: str = "", notes: str = "",
    ) -> None:
        """Update a prediction's outcome.

        Args:
            prediction_id: The prediction to update
            outcome: confirmed, not_occurred, opposite
            outcome_date: When the outcome was observed
            notes: Additional notes
        """
        if outcome not in ("confirmed", "not_occurred", "opposite", "pending"):
            raise ValueError(f"Invalid outcome: {outcome}")
        if not outcome_date:
            outcome_date = datetime.now().strftime("%Y-%m-%d")
        self._conn.execute(
            "UPDATE predictions SET outcome = ?, outcome_date = ?, notes = ? WHERE id = ?",
            (outcome, outcome_date, notes, prediction_id),
        )
        self._conn.commit()

    def get_predictions(
        self, chart_id: int | None = None, category: str | None = None,
        outcome: str | None = None,
    ) -> list[Prediction]:
        """Get predictions with optional filters."""
        query = "SELECT * FROM predictions WHERE 1=1"
        params: list[Any] = []
        if chart_id is not None:
            query += " AND chart_id = ?"
            params.append(chart_id)
        if category:
            query += " AND category = ?"
            params.append(category)
        if outcome:
            query += " AND outcome = ?"
            params.append(outcome)
        query += " ORDER BY prediction_date DESC"

        rows = self._conn.execute(query, params).fetchall()
        return [Prediction(**dict(r)) for r in rows]

    def get_accuracy_dashboard(self) -> dict[str, Any]:
        """Get accuracy statistics across all predictions.

        Returns:
            Dict with per-category accuracy rates and overall stats.
        """
        rows = self._conn.execute(
            "SELECT category, outcome, COUNT(*) as cnt FROM predictions "
            "WHERE outcome != 'pending' GROUP BY category, outcome"
        ).fetchall()

        categories: dict[str, dict[str, int]] = {}
        for r in rows:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = {"confirmed": 0, "not_occurred": 0, "opposite": 0}
            categories[cat][r["outcome"]] = r["cnt"]

        dashboard: dict[str, Any] = {"categories": {}}
        total_confirmed = 0
        total_decided = 0

        for cat, counts in categories.items():
            confirmed = counts.get("confirmed", 0)
            decided = confirmed + counts.get("not_occurred", 0) + counts.get("opposite", 0)
            accuracy = confirmed / decided if decided > 0 else 0.0
            dashboard["categories"][cat] = {
                "confirmed": confirmed,
                "total_decided": decided,
                "accuracy": round(accuracy * 100, 1),
            }
            total_confirmed += confirmed
            total_decided += decided

        dashboard["overall_accuracy"] = (
            round(total_confirmed / total_decided * 100, 1) if total_decided > 0 else 0.0
        )
        dashboard["total_predictions"] = self._conn.execute(
            "SELECT COUNT(*) FROM predictions"
        ).fetchone()[0]
        dashboard["pending"] = self._conn.execute(
            "SELECT COUNT(*) FROM predictions WHERE outcome = 'pending'"
        ).fetchone()[0]

        return dashboard

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
