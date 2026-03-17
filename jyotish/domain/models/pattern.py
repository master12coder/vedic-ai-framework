"""Domain model for statistical pattern analysis results."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PatternResult:
    """Represents a statistical pattern discovered from life events data.

    Captures the correlation between an astrological factor (planet-house
    placement, yoga presence, dasha period, or remedy) and observed life
    outcomes across multiple charts.

    Attributes:
        pattern_type: Category of pattern — one of planet_house, yoga_outcome,
            dasha_event, or remedy_effectiveness.
        description: Human-readable summary, e.g. "Jupiter in 12th house".
        sample_size: Total number of events matching this pattern.
        positive_count: Events with a positive outcome.
        negative_count: Events with a negative outcome.
        neutral_count: Events with a neutral or unspecified outcome.
        confidence: Statistical confidence from 0.0 to 1.0, based on sample
            size and outcome consistency.
        details: Detailed breakdown text for reporting.
    """

    pattern_type: str
    description: str
    sample_size: int
    positive_count: int
    negative_count: int
    neutral_count: int
    confidence: float
    details: str

    @property
    def positive_rate(self) -> float:
        """Fraction of events that were positive (0.0 to 1.0)."""
        return self.positive_count / self.sample_size if self.sample_size > 0 else 0.0

    @property
    def negative_rate(self) -> float:
        """Fraction of events that were negative (0.0 to 1.0)."""
        return self.negative_count / self.sample_size if self.sample_size > 0 else 0.0

    @property
    def dominant_outcome(self) -> str:
        """Return the most common outcome label."""
        counts = {
            "positive": self.positive_count,
            "negative": self.negative_count,
            "neutral": self.neutral_count,
        }
        return max(counts, key=counts.get)  # type: ignore[arg-type]
