"""Namakarana — Vedic Naming Ceremony computation.

Complete implementation: 27 x 4 pada syllable table, rashi-based letter
assignments, Gand Mool check, Chaldean numerology, name scoring, and
name suggestion generation.

Source: Traditional Jyotish practice (Parashari), Chaldean numerology.
"""

from __future__ import annotations

from daivai_engine.compute.namakarana_tables import (
    _CHALDEAN,
    _GAND_MOOL_NAKSHATRAS,
    _GAND_MOOL_SEVERITY,
    _NAKSHATRA_LETTERS,
)
from daivai_engine.knowledge.loader import load_namakarana_rules
from daivai_engine.models.chart import ChartData
from daivai_engine.models.namakarana import (
    GandMoolResult,
    NamakaranaResult,
    NameNumerology,
    NameScore,
    NameSuggestion,
)


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


def compute_name_number(name: str) -> NameNumerology:
    """Compute Chaldean name numerology for a given name.

    Sums Chaldean letter values for all alpha characters and reduces
    the total to a single digit (1-9).

    Source: Chaldean numerology system.

    Args:
        name: Candidate name string (spaces and non-alpha are ignored).

    Returns:
        NameNumerology with name number, raw sum, and interpretation.
    """
    raw_sum = sum(_CHALDEAN.get(c.upper(), 0) for c in name if c.isalpha())
    number = _reduce_to_single(raw_sum)
    interpretations = {
        1: "Leadership, independence, originality",
        2: "Cooperation, diplomacy, sensitivity",
        3: "Expression, creativity, social nature",
        4: "Stability, discipline, hard work",
        5: "Freedom, adventure, versatility",
        6: "Responsibility, love, nurturing",
        7: "Spirituality, analysis, wisdom",
        8: "Power, ambition, material success",
        9: "Compassion, completion, universal love",
    }
    return NameNumerology(
        name=name,
        name_number=number,
        raw_sum=raw_sum,
        interpretation=interpretations.get(number, ""),
    )


def score_name(name: str, chart: ChartData) -> NameScore:
    """Score a candidate name for auspiciousness against the birth chart.

    Evaluates three dimensions:
    1. Nakshatra match (0-40 pts): name starts with Moon's pada syllable.
    2. Rashi score (0-30 pts): name starts with a Moon-sign letter.
    3. Numerology score (0-30 pts): name number compatible with birth number.

    Total ≥ 60 is flagged as recommended for the naming ceremony.

    Args:
        name: Candidate name to score (first name or full name).
        chart: The newborn's birth chart.

    Returns:
        NameScore with component scores, name number, and recommendation flag.
    """
    moon = chart.planets["Moon"]
    name_lower = name.strip().lower()

    # 1. Nakshatra-pada match (0-40 points)
    pada_letters = get_naming_syllables(moon.nakshatra, moon.pada)
    nak_score = 40.0 if _starts_with_any(name_lower, pada_letters) else 0.0

    # 2. Rashi match (0-30 points)
    rashi_ltrs = get_rashi_letters(moon.sign)
    rashi_score = 30.0 if _starts_with_any(name_lower, rashi_ltrs) else 0.0

    # 3. Numerology compatibility (0-30 points)
    numerology = compute_name_number(name)
    birth_num = _birth_number(chart.dob)
    compat = _compatible_numbers(birth_num)
    num_score = 30.0 if numerology.name_number in compat else 0.0

    total = nak_score + rashi_score + num_score
    breakdown: dict[str, str] = {
        "nakshatra": moon.nakshatra,
        "pada": str(moon.pada),
        "nakshatra_letters": ", ".join(pada_letters) if pada_letters else "none",
        "rashi": moon.sign,
        "rashi_letters_sample": ", ".join(rashi_ltrs[:5]) if rashi_ltrs else "none",
        "birth_number": str(birth_num),
        "name_number": str(numerology.name_number),
        "compatible_numbers": ", ".join(str(n) for n in compat),
    }
    return NameScore(
        name=name,
        total_score=min(total, 100.0),
        nakshatra_match=nak_score,
        rashi_score=rashi_score,
        numerology_score=num_score,
        name_number=numerology.name_number,
        is_recommended=total >= 60.0,
        breakdown=breakdown,
    )


