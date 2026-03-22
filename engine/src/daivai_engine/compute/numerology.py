"""Vedic Numerology (Anka Jyotish) core number computation engine.

Computes the four core numbers: Mulank (birth day), Bhagyank (full date),
Namank (name via Chaldean/Pythagorean/Devanagari), and Kua (Lo Shu personal).
Yantra, compatibility, and attribute lookups live in numerology_attrs.py.

All letter-value tables are loaded from engine/knowledge/numerology_rules.yaml.
"""

from __future__ import annotations

from daivai_engine.compute.numerology_attrs import (
    compute_compatibility,
    generate_yantra,
    get_compound_number_meaning,
    get_number_attributes,
    planet_for_number,
)
from daivai_engine.compute.numerology_loshu import build_loshu_grid
from daivai_engine.exceptions import ValidationError
from daivai_engine.knowledge.loader import load_numerology_rules
from daivai_engine.models.numerology import (
    LoShuGrid,
    NumerologyNumbers,
    NumerologyResult,
)


_MASTER_NUMBERS: frozenset[int] = frozenset({11, 22, 33})


# ── Digit helpers ─────────────────────────────────────────────────────────────


def _digit_sum(n: int) -> int:
    """Sum all decimal digits of a positive integer (e.g. 1989 -> 27)."""
    return sum(int(ch) for ch in str(abs(n)))


def reduce_to_single(n: int, preserve_master: bool = True) -> int:
    """Iteratively reduce n to a single digit (1-9).

    Args:
        n:               Positive integer to reduce.
        preserve_master: When True, stop at 11, 22, or 33.

    Returns:
        Integer in 1-9 (or 11/22/33 when preserve_master is True).

    Raises:
        ValidationError: If n <= 0.
    """
    if n <= 0:
        raise ValidationError(f"Number must be positive, got {n}")
    while n > 9:
        if preserve_master and n in _MASTER_NUMBERS:
            break
        n = _digit_sum(n)
        if preserve_master and n in _MASTER_NUMBERS:
            break
    return n


# ── Core number computations ──────────────────────────────────────────────────


def compute_mulank(day: int, preserve_master: bool = False) -> tuple[int, int | None]:
    """Compute Mulank (Birth/Root Number) from the birth day (1-31).

    Returns:
        (mulank, compound) where compound is the raw day when > 9, else None.

    Raises:
        ValidationError: If day is not 1-31.
    """
    if not 1 <= day <= 31:
        raise ValidationError(f"Day must be between 1 and 31, got {day}")
    if day <= 9:
        return day, None
    return reduce_to_single(day, preserve_master=preserve_master), day


def compute_bhagyank(
    day: int, month: int, year: int, preserve_master: bool = False
) -> tuple[int, int | None]:
    """Compute Bhagyank (Destiny Number) by summing all digits of DD/MM/YYYY.

    Example: 13/03/1989 -> 1+3+0+3+1+9+8+9=34 -> 3+4=7 -> returns (7, 34).

    Returns:
        (bhagyank, compound) where compound is the digit sum before final
        reduction, or None when digit sum is already single digit.

    Raises:
        ValidationError: If arguments are out of range.
    """
    if not 1 <= day <= 31:
        raise ValidationError(f"Day must be between 1 and 31, got {day}")
    if not 1 <= month <= 12:
        raise ValidationError(f"Month must be between 1 and 12, got {month}")
    if year < 1:
        raise ValidationError(f"Year must be positive, got {year}")

    total = sum(int(ch) for ch in f"{day:02d}{month:02d}{year:04d}")
    if total <= 9:
        return total, None
    return reduce_to_single(total, preserve_master=preserve_master), total


def compute_namank(name: str, system: str = "chaldean") -> tuple[int, int | None]:
    """Compute Namank (Name Number) using the specified letter-value system.

    Args:
        name:   Full name string. Spaces and punctuation are ignored.
        system: "chaldean" (default), "pythagorean", or "devanagari".

    Returns:
        (namank, compound) where compound is the pre-reduction total,
        or None when already single digit.

    Raises:
        ValidationError: If system is unknown or name has no valid letters.
    """
    valid_systems = {"chaldean", "pythagorean", "devanagari"}
    if system not in valid_systems:
        raise ValidationError(
            f"Unknown letter-value system '{system}'. Valid: {sorted(valid_systems)}"
        )
    clean_name = name.strip()
    if not clean_name:
        raise ValidationError("Name must not be empty")

    rules = load_numerology_rules()
    value_table: dict[str, int] = rules.get(f"{system}_values", {})

    total = 0
    for ch in clean_name:
        if ch.isspace() or ch in ".-_'":
            continue
        val = value_table.get(ch) or value_table.get(ch.upper())
        if val is not None:
            total += val

    if total == 0:
        raise ValidationError(f"No valid letters found in name '{name}' for system '{system}'")
    if total <= 9:
        return total, None
    return reduce_to_single(total, preserve_master=False), total


