"""6-layer validation pipeline for Pandit Ji corrections.

Validates corrections through format, scripture, computation consistency,
safety, cross-reference, and trust layers before they can be accepted
into the learning system.

Source: ADR in docs/architecture/decisions.md — 6-layer validation design.
"""

from __future__ import annotations

import logging
import re

from pydantic import BaseModel, ConfigDict, Field

from daivai_engine.constants.signs import SIGNS
from daivai_engine.models.chart import ChartData
from daivai_products.plugins.pandit.trust import (
    _DEFAULT_MIN_TRUST,
    _VALID_SCRIPTURE_PREFIXES,
    compute_trust_score,
)
from daivai_products.store.corrections import PanditCorrection, PanditCorrectionStore


logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Result of the 6-layer validation pipeline for a correction."""

    model_config = ConfigDict(frozen=True)

    is_valid: bool
    passed_layers: list[int]  # e.g. [1, 2, 3, 4, 5, 6]
    failed_layer: int | None  # None if all passed
    failure_reason: str
    trust_score: float = Field(ge=0.0, le=1.0)


# ── Safety patterns ────────────────────────────────────────────────────────
# Corrections that try to recommend prohibited stones for specific lagnas
_SAFETY_VIOLATIONS: list[tuple[str, str]] = [
    ("pukhraj", "mithuna"),
    ("moonga", "mithuna"),
    ("moti", "mithuna"),
    ("manikya", "mithuna"),
]

# Broader patterns — recommending maraka stones
_MARAKA_OVERRIDE_PATTERN = re.compile(
    r"(recommend|wear|should\s+wear|beneficial)\s+.*\b(maraka|2nd\s+lord|7th\s+lord)\b",
    re.IGNORECASE,
)


# ── Layer validators ───────────────────────────────────────────────────────


def _layer_1_format(correction: PanditCorrection) -> str:
    """Layer 1: Format check — required fields present and non-empty.

    Returns empty string on success, error message on failure.
    """
    missing: list[str] = []
    if not correction.category or not correction.category.strip():
        missing.append("category")
    if not correction.pandit_said or not correction.pandit_said.strip():
        missing.append("pandit_said")
    if not correction.pandit_reasoning or not correction.pandit_reasoning.strip():
        missing.append("pandit_reasoning")

    if missing:
        return f"Missing required fields: {', '.join(missing)}"
    return ""


def _layer_2_scripture(correction: PanditCorrection) -> str:
    """Layer 2: Scripture reference check — valid BPHS/Saravali/classical reference.

    Does not fail the correction outright — just flags if no scripture is cited.
    Only fails if the correction explicitly claims a scripture that is not recognised.

    Returns empty string on success, error message on failure.
    """
    reasoning = (correction.pandit_reasoning or "").lower()

    # Check for explicit but invalid scripture references
    # Pattern: "chapter X" or "Ch.X" without a recognised scripture name
    has_chapter_ref = bool(re.search(r"(chapter|ch\.)\s*\d+", reasoning))
    has_valid_source = any(prefix in reasoning for prefix in _VALID_SCRIPTURE_PREFIXES)

    if has_chapter_ref and not has_valid_source:
        return (
            "Cites a chapter reference without a recognised scripture name. "
            "Accepted sources: BPHS, Saravali, Phala Deepika, Jataka Parijata, "
            "Brihat Jataka, Uttara Kalamrita, Lal Kitab."
        )
    return ""


def _layer_3_computation(
    correction: PanditCorrection,
    chart: ChartData | None,
) -> str:
    """Layer 3: Computation consistency — correction must not contradict engine output.

    If a chart is provided, checks that claimed planetary positions match.
    Without a chart, this layer passes (benefit of the doubt).

    Returns empty string on success, error message on failure.
    """
    if chart is None:
        return ""

    text = (correction.pandit_said or "").lower()

    # Check for planet-in-sign claims that contradict the actual chart
    for planet_name, planet_data in chart.planets.items():
        p_lower = planet_name.lower()
        actual_sign = planet_data.sign.lower()
        actual_house = planet_data.house

        # Pattern: "{planet} is in {sign}" where sign differs from actual
        sign_claim = re.search(rf"\b{re.escape(p_lower)}\s+(?:is\s+)?in\s+(\w+)", text)
        if sign_claim:
            claimed = sign_claim.group(1).lower()
            # Only flag if the claim looks like a sign name and it differs
            sign_names = [s.lower() for s in SIGNS]
            if claimed in sign_names and claimed != actual_sign:
                return (
                    f"Claims {planet_name} is in {claimed.capitalize()} "
                    f"but engine shows {actual_sign.capitalize()} "
                    f"(house {actual_house})."
                )

    return ""


def _layer_4_safety(correction: PanditCorrection) -> str:
    """Layer 4: Safety check — must not recommend prohibited gemstones.

    Returns empty string on success, error message on failure.
    """
    text = (correction.pandit_said or "").lower()
    lagna = (correction.lagna or "").lower()

    # Check specific stone+lagna combinations
    for stone, forbidden_lagna in _SAFETY_VIOLATIONS:
        if stone in text and (lagna == forbidden_lagna or forbidden_lagna in text):
            # Only flag if text recommends the stone (not if it warns against it)
            recommend_pattern = re.compile(
                rf"(recommend|wear|should\s+wear|beneficial|good)\b.*\b{re.escape(stone)}\b",
                re.IGNORECASE,
            )
            avoid_pattern = re.compile(
                rf"(avoid|never|prohibited|harmful)\b.*\b{re.escape(stone)}\b",
                re.IGNORECASE,
            )
            if recommend_pattern.search(text) and not avoid_pattern.search(text):
                return (
                    f"SAFETY VIOLATION: Recommends {stone.capitalize()} "
                    f"for {forbidden_lagna.capitalize()} lagna, which is prohibited."
                )

    # Check maraka override pattern
    if _MARAKA_OVERRIDE_PATTERN.search(text):
        return "SAFETY VIOLATION: Attempts to override maraka stone prohibition."

    return ""


def _layer_5_cross_reference(
    correction: PanditCorrection,
    store: PanditCorrectionStore | None,
) -> str:
    """Layer 5: Cross-reference check — look for conflicting corrections.

    If an existing validated correction on the same topic directly contradicts
    this one, flag it for review.

    Returns empty string on success, error message on failure.
    """
    if store is None:
        return ""

    existing = store.list_corrections(
        status="validated",
        category=correction.category,
    )

    new_text = (correction.pandit_said or "").lower()[:100]
    new_words = set(new_text.split())

    for ex in existing:
        if ex.id == correction.id:
            continue
        if ex.chart_name and ex.chart_name != correction.chart_name:
            continue

        ex_text = (ex.pandit_said or "").lower()[:100]
        ex_words = set(ex_text.split())

        # High overlap but different conclusion suggests contradiction
        if new_words and ex_words:
            overlap = len(new_words & ex_words) / max(len(new_words), 1)
            if overlap > 0.6:
                # Check for opposing sentiment
                new_positive = any(w in new_text for w in ("recommend", "wear", "good", "benefic"))
                ex_positive = any(w in ex_text for w in ("recommend", "wear", "good", "benefic"))
                new_negative = any(
                    w in new_text for w in ("avoid", "never", "harmful", "prohibited")
                )
                ex_negative = any(w in ex_text for w in ("avoid", "never", "harmful", "prohibited"))

                if (new_positive and ex_negative) or (new_negative and ex_positive):
                    return (
                        f"Contradicts validated correction [{ex.id}]: "
                        f"'{ex.pandit_said[:50]}...'. "
                        f"Review both before accepting."
                    )

    return ""


def _layer_6_trust(
    correction: PanditCorrection,
    all_corrections: list[PanditCorrection],
    min_trust: float,
) -> tuple[str, float]:
    """Layer 6: Trust threshold check.

    Returns (error_string, trust_score). Error is empty if trust meets threshold.
    """
    trust = compute_trust_score(correction, all_corrections=all_corrections)
    if trust.trust_score < min_trust:
        return (
            f"Trust score {trust.trust_score:.2f} below threshold {min_trust:.2f}. "
            f"Factors: {'; '.join(trust.factors)}",
            trust.trust_score,
        )
    return "", trust.trust_score


# ── Public API ─────────────────────────────────────────────────────────────


def validate_correction(
    correction: PanditCorrection,
    chart: ChartData | None = None,
    store: PanditCorrectionStore | None = None,
    min_trust: float = _DEFAULT_MIN_TRUST,
) -> ValidationResult:
    """Run 6-layer validation: format → scripture → computation → safety → cross-ref → trust."""
    passed: list[int] = []
    all_corrections: list[PanditCorrection] = []
    if store is not None:
        all_corrections = store.list_corrections()

    def _fail(layer: int, reason: str, score: float | None = None) -> ValidationResult:
        ts = (
            score
            if score is not None
            else compute_trust_score(correction, all_corrections).trust_score
        )
        return ValidationResult(
            is_valid=False,
            passed_layers=list(passed),
            failed_layer=layer,
            failure_reason=reason,
            trust_score=ts,
        )

    # Layers 1-5: sequential checks
    checks: list[tuple[int, str]] = [
        (1, _layer_1_format(correction)),
        (2, _layer_2_scripture(correction)),
        (3, _layer_3_computation(correction, chart)),
        (4, _layer_4_safety(correction)),
        (5, _layer_5_cross_reference(correction, store)),
    ]
    for layer_num, err in checks:
        if err:
            return _fail(layer_num, err)
        passed.append(layer_num)

    # Layer 6: Trust threshold
    err, trust_score = _layer_6_trust(correction, all_corrections, min_trust)
    if err:
        return _fail(6, err, trust_score)
    passed.append(6)

    return ValidationResult(
        is_valid=True,
        passed_layers=passed,
        failed_layer=None,
        failure_reason="",
        trust_score=trust_score,
    )
