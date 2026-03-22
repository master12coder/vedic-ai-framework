"""Lo Shu grid construction and arrow pattern detection for Vedic Numerology.

The Lo Shu is a 3x3 magic square whose nine positions correspond to numbers
1-9. A birth date's digits are counted and placed in their fixed grid positions.
Eight arrow patterns (rows, columns, diagonals) reveal inherent strengths and
areas needing development.

All configuration is loaded from engine/knowledge/numerology_rules.yaml.
"""

from __future__ import annotations

from daivai_engine.knowledge.loader import load_numerology_rules
from daivai_engine.models.numerology import ArrowPattern, LoShuGrid


# ── Fixed Lo Shu grid position map ────────────────────────────────────────────
# Number → (row, col) in the 3x3 grid (0-indexed).
#   4  9  2   → row 0
#   3  5  7   → row 1
#   8  1  6   → row 2

_LOSHU_POSITIONS: dict[int, tuple[int, int]] = {
    4: (0, 0),
    9: (0, 1),
    2: (0, 2),
    3: (1, 0),
    5: (1, 1),
    7: (1, 2),
    8: (2, 0),
    1: (2, 1),
    6: (2, 2),
}

# Arrow key order (determines display order in results)
_ARROW_KEYS = [
    "thought",
    "will",
    "action",
    "memory",
    "determination",
    "emotions",
    "spirituality",
    "compassion",
]


def _extract_digits(day: int, month: int, year: int) -> list[int]:
    """Extract all non-zero digits from a birth date.

    Args:
        day:   Birth day (1-31).
        month: Birth month (1-12).
        year:  Birth year (4 digits).

    Returns:
        List of individual digits from DD/MM/YYYY, with zeros removed.
    """
    date_str = f"{day:02d}{month:02d}{year:04d}"
    return [int(ch) for ch in date_str if ch != "0"]


def _count_digits(digits: list[int]) -> dict[int, int]:
    """Count occurrences of each digit 1-9 in the list.

    Args:
        digits: List of birth-date digits (zeros already removed).

    Returns:
        Dict mapping digit (1-9) to its occurrence count.
    """
    counts: dict[int, int] = {n: 0 for n in range(1, 10)}
    for d in digits:
        if 1 <= d <= 9:
            counts[d] += 1
    return counts


def _build_grid(counts: dict[int, int]) -> list[list[int]]:
    """Construct the 3x3 Lo Shu grid from digit counts.

    Each cell in the 3x3 grid holds the occurrence count of the number
    fixed at that position in the Lo Shu arrangement.

    Args:
        counts: Digit occurrence counts from _count_digits.

    Returns:
        3x3 list of lists containing occurrence counts.
    """
    grid = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    for number, (row, col) in _LOSHU_POSITIONS.items():
        grid[row][col] = counts.get(number, 0)
    return grid


def _detect_arrows(counts: dict[int, int]) -> list[ArrowPattern]:
    """Detect all eight Lo Shu arrow patterns from digit counts.

    An arrow is PRESENT when all three of its numbers appear at least once.
    An arrow is MISSING when none of its three numbers appear at all.
    Otherwise it is partially filled (neither present nor missing).

    Args:
        counts: Digit occurrence counts from _count_digits.

    Returns:
        List of ArrowPattern objects for all 8 arrows, in canonical order.
    """
    rules = load_numerology_rules()
    pattern_defs: dict[str, dict] = rules.get("arrow_patterns", {})

    arrows: list[ArrowPattern] = []

    for key in _ARROW_KEYS:
        defn = pattern_defs.get(key, {})
        numbers: list[int] = defn.get("numbers", [])

        present_count = sum(1 for n in numbers if counts.get(n, 0) > 0)
        is_present = present_count == len(numbers)
        is_missing = present_count == 0

        arrows.append(
            ArrowPattern(
                key=key,
                name=defn.get("name", key),
                name_hi=defn.get("name_hi", ""),
                numbers=numbers,
                is_present=is_present,
                is_missing=is_missing,
                plane=defn.get("plane", ""),
                plane_hi=defn.get("plane_hi", ""),
                meaning=defn.get("meaning", ""),
                missing_meaning=defn.get("missing_meaning", ""),
            )
        )

    return arrows


def build_loshu_grid(day: int, month: int, year: int) -> LoShuGrid:
    """Build the complete Lo Shu grid analysis for a birth date.

    Extracts digits from DD/MM/YYYY (excluding zeros), counts occurrences,
    places counts into the 3x3 Lo Shu arrangement, and detects all eight
    arrow patterns.

    Args:
        day:   Birth day (1-31).
        month: Birth month (1-12).
        year:  Birth year (4 digits, e.g. 1989).

    Returns:
        LoShuGrid with grid values, present/missing numbers, and arrows.

    Example:
        Birth date 13/03/1989 → digits [1,3,3,1,9,8,9] (zero removed)
        Counts: {1:2, 3:2, 8:1, 9:2} → others 0
        Present: [1,3,8,9]; Missing: [2,4,5,6,7]
    """
    digits = _extract_digits(day, month, year)
    counts = _count_digits(digits)

    grid = _build_grid(counts)
    arrows = _detect_arrows(counts)

    present_numbers = sorted(n for n in range(1, 10) if counts[n] > 0)
    missing_numbers = sorted(n for n in range(1, 10) if counts[n] == 0)

    present_arrow_names = [a.name for a in arrows if a.is_present]
    missing_arrow_names = [a.name for a in arrows if a.is_missing]

    # Stringify digit_counts keys for Pydantic (dict[str, int])
    digit_counts_str = {str(k): v for k, v in counts.items()}

    return LoShuGrid(
        grid=grid,
        digit_counts=digit_counts_str,
        present_numbers=present_numbers,
        missing_numbers=missing_numbers,
        arrows=arrows,
        present_arrow_names=present_arrow_names,
        missing_arrow_names=missing_arrow_names,
    )
