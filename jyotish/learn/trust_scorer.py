"""Per-source trust scoring for Pandit Ji corrections.

Tracks each pandit's accuracy over time to weight their corrections.
Levels: MASTER (0.8+), TRUSTED (0.6+), LEARNING (0.3+), UNVERIFIED (<0.3)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

from jyotish.config import get as cfg_get
from jyotish.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PanditTrustScore:
    """Trust score for a pandit source."""
    pandit_name: str
    total_corrections: int = 0
    validated_count: int = 0
    disputed_count: int = 0
    accuracy: float = 0.0         # validated / (validated + disputed)
    trust_score: float = 0.3      # 0.0 to 1.0
    trust_level: str = "UNVERIFIED"  # MASTER, TRUSTED, LEARNING, UNVERIFIED
    categories: dict[str, int] = field(default_factory=dict)  # category -> count

    def update_level(self) -> None:
        """Recalculate trust level from accuracy and volume."""
        if self.total_corrections == 0:
            self.trust_level = "UNVERIFIED"
            self.trust_score = 0.3
            return

        decided = self.validated_count + self.disputed_count
        if decided > 0:
            self.accuracy = self.validated_count / decided
        else:
            self.accuracy = 0.5  # No decisions yet

        # Trust score = weighted combination of accuracy and volume
        volume_factor = min(1.0, self.total_corrections / 20.0)
        self.trust_score = round(self.accuracy * 0.7 + volume_factor * 0.3, 3)

        if self.trust_score >= 0.8 and self.total_corrections >= 10:
            self.trust_level = "MASTER"
        elif self.trust_score >= 0.6:
            self.trust_level = "TRUSTED"
        elif self.trust_score >= 0.3:
            self.trust_level = "LEARNING"
        else:
            self.trust_level = "UNVERIFIED"


class TrustScorer:
    """Manages trust scores for all pandit sources."""

    def __init__(self, data_dir: str | Path | None = None):
        if data_dir is None:
            data_dir = cfg_get("learning.data_dir", "data/pandit_corrections")
        self._dir = Path(data_dir)
        self._scores_path = self._dir / "trust_scores.json"
        self._scores: dict[str, PanditTrustScore] = {}
        self._load()

    def _load(self) -> None:
        """Load trust scores from disk."""
        if self._scores_path.exists():
            try:
                with open(self._scores_path) as f:
                    data = json.load(f)
                for name, score_data in data.items():
                    self._scores[name] = PanditTrustScore(**score_data)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Could not load trust scores, starting fresh")

    def _save(self) -> None:
        """Save trust scores to disk."""
        self._dir.mkdir(parents=True, exist_ok=True)
        with open(self._scores_path, "w") as f:
            json.dump({n: asdict(s) for n, s in self._scores.items()}, f, indent=2)

    def get_score(self, pandit_name: str) -> PanditTrustScore:
        """Get trust score for a pandit. Creates if not exists."""
        if pandit_name not in self._scores:
            self._scores[pandit_name] = PanditTrustScore(pandit_name=pandit_name)
        return self._scores[pandit_name]

    def record_correction(self, pandit_name: str, category: str = "general") -> None:
        """Record that a pandit submitted a correction."""
        score = self.get_score(pandit_name)
        score.total_corrections += 1
        score.categories[category] = score.categories.get(category, 0) + 1
        score.update_level()
        self._save()

    def record_validation(self, pandit_name: str) -> None:
        """Record that a pandit's correction was validated."""
        score = self.get_score(pandit_name)
        score.validated_count += 1
        score.update_level()
        self._save()

    def record_dispute(self, pandit_name: str) -> None:
        """Record that a pandit's correction was disputed."""
        score = self.get_score(pandit_name)
        score.disputed_count += 1
        score.update_level()
        self._save()

    def get_all_scores(self) -> list[PanditTrustScore]:
        """Get all pandit trust scores sorted by trust_score descending."""
        return sorted(self._scores.values(), key=lambda s: s.trust_score, reverse=True)

    def get_weight(self, pandit_name: str) -> float:
        """Get the confidence weight for a pandit's corrections.

        Used to weight corrections when extracting rules.
        """
        score = self.get_score(pandit_name)
        return score.trust_score