def suggest_names(chart: ChartData) -> NameSuggestion:
    """Generate complete naming guidance for the Namakarana ceremony.

    Returns a NameSuggestion with primary nakshatra-pada syllables,
    rashi letters, birth numerology, and compatible name numbers.

    Args:
        chart: The newborn's birth chart.

    Returns:
        NameSuggestion with all astrological context for name selection.
    """
    moon = chart.planets["Moon"]
    nak, pada = moon.nakshatra, moon.pada
    rashi, rashi_lord = moon.sign, moon.sign_lord

    pada_letters = get_naming_syllables(nak, pada)
    r_letters = get_rashi_letters(rashi)
    birth_num = _birth_number(chart.dob)
    compat_nums = _compatible_numbers(birth_num)

    # all_letters = pada letters + rashi letters not already in pada set
    pada_set = {s.lower() for s in pada_letters}
    extra = [syllable for syllable in r_letters if syllable.lower() not in pada_set]
    all_letters = list(pada_letters) + extra

    guidance = (
        f"Moon in {nak} Pada {pada} ({rashi}). "
        f"Primary syllables: {', '.join(pada_letters) or 'see rashi letters'}. "
        f"Rashi lord: {rashi_lord}. "
        f"Target name number: {', '.join(str(n) for n in compat_nums[:3])}."
    )
    return NameSuggestion(
        nakshatra=nak,
        pada=pada,
        nakshatra_letters=pada_letters,
        rashi=rashi,
        rashi_letters=r_letters,
        rashi_lord=rashi_lord,
        birth_number=birth_num,
        compatible_name_numbers=compat_nums,
        primary_letters=pada_letters,
        all_letters=all_letters,
        guidance=guidance,
    )


def compute_namakarana(chart: ChartData) -> NamakaranaResult:
    """Compute the complete Namakarana result for a birth chart.

    Combines Gand Mool dosha check and name suggestion into one result.

    Args:
        chart: The newborn's birth chart.

    Returns:
        NamakaranaResult with gand_mool and suggestion fields populated.
    """
    return NamakaranaResult(
        gand_mool=check_gand_mool(chart),
        suggestion=suggest_names(chart),
    )


# ── Private helpers ───────────────────────────────────────────────────────────


def _reduce_to_single(n: int) -> int:
    """Reduce integer to single digit (1-9) by iteratively summing digits."""
    while n > 9:
        n = sum(int(d) for d in str(n))
    return max(n, 1)


def _birth_number(dob: str) -> int:
    """Compute birth root number from DOB string (DD/MM/YYYY or DD-MM-YYYY).

    Sums all digits of the full date string and reduces to single digit.

    Args:
        dob: Date of birth string (e.g., "13/03/1989").

    Returns:
        Birth root number (1-9).
    """
    digits = [int(c) for c in dob if c.isdigit()]
    return _reduce_to_single(sum(digits)) if digits else 1


def _compatible_numbers(birth_num: int) -> list[int]:
    """Return sorted compatible name numbers for a given birth number.

    Args:
        birth_num: Birth root number (1-9).

    Returns:
        Sorted list of compatible Chaldean name numbers.
    """
    rules = load_namakarana_rules()
    data = rules.get("numerology_compatibility", {}).get(birth_num, {})
    return sorted(data.get("compatible", []))


def _starts_with_any(text: str, syllables: list[str]) -> bool:
    """Check if text starts with any syllable (case-insensitive).

    Args:
        text: Lowercased name string.
        syllables: Syllable list (e.g., ["Va", "Vi"]).

    Returns:
        True if text starts with any of the syllables.
    """
    return any(text.startswith(s.lower()) for s in syllables)
