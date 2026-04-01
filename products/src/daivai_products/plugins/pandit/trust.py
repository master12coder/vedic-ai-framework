"""Trust scoring system for Pandit Ji corrections.

Computes a 0.0-1.0 trust score per correction based on six weighted factors:
source authority, scripture citation, multi-pandit consensus, rule contradiction,
age (time-tested), and complaint-free application. The scores are used by the
validation pipeline and the learning system to decide which corrections to
inject into LLM prompts.

Source: ADR in docs/architecture/decisions.md — 6-layer validation design.
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from daivai_products.store.corrections import PanditCorrection


logger = logging.getLogger(__name__)

# ── Known scripture references (prefixes accepted as valid) ────────────────
_VALID_SCRIPTURE_PREFIXES = (
    "bphs",
    "saravali",
    "phala deepika",
    "jataka parijata",
    "brihat jataka",
    "hora shastra",
    "phaladeepika",
    "uttara kalamrita",
    "lal kitab",
    "chamatkar chintamani",
    "brihajjataka",
)

# ── Senior pandit names (configurable — in production this comes from DB) ──
_SENIOR_PANDITS: frozenset[str] = frozenset(
    {
        "pandit_senior",
        "guru",
        "acharya",
    }
)

# ── Weight constants ───────────────────────────────────────────────────────
_W_SOURCE_AUTHORITY = 0.15
_W_SCRIPTURE_CITATION = 0.20
_W_MULTI_PANDIT = 0.15
_W_NO_CONTRADICTION = 0.20
_W_AGE_TESTED = 0.15
_W_COMPLAINT_FREE = 0.15

# Thresholds
_AGE_DAYS_FOR_FULL_SCORE = 180  # 6 months of field testing
_DEFAULT_MIN_TRUST = 0.5


class CorrectionTrust(BaseModel):
    """Trust assessment for a single Pandit Ji correction."""

    model_config = ConfigDict(frozen=True)

    correction_id: str
    trust_score: float = Field(ge=0.0, le=1.0)
    verification_count: int = Field(ge=0)
    factors: list[str]


def _has_scripture_citation(correction: PanditCorrection) -> bool:
    """Check if the correction reasoning cites a recognised scripture."""
    text = (correction.pandit_reasoning or "").lower()
    return any(prefix in text for prefix in _VALID_SCRIPTURE_PREFIXES)


def _is_senior_source(correction: PanditCorrection) -> bool:
    """Check if the correction comes from a senior/trusted pandit."""
    name = (correction.pandit_name or "").lower().strip()
    return any(tag in name for tag in _SENIOR_PANDITS)


def _age_days(correction: PanditCorrection) -> int:
    """Days since the correction was created."""
    try:
        created = datetime.strptime(correction.date, "%Y-%m-%d").date()
        return max(0, (date.today() - created).days)
    except (ValueError, TypeError):
        return 0


def _count_agreements(
    correction: PanditCorrection,
    all_corrections: list[PanditCorrection],
) -> int:
    """Count how many other corrections agree on the same topic.

    Agreement = same category + same chart_name + similar pandit_said.
    """
    count = 0
    target = (correction.pandit_said or "").lower()[:60]
    for other in all_corrections:
        if other.id == correction.id:
            continue
        if other.category != correction.category:
            continue
        if other.chart_name != correction.chart_name:
            continue
        other_text = (other.pandit_said or "").lower()[:60]
        # Simple overlap check (>50% shared words)
        target_words = set(target.split())
        other_words = set(other_text.split())
        if target_words and other_words:
            overlap = len(target_words & other_words) / max(len(target_words), 1)
            if overlap > 0.5:
                count += 1
    return count


def _contradicts_established_rules(correction: PanditCorrection) -> bool:
    """Check if the correction contradicts known safety rules.

    Currently checks for attempts to override prohibited gemstone rules.
    """
    text = (correction.pandit_said or "").lower()
    # Flag if correction tries to recommend stones known to be dangerous
    danger_patterns = [
        r"pukhraj.*mithuna.*recommend",
        r"moonga.*mithuna.*recommend",
        r"moti.*mithuna.*recommend",
        r"recommend.*maraka.*stone",
    ]
    return any(re.search(pattern, text) for pattern in danger_patterns)


def compute_trust_score(
    correction: PanditCorrection,
    all_corrections: list[PanditCorrection] | None = None,
) -> CorrectionTrust:
    """Compute trust score for a single correction.

    Factors (weights sum to 1.0):
    - Source authority: senior pandit = +0.15
    - Scripture citation: valid BPHS/Saravali reference = +0.20
    - Multi-pandit consensus: +0.15 per additional agreement (capped)
    - No contradiction with established rules: +0.20
    - Age tested: older corrections = more trusted (up to +0.15)
    - Complaint-free: validated status = +0.15

    Args:
        correction: The correction to evaluate.
        all_corrections: All corrections for consensus check (optional).

    Returns:
        CorrectionTrust with score and factor breakdown.
    """
    if all_corrections is None:
        all_corrections = []

    score = 0.0
    factors: list[str] = []

    # Factor 1: Source authority
    if _is_senior_source(correction):
        score += _W_SOURCE_AUTHORITY
        factors.append(f"Senior pandit source (+{_W_SOURCE_AUTHORITY})")

    # Factor 2: Scripture citation
    if _has_scripture_citation(correction):
        score += _W_SCRIPTURE_CITATION
        factors.append(f"Scripture citation provided (+{_W_SCRIPTURE_CITATION})")

    # Factor 3: Multi-pandit consensus
    agreements = _count_agreements(correction, all_corrections)
    if agreements > 0:
        consensus_score = min(agreements * 0.15, _W_MULTI_PANDIT)
        score += consensus_score
        factors.append(f"{agreements} pandit(s) agree (+{consensus_score:.2f})")

    # Factor 4: No contradiction with safety rules
    if not _contradicts_established_rules(correction):
        score += _W_NO_CONTRADICTION
        factors.append(f"No safety rule contradiction (+{_W_NO_CONTRADICTION})")
    else:
        factors.append("CONTRADICTS established safety rules (-0.0)")

    # Factor 5: Age tested
    age = _age_days(correction)
    age_ratio = min(age / _AGE_DAYS_FOR_FULL_SCORE, 1.0)
    age_score = age_ratio * _W_AGE_TESTED
    score += age_score
    factors.append(f"Age: {age} days, score +{age_score:.2f}")

    # Factor 6: Complaint-free (validated status)
    if correction.status == "validated":
        score += _W_COMPLAINT_FREE
        factors.append(f"Validated status (+{_W_COMPLAINT_FREE})")
    elif correction.status == "learned":
        score += _W_COMPLAINT_FREE
        factors.append(f"Learned status (+{_W_COMPLAINT_FREE})")

    score = max(0.0, min(1.0, score))

    return CorrectionTrust(
        correction_id=correction.id,
        trust_score=round(score, 4),
        verification_count=agreements,
        factors=factors,
    )


def get_trusted_corrections(
    corrections: list[PanditCorrection],
    min_trust: float = _DEFAULT_MIN_TRUST,
) -> list[PanditCorrection]:
    """Filter corrections by minimum trust threshold.

    Computes trust scores for all corrections and returns only those
    that meet or exceed the threshold, sorted by trust score descending.

    Args:
        corrections: List of corrections to evaluate.
        min_trust: Minimum trust score (0.0-1.0) to include.

    Returns:
        Filtered and sorted list of corrections.
    """
    scored: list[tuple[float, PanditCorrection]] = []
    for correction in corrections:
        trust = compute_trust_score(correction, all_corrections=corrections)
        if trust.trust_score >= min_trust:
            scored.append((trust.trust_score, correction))

    scored.sort(key=lambda t: t[0], reverse=True)
    return [c for _, c in scored]
