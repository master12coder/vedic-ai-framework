"""6-layer validation pipeline for Pandit Ji corrections.

Layers:
1. Astronomical fact check — auto-reject if contradicts computation
2. Scripture cross-reference — flag if contradicts BPHS
3. Life event validation — strongest real-world evidence
4. Multi-source consensus — single pandit != truth
5. Source trust scoring — per-pandit accuracy tracking
6. Fact vs interpretation separation — computation is LOCKED
"""

from __future__ import annotations

from dataclasses import dataclass

from jyotish.learn.corrections import PanditCorrection, PanditCorrectionStore
from jyotish.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    correction_id: str
    is_valid: bool
    new_status: str
    confidence_delta: float
    source: str
    layer: int            # Which validation layer (1-6)
    notes: str


@dataclass
class FullValidationReport:
    """Complete validation report across all 6 layers."""
    correction_id: str
    layer_results: list[ValidationResult]
    final_status: str     # validated, disputed, pending
    final_confidence: float
    passed_layers: int
    failed_layers: int
    skipped_layers: int


class SixLayerValidator:
    """Implements the 6-layer validation pipeline."""

    def __init__(self, store: PanditCorrectionStore | None = None):
        self._store = store or PanditCorrectionStore()

    # ── Layer 1: Astronomical Fact Check ───────────────────────────────

    def check_astronomical_facts(
        self, correction_id: str, contradicts_computation: bool,
    ) -> ValidationResult:
        """Layer 1: Auto-reject if correction contradicts computed positions.

        Computation is LOCKED — a pandit cannot override Swiss Ephemeris.
        E.g., if pandit says "Jupiter is in Aries" but computation shows Taurus.
        """
        if contradicts_computation:
            self._store.update_status(correction_id, "rejected", -0.5)
            return ValidationResult(
                correction_id=correction_id, is_valid=False,
                new_status="rejected", confidence_delta=-0.5,
                source="astronomical_check", layer=1,
                notes="REJECTED: Contradicts Swiss Ephemeris computation. Computation is locked.",
            )
        return ValidationResult(
            correction_id=correction_id, is_valid=True,
            new_status="pending", confidence_delta=0.1,
            source="astronomical_check", layer=1,
            notes="Passed: Does not contradict computation.",
        )

    # ── Layer 2: Scripture Cross-Reference ─────────────────────────────

    def check_scripture_reference(
        self, correction_id: str, aligns_with_scripture: bool | None = None,
        scripture_ref: str = "",
    ) -> ValidationResult:
        """Layer 2: Flag if correction contradicts classical texts (BPHS, etc.)."""
        if aligns_with_scripture is None:
            return ValidationResult(
                correction_id=correction_id, is_valid=True,
                new_status="pending", confidence_delta=0.0,
                source="scripture_check", layer=2,
                notes="Skipped: No scripture reference available.",
            )
        if aligns_with_scripture:
            self._store.update_status(correction_id, "pending", 0.2)
            return ValidationResult(
                correction_id=correction_id, is_valid=True,
                new_status="pending", confidence_delta=0.2,
                source="scripture_check", layer=2,
                notes=f"Supported by scripture: {scripture_ref}",
            )
        else:
            self._store.update_status(correction_id, "pending", -0.1)
            return ValidationResult(
                correction_id=correction_id, is_valid=False,
                new_status="pending", confidence_delta=-0.1,
                source="scripture_check", layer=2,
                notes=f"Contradicts scripture: {scripture_ref}. Flagged for review.",
            )

    # ── Layer 3: Life Event Validation ─────────────────────────────────

    def validate_by_life_event(
        self, correction_id: str, event_matches: bool,
        event_description: str = "",
    ) -> ValidationResult:
        """Layer 3: Strongest evidence — does real life confirm the correction?"""
        if event_matches:
            self._store.update_status(correction_id, "validated", 0.3)
            return ValidationResult(
                correction_id=correction_id, is_valid=True,
                new_status="validated", confidence_delta=0.3,
                source="life_event", layer=3,
                notes=f"Confirmed by event: {event_description}",
            )
        else:
            self._store.update_status(correction_id, "disputed", -0.2)
            return ValidationResult(
                correction_id=correction_id, is_valid=False,
                new_status="disputed", confidence_delta=-0.2,
                source="life_event", layer=3,
                notes=f"Contradicted by event: {event_description}",
            )

    # ── Layer 4: Multi-Source Consensus ────────────────────────────────

    def validate_by_second_opinion(
        self, correction_id: str, second_pandit_agrees: bool,
        pandit_name: str = "", notes: str = "",
    ) -> ValidationResult:
        """Layer 4: Single pandit is not truth — require consensus."""
        if second_pandit_agrees:
            self._store.update_status(correction_id, "validated", 0.3)
            return ValidationResult(
                correction_id=correction_id, is_valid=True,
                new_status="validated", confidence_delta=0.3,
                source=f"second_pandit:{pandit_name}", layer=4,
                notes=notes or "Second pandit agrees",
            )
        else:
            self._store.update_status(correction_id, "disputed", -0.2)
            return ValidationResult(
                correction_id=correction_id, is_valid=False,
                new_status="disputed", confidence_delta=-0.2,
                source=f"second_pandit:{pandit_name}", layer=4,
                notes=notes or "Second pandit disagrees",
            )

    # ── Layer 5: Source Trust Scoring ──────────────────────────────────

    def apply_trust_weight(
        self, correction_id: str, trust_score: float,
    ) -> ValidationResult:
        """Layer 5: Weight the correction by the pandit's trust score.

        MASTER (0.8+): +0.2 confidence
        TRUSTED (0.6+): +0.1
        LEARNING (0.3+): 0.0
        UNVERIFIED (<0.3): -0.1
        """
        if trust_score >= 0.8:
            delta = 0.2
            notes = f"MASTER-level pandit (trust={trust_score:.2f}): +0.2"
        elif trust_score >= 0.6:
            delta = 0.1
            notes = f"TRUSTED pandit (trust={trust_score:.2f}): +0.1"
        elif trust_score >= 0.3:
            delta = 0.0
            notes = f"LEARNING pandit (trust={trust_score:.2f}): no weight change"
        else:
            delta = -0.1
            notes = f"UNVERIFIED pandit (trust={trust_score:.2f}): -0.1"

        self._store.update_status(correction_id, "pending", delta)
        return ValidationResult(
            correction_id=correction_id, is_valid=delta >= 0,
            new_status="pending", confidence_delta=delta,
            source="trust_scoring", layer=5,
            notes=notes,
        )

    # ── Layer 6: Fact vs Interpretation ────────────────────────────────

    def check_fact_vs_interpretation(
        self, correction_id: str, is_computation_override: bool,
    ) -> ValidationResult:
        """Layer 6: Ensure corrections don't try to override computation.

        Corrections can override INTERPRETATION (e.g., 'Jupiter in 7th means X')
        but NEVER computation (e.g., 'Jupiter is actually in 8th house').
        """
        if is_computation_override:
            self._store.update_status(correction_id, "rejected", -1.0)
            return ValidationResult(
                correction_id=correction_id, is_valid=False,
                new_status="rejected", confidence_delta=-1.0,
                source="fact_interpretation_check", layer=6,
                notes="REJECTED: Cannot override computed planetary positions.",
            )
        return ValidationResult(
            correction_id=correction_id, is_valid=True,
            new_status="pending", confidence_delta=0.0,
            source="fact_interpretation_check", layer=6,
            notes="Passed: Correction is about interpretation, not computation.",
        )

    # ── Full Pipeline ──────────────────────────────────────────────────

    def validate_by_computation(
        self, correction_id: str, computation_agrees: bool,
        notes: str = "",
    ) -> ValidationResult:
        """Backward-compatible: validate using computational verification."""
        if computation_agrees:
            self._store.update_status(correction_id, "validated", 0.2)
            return ValidationResult(
                correction_id=correction_id, is_valid=True,
                new_status="validated", confidence_delta=0.2,
                source="computation", layer=1,
                notes=notes or "Computational verification passed",
            )
        else:
            self._store.update_status(correction_id, "disputed", -0.1)
            return ValidationResult(
                correction_id=correction_id, is_valid=False,
                new_status="disputed", confidence_delta=-0.1,
                source="computation", layer=1,
                notes=notes or "Computational verification failed",
            )

    def get_validation_summary(self) -> dict[str, int]:
        """Get a summary of validation status across all corrections."""
        return self._store.get_stats()


# Backward-compatible alias
MultiSourceValidator = SixLayerValidator
