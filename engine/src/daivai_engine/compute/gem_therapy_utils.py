"""Gem therapy shared utilities, constants, and simple helpers."""

from __future__ import annotations

from typing import Any


# ── Activation mantra count (for Pran Pratishtha ritual) ────────────────────
_ACTIVATION_MANTRA_COUNT = 108  # Standard for all planets

# ── Activation steps (common to all planets) ─────────────────────────────────
_ACTIVATION_STEPS = [
    "Purchase stone on planet's auspicious weekday",
    "Set in prescribed metal with stone touching the skin",
    "Wake before sunrise on wearing day and take a purifying bath",
    "Place ring on raw rice on a clean coloured cloth",
    "Light ghee lamp (diya) and incense appropriate to the planet",
    "Purify with panchamrit (milk, curd, honey, ghee, sugar) and wash with Gangajal",
    "Chant the planet's Vedic mantra the prescribed number of times",
    "Wear on the specified finger during the planet's hora",
    "Touch ring to forehead and offer a prayer of intention",
]

# ── Universal removal conditions ────────────────────────────────────────────
_UNIVERSAL_REMOVAL = [
    "If the stone develops a crack or chip",
    "If the stone's color changes dramatically or becomes cloudy",
    "If severe negative events occur within 3-7 days of wearing",
    "If persistent bad dreams occur for 3 or more consecutive nights",
    "If unexplained physical discomfort appears at the finger",
    "During surgery — remove all metals and stones",
    "After the planet's recommended wearing period (typically 3-7 years)",
]


def _lagna_to_key(lagna_sign: str, rules: dict[str, Any]) -> str:
    """Convert lagna sign name to knowledge key (e.g., 'Gemini' → 'mithuna')."""
    mapping: dict[str, str] = rules.get("lagna_sign_to_key", {})
    return mapping.get(lagna_sign, lagna_sign.lower())


def _get_lordship_gem_recs(lagna_key: str, lordship: dict[str, Any]) -> dict[str, Any]:
    """Extract gemstone_recommendations for the given lagna from lordship_rules."""
    lagnas: dict[str, Any] = lordship.get("lagnas", {})
    lagna_data: dict[str, Any] = lagnas.get(lagna_key, {})
    result: dict[str, Any] = lagna_data.get("gemstone_recommendations", {})
    return result


def _map_recommendation_status(recommendation: str) -> str:
    """Map lordship_rules.yaml recommendation values to canonical status strings."""
    mapping = {
        "wear": "recommended",
        "recommended": "recommended",
        "test": "test_with_caution",
        "test_with_caution": "test_with_caution",
        "avoid": "prohibited",
        "prohibited": "prohibited",
        "neutral": "neutral",
    }
    return mapping.get(recommendation.lower(), "neutral")


def _universal_removal() -> list[str]:
    """Return universal gem removal conditions."""
    return list(_UNIVERSAL_REMOVAL)


def _get_special_precaution(stone_name: str, quality_data: dict[str, Any]) -> str | None:
    """Return special_precaution string if one exists for this stone."""
    q = quality_data.get(stone_name, {})
    return q.get("special_precaution") or None
