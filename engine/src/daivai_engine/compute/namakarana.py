"""Namakarana — Vedic Naming Ceremony computation.

Core functions: 27 x 4 pada syllable lookup, rashi-based letter
assignments, and Gand Mool dosha check.

Scoring, numerology, and suggestion logic live in namakarana_scoring.py.

Source: Traditional Jyotish practice (Parashari), Chaldean numerology.
"""

from __future__ import annotations

from daivai_engine.compute.namakarana_tables import (
    _GAND_MOOL_NAKSHATRAS,
    _GAND_MOOL_SEVERITY,
    _NAKSHATRA_LETTERS,
)
from daivai_engine.knowledge.loader import load_namakarana_rules
from daivai_engine.models.chart import ChartData
from daivai_engine.models.namakarana import GandMoolResult


def get_naming_syllables(moon_nakshatra: str, moon_pada: int) -> list[str]:
    """Get recommended starting syllables (aksharas) for naming.

    Returns traditional Jyotish-recommended syllables based on Moon's
    nakshatra and pada at birth (from the 108-pada table).

    Args:
        moon_nakshatra: Moon's nakshatra name at birth (e.g., "Rohini").
        moon_pada: Moon's pada (1-4).

    Returns:
        List of recommended starting syllables.
    """
    letters = _NAKSHATRA_LETTERS.get(moon_nakshatra)
    if not letters or not (1 <= moon_pada <= 4):
        return []
    return letters[moon_pada - 1]


# Backward-compatible alias
def get_name_letters(moon_nakshatra: str, moon_pada: int) -> list[str]:
    """Alias for get_naming_syllables — backward compatibility."""
    return get_naming_syllables(moon_nakshatra, moon_pada)


def get_rashi_letters(rashi: str) -> list[str]:
    """Get all recommended starting letters for a Moon-sign (rashi).

    Returns the 9 syllables derived from the three nakshatras spanning
    that rashi, providing secondary auspicious options beyond the exact pada.

    Args:
        rashi: Vedic rashi name in Sanskrit (e.g., "Vrishabha").

    Returns:
        List of starting syllables for that rashi.
    """
    rules = load_namakarana_rules()
    return list(rules.get("rashi_letters", {}).get(rashi, {}).get("letters", []))


def check_gand_mool(chart: ChartData) -> GandMoolResult:
    """Check if Moon is in a Gand Mool nakshatra.

    Gand Mool nakshatras: Ashwini, Ashlesha, Magha, Jyeshtha, Moola, Revati.
    A child born with Moon in these nakshatras traditionally requires a
    Gand Mool Shanti Puja, ideally on the 27th day after birth.

    Source: Traditional Jyotish practice.

    Args:
        chart: The newborn's computed ChartData.

    Returns:
        GandMoolResult with presence flag, severity, and remedy guidance.
    """
    moon = chart.planets["Moon"]
    nak, pada = moon.nakshatra, moon.pada

    if nak not in _GAND_MOOL_NAKSHATRAS:
        return GandMoolResult(
            is_gand_mool=False,
            nakshatra=nak,
            pada=pada,
            severity="none",
            description="Moon not in Gand Mool nakshatra",
            recommended_shanti="",
        )

    severity = _GAND_MOOL_SEVERITY.get(nak, {}).get(pada, "mild")
    return GandMoolResult(
        is_gand_mool=True,
        nakshatra=nak,
        pada=pada,
        severity=severity,
        description=f"Moon in {nak} Pada {pada} — Gand Mool dosha present",
        recommended_shanti=(
            f"Gand Mool Shanti Puja recommended (nakshatra: {nak}). "
            "Perform on 27th day after birth or on a favorable muhurta."
        ),
    )


# -- Private helpers (used by namakarana_scoring) ------------------------------


def _starts_with_any(text: str, syllables: list[str]) -> bool:
    """Check if text starts with any syllable (case-insensitive).

    Args:
        text: Lowercased name string.
        syllables: Syllable list (e.g., ["Va", "Vi"]).

    Returns:
        True if text starts with any of the syllables.
    """
    return any(text.startswith(s.lower()) for s in syllables)


# -- Re-exports for backward compatibility ------------------------------------
# These functions moved to namakarana_scoring.py but are re-exported here
# so existing imports (e.g., from daivai_engine.compute.namakarana import
# compute_namakarana) continue to work.
from daivai_engine.compute.namakarana_scoring import (  # noqa: E402, I001
    compute_name_number as compute_name_number,
    compute_namakarana as compute_namakarana,
    score_name as score_name,
    suggest_names as suggest_names,
)
