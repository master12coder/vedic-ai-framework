"""Pandit Ji correction store — file-based JSON storage."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from jyotish.config import get as cfg_get


@dataclass
class PanditCorrection:
    """A correction submitted by a Pandit Ji about chart interpretation."""

    id: str = ""
    pandit_name: str = ""
    date: str = ""
    chart_name: str = ""
    category: str = ""            # gemstone, house_reading, dasha, remedy, yoga, dosha
    ai_said: str = ""
    pandit_said: str = ""
    pandit_reasoning: str = ""
    correction_type: str = ""     # override, refinement, addition
    planets_involved: list[str] = field(default_factory=list)
    houses_involved: list[int] = field(default_factory=list)
    lagna: str = ""
    status: str = "pending"       # pending, validated, disputed, learned, rejected
    confidence: float = 0.0
    audio_file: str = ""
    transcript: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.date:
            self.date = datetime.now().strftime("%Y-%m-%d")


class PanditCorrectionStore:
    """File-based JSON store for pandit corrections."""

    def __init__(self, data_dir: str | Path | None = None):
        if data_dir is None:
            data_dir = cfg_get("learning.data_dir", "data/pandit_corrections")
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _correction_path(self, correction_id: str) -> Path:
        return self._dir / f"{correction_id}.json"

    def add_correction(self, correction: PanditCorrection) -> str:
        """Add a new correction. Returns the correction ID."""
        path = self._correction_path(correction.id)
        with open(path, "w") as f:
            json.dump(asdict(correction), f, indent=2, ensure_ascii=False)
        return correction.id

    def get_correction(self, correction_id: str) -> PanditCorrection | None:
        """Get a correction by ID."""
        path = self._correction_path(correction_id)
        if not path.exists():
            return None
        with open(path) as f:
            data = json.load(f)
        return PanditCorrection(**data)

    def list_corrections(
        self,
        status: str | None = None,
        category: str | None = None,
        lagna: str | None = None,
    ) -> list[PanditCorrection]:
        """List corrections with optional filters."""
        corrections = []
        for path in self._dir.glob("*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                c = PanditCorrection(**data)
                if status and c.status != status:
                    continue
                if category and c.category != category:
                    continue
                if lagna and c.lagna != lagna:
                    continue
                corrections.append(c)
            except (json.JSONDecodeError, TypeError):
                continue
        return sorted(corrections, key=lambda c: c.date, reverse=True)

    def update_status(self, correction_id: str, status: str, confidence_delta: float = 0.0) -> bool:
        """Update a correction's status and confidence."""
        correction = self.get_correction(correction_id)
        if correction is None:
            return False
        correction.status = status
        correction.confidence += confidence_delta
        correction.confidence = max(0.0, min(1.0, correction.confidence))
        self.add_correction(correction)
        return True

    def validate_correction(self, correction_id: str) -> bool:
        """Mark a correction as validated (+0.3 confidence)."""
        return self.update_status(correction_id, "validated", 0.3)

    def dispute_correction(self, correction_id: str) -> bool:
        """Mark a correction as disputed (-0.2 confidence)."""
        return self.update_status(correction_id, "disputed", -0.2)

    def get_relevant_rules(
        self,
        lagna: str | None = None,
        category: str | None = None,
        planets: list[str] | None = None,
        max_rules: int | None = None,
    ) -> list[PanditCorrection]:
        """Get validated corrections relevant to the given context."""
        if max_rules is None:
            max_rules = int(cfg_get("learning.max_rules_in_prompt", 5))

        corrections = self.list_corrections(status="validated")
        if lagna:
            corrections = [c for c in corrections if c.lagna == lagna or not c.lagna]
        if category:
            corrections = [c for c in corrections if c.category == category]
        if planets:
            corrections = [
                c for c in corrections
                if any(p in c.planets_involved for p in planets) or not c.planets_involved
            ]

        # Sort by confidence descending
        corrections.sort(key=lambda c: c.confidence, reverse=True)
        return corrections[:max_rules]

    def get_prompt_additions(
        self,
        lagna: str | None = None,
        category: str | None = None,
    ) -> str:
        """Generate text to inject into LLM prompts from learned rules."""
        rules = self.get_relevant_rules(lagna=lagna, category=category)
        if not rules:
            return ""

        lines = ["## Learned Rules from Pandit Ji"]
        for r in rules:
            lines.append(
                f"- [{r.category}] {r.pandit_said}"
                f" (Reasoning: {r.pandit_reasoning})"
                f" [Confidence: {r.confidence:.1f}]"
            )
        return "\n".join(lines)

    def get_stats(self) -> dict[str, int]:
        """Get statistics about corrections."""
        all_corrections = self.list_corrections()
        stats = {
            "total": len(all_corrections),
            "pending": 0,
            "validated": 0,
            "disputed": 0,
            "learned": 0,
            "rejected": 0,
        }
        for c in all_corrections:
            if c.status in stats:
                stats[c.status] += 1
        return stats

    def generate_comparison_table(self, chart_name: str | None = None) -> str:
        """Generate a comparison table of AI vs Pandit Ji findings."""
        corrections = self.list_corrections()
        if chart_name:
            corrections = [c for c in corrections if c.chart_name == chart_name]

        if not corrections:
            return "No corrections found."

        lines = ["| # | Category | AI Said | Pandit Said | Status | Confidence |"]
        lines.append("|---|----------|---------|-------------|--------|------------|")
        for i, c in enumerate(corrections, 1):
            lines.append(
                f"| {i} | {c.category} | {c.ai_said[:40]}... | "
                f"{c.pandit_said[:40]}... | {c.status} | {c.confidence:.1f} |"
            )
        return "\n".join(lines)