def compute_kua_number(birth_year: int, gender: str) -> int:
    """Compute the Kua Number (Lo Shu personal number) for a birth year.

    Formula: reduce year digits to year_digit, then
    Male pre-2000: 11 - year_digit | post-2000: 9 - year_digit
    Female pre-2000: 4 + year_digit | post-2000: 6 + year_digit
    Result 5 -> Male=2, Female=8.

    Raises:
        ValidationError: If birth_year < 1 or gender not Male/Female.
    """
    if birth_year < 1:
        raise ValidationError(f"Birth year must be positive, got {birth_year}")
    gender_lower = gender.strip().lower()
    if gender_lower not in {"male", "female"}:
        raise ValidationError(f"Gender must be 'Male' or 'Female', got '{gender}'")

    year_digit = reduce_to_single(_digit_sum(birth_year), preserve_master=False)

    if gender_lower == "male":
        kua = 11 - year_digit if birth_year < 2000 else 9 - year_digit
        if kua <= 0:
            kua += 9
    else:
        kua = 4 + year_digit if birth_year < 2000 else 6 + year_digit

    kua = reduce_to_single(kua, preserve_master=False)
    if kua == 5:
        kua = 2 if gender_lower == "male" else 8
    return kua


# ── Main entry point ──────────────────────────────────────────────────────────


def compute_numerology(
    dob: str,
    name: str | None = None,
    gender: str | None = None,
) -> NumerologyResult:
    """Compute a complete Vedic Numerology analysis (Anka Jyotish).

    Args:
        dob:    Birth date "DD/MM/YYYY".
        name:   Optional full name for Namank computation.
        gender: Optional "Male"/"Female" for Kua number.

    Returns:
        NumerologyResult with all computed values.

    Raises:
        ValidationError: If dob format is invalid.

    Example:
        compute_numerology("13/03/1989", "Manish Chaurasia", "Male")
        -> Mulank=4(Rahu), Bhagyank=7(Ketu), Namank=6(Venus), Kua=2(Moon)
    """
    try:
        parts = dob.strip().split("/")
        if len(parts) != 3:
            raise ValueError
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
    except (ValueError, AttributeError) as exc:
        raise ValidationError(f"Invalid birth date format '{dob}'. Expected 'DD/MM/YYYY'.") from exc

    mulank, mulank_compound = compute_mulank(day, preserve_master=False)
    bhagyank, bhagyank_compound = compute_bhagyank(day, month, year, preserve_master=False)

    namank: int | None = None
    namank_compound: int | None = None
    if name:
        try:
            namank, namank_compound = compute_namank(name, system="chaldean")
        except ValidationError:
            namank = None

    kua: int | None = None
    if gender:
        kua = compute_kua_number(year, gender)

    numbers = NumerologyNumbers(
        mulank=mulank,
        mulank_compound=mulank_compound,
        bhagyank=bhagyank,
        bhagyank_compound=bhagyank_compound,
        namank=namank,
        namank_compound=namank_compound,
        kua=kua,
        mulank_planet=planet_for_number(mulank),
        bhagyank_planet=planet_for_number(bhagyank),
        namank_planet=planet_for_number(namank) if namank else None,
    )

    loshu = build_loshu_grid(day, month, year)

    return NumerologyResult(
        name=name,
        dob=dob,
        gender=gender,
        numbers=numbers,
        mulank_attributes=get_number_attributes(mulank),
        bhagyank_attributes=get_number_attributes(bhagyank),
        loshu_grid=loshu,
        mulank_yantra=generate_yantra(mulank),
        summary=_build_summary(numbers, name, loshu),
    )


def _build_summary(numbers: NumerologyNumbers, name: str | None, loshu: LoShuGrid) -> str:
    """Compose a concise numerology summary string."""
    parts: list[str] = []
    if name:
        parts.append(f"{name}:")
    parts.append(
        f"Mulank {numbers.mulank} ({numbers.mulank_planet}), "
        f"Bhagyank {numbers.bhagyank} ({numbers.bhagyank_planet})"
    )
    if numbers.namank:
        parts.append(f"Namank {numbers.namank} ({numbers.namank_planet})")
    if numbers.kua:
        rules = load_numerology_rules()
        kua_planet = rules.get("planet_numbers", {}).get(numbers.kua, "")
        parts.append(f"Kua {numbers.kua} ({kua_planet})")
    if loshu.present_arrow_names:
        parts.append(f"Lo Shu arrows present: {len(loshu.present_arrow_names)}")
    if loshu.missing_arrow_names:
        parts.append(f"Missing arrows: {len(loshu.missing_arrow_names)}")
    return ". ".join(parts) + "."


# Re-export attrs helpers so callers can use a single import point
__all__ = [
    "compute_bhagyank",
    "compute_compatibility",
    "compute_kua_number",
    "compute_mulank",
    "compute_namank",
    "compute_numerology",
    "generate_yantra",
    "get_compound_number_meaning",
    "get_number_attributes",
    "reduce_to_single",
]
