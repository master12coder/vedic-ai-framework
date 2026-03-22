"""Sarvatobhadra Chakra (SBC) -- 9x9 transit analysis grid.

The SBC is used by both North and South Indian pandits to analyze transit
effects through geometric vedha (obstruction) patterns. A transiting planet
at a nakshatra strikes cells in the grid via three vedha types:

  1. Across (Tirya Vedha):      entire row + column through the planet's cell
  2. Fore   (Agra Vedha):       / diagonal -- clockwise / zodiacal direction
  3. Hind   (Prishthaja Vedha): backslash diagonal -- counter-clockwise direction

Source: Phaladeepika Ch.26; Gopesh Kumar Ojha commentary (Bhavartha Bodhini).
Grid layout cross-checked against PyJHora chakra.py (PyJHora project).
"""

from __future__ import annotations

from daivai_engine.constants import NAKSHATRAS, SIGNS
from daivai_engine.models.sarvatobhadra import SBCCell, SBCVedhaResult


# ── Tithi group → tithi numbers (1-30) ────────────────────────────────────────
# Five groups by position within each paksha (1st/6th/11th = Nanda, etc.)
_TITHI_GROUPS: dict[str, list[int]] = {
    "Nanda": [1, 6, 11, 16, 21, 26],
    "Bhadra": [2, 7, 12, 17, 22, 27],
    "Jaya": [3, 8, 13, 18, 23, 28],
    "Rikta": [4, 9, 14, 19, 24, 29],
    "Purna": [5, 10, 15, 20, 25, 30],
}

# ── Special name for the 28th SBC nakshatra ────────────────────────────────────
_ABHIJIT = "Abhijit"

# ── Compact raw grid definition ────────────────────────────────────────────────
# Encoding:
#   ('n', int)              nakshatra, 1-based SBC number (1-28)
#   ('v', str)              vowel (svara)
#   ('c', str)              consonant (vyanjana)
#   ('r', int)              rashi, 1-based (1=Mesha … 12=Meena)
#   ('t', str, list[str])   tithi group + varas
#   ('ct', str, list[str])  center cell: Purna tithi + Saturday

_GRID_RAW: list[list[tuple]] = [
    # Row 0 — North outer ring (left→right, zodiacal Dhanishtha→Bharani)
    [
        ("v", "ii"),
        ("n", 23),
        ("n", 24),
        ("n", 25),
        ("n", 26),
        ("n", 27),
        ("n", 1),
        ("n", 2),
        ("v", "a"),
    ],
    # Row 1 — Ring 2 North consonants; outer WEST=22(Shravana), EAST=3(Krittika)
    [
        ("n", 22),
        ("v", "rii"),
        ("c", "ga"),
        ("c", "sa"),
        ("c", "da"),
        ("c", "cha"),
        ("c", "la"),
        ("v", "u"),
        ("n", 3),
    ],
    # Row 2 — Abhijit on WEST; Ring 2 East 'a'; Ring 3 North rashis; EAST=4(Rohini)
    [
        ("n", 28),
        ("c", "kha"),
        ("v", "ai"),
        ("r", 11),
        ("r", 12),
        ("r", 1),
        ("v", "lu"),
        ("c", "a"),
        ("n", 4),
    ],
    # Row 3 — Ring 3 West/East rashis; Ring 4 corners; Rikta/Friday cell
    [
        ("n", 21),
        ("c", "ja"),
        ("r", 10),
        ("v", "ah"),
        ("t", "Rikta", ["Friday"]),
        ("v", "o"),
        ("r", 2),
        ("c", "va"),
        ("n", 5),
    ],
    # Row 4 — Center row: Jaya/Thursday, CENTER Purna/Saturday, Nanda/Sun+Tue
    [
        ("n", 20),
        ("c", "bha"),
        ("r", 9),
        ("t", "Jaya", ["Thursday"]),
        ("ct", "Purna", ["Saturday"]),
        ("t", "Nanda", ["Sunday", "Tuesday"]),
        ("r", 3),
        ("c", "ka"),
        ("n", 6),
    ],
    # Row 5 — Ring 3/4 junction; Bhadra/Mon+Wed cell
    [
        ("n", 19),
        ("c", "ya"),
        ("r", 8),
        ("v", "am"),
        ("t", "Bhadra", ["Monday", "Wednesday"]),
        ("v", "au"),
        ("r", 4),
        ("c", "ha"),
        ("n", 7),
    ],
    # Row 6 — Ring 3 South rashis (Libra, Virgo, Leo); Ring 2 East 'da'
    [
        ("n", 18),
        ("c", "na"),
        ("v", "e"),
        ("r", 7),
        ("r", 6),
        ("r", 5),
        ("v", "luu"),
        ("c", "da"),
        ("n", 8),
    ],
    # Row 7 — Ring 2 South consonants; outer WEST=17(Anuradha), EAST=9(Ashlesha)
    [
        ("n", 17),
        ("v", "ri"),
        ("c", "ta"),
        ("c", "ra"),
        ("c", "pa"),
        ("c", "tha"),
        ("c", "ma"),
        ("v", "uu"),
        ("n", 9),
    ],
    # Row 8 — South outer ring (left→right, Vishakha→Magha)
    [
        ("v", "i"),
        ("n", 16),
        ("n", 15),
        ("n", 14),
        ("n", 13),
        ("n", 12),
        ("n", 11),
        ("n", 10),
        ("v", "aa"),
    ],
]


def _build_cell(row: int, col: int, raw: tuple) -> SBCCell:
    """Convert one raw tuple to an SBCCell."""
    kind = raw[0]

    if kind == "n":
        num: int = raw[1]
        name = NAKSHATRAS[num - 1] if num <= 27 else _ABHIJIT
        return SBCCell(row=row, col=col, nakshatra_nums=[num], nakshatra_names=[name])

    if kind == "v":
        return SBCCell(row=row, col=col, vowels=[raw[1]])

    if kind == "c":
        return SBCCell(row=row, col=col, consonants=[raw[1]])

    if kind == "r":
        rashi_1based: int = raw[1]
        return SBCCell(
            row=row,
            col=col,
            rashis=[rashi_1based],
            rashi_names=[SIGNS[rashi_1based - 1]],
        )

    if kind in ("t", "ct"):
        group: str = raw[1]
        varas: list[str] = raw[2]
        return SBCCell(
            row=row,
            col=col,
            tithi_group=group,
            tithi_numbers=_TITHI_GROUPS[group],
            varas=varas,
            is_center=(kind == "ct"),
        )

    raise ValueError(f"Unknown SBC cell kind: {kind!r}")  # pragma: no cover


def build_sbc_grid() -> list[list[SBCCell]]:
    """Build the complete 9x9 SBC grid from the raw layout.

    Returns:
        9x9 list (row-major) of SBCCell objects, indexed as grid[row][col].
    """
    return [[_build_cell(r, c, _GRID_RAW[r][c]) for c in range(9)] for r in range(9)]


def _build_nakshatra_positions() -> dict[int, tuple[int, int]]:
    """Map SBC nakshatra number (1-28) → (row, col)."""
    positions: dict[int, tuple[int, int]] = {}
    for r in range(9):
        for c in range(9):
            raw = _GRID_RAW[r][c]
            if raw[0] == "n":
                positions[raw[1]] = (r, c)
    return positions


# ── Module-level cached data structures ───────────────────────────────────────
_SBC_GRID: list[list[SBCCell]] = build_sbc_grid()
_NAKSHATRA_POSITIONS: dict[int, tuple[int, int]] = _build_nakshatra_positions()


# ── Vedha geometry helpers ────────────────────────────────────────────────────


def _across_cells(r: int, c: int) -> list[SBCCell]:
    """Across (Tirya) vedha: entire row + column, excluding planet's own cell."""
    cells: list[SBCCell] = []
    for col in range(9):
        if col != c:
            cells.append(_SBC_GRID[r][col])
    for row in range(9):
        if row != r:
            cells.append(_SBC_GRID[row][c])
    return cells


def _fore_cells(r: int, c: int) -> list[SBCCell]:
    """Fore (Agra) vedha: / diagonal — clockwise (zodiacal) direction.

    Upper-right arm: (r-k, c+k) while in bounds.
    Lower-left  arm: (r+k, c-k) while in bounds.
    """
    cells: list[SBCCell] = []
    k = 1
    while r - k >= 0 and c + k <= 8:
        cells.append(_SBC_GRID[r - k][c + k])
        k += 1
    k = 1
    while r + k <= 8 and c - k >= 0:
        cells.append(_SBC_GRID[r + k][c - k])
        k += 1
    return cells


def _hind_cells(r: int, c: int) -> list[SBCCell]:
    """Hind (Prishthaja) vedha: \\ diagonal — counter-clockwise direction.

    Upper-left  arm: (r-k, c-k) while in bounds.
    Lower-right arm: (r+k, c+k) while in bounds.
    """
    cells: list[SBCCell] = []
    k = 1
    while r - k >= 0 and c - k >= 0:
        cells.append(_SBC_GRID[r - k][c - k])
        k += 1
    k = 1
    while r + k <= 8 and c + k <= 8:
        cells.append(_SBC_GRID[r + k][c + k])
        k += 1
    return cells


# ── Extraction helpers ────────────────────────────────────────────────────────


def _nakshatra_names(cells: list[SBCCell]) -> list[str]:
    names: list[str] = []
    for cell in cells:
        names.extend(cell.nakshatra_names)
    return names


def _tithi_groups(cells: list[SBCCell]) -> list[str]:
    groups: list[str] = []
    for cell in cells:
        if cell.tithi_group and cell.tithi_group not in groups:
            groups.append(cell.tithi_group)
    return groups


def _varas(cells: list[SBCCell]) -> list[str]:
    result: list[str] = []
    for cell in cells:
        for vara in cell.varas:
            if vara not in result:
                result.append(vara)
    return result


# ── Public API ─────────────────────────────────────────────────────────────────


def compute_sbc_vedha(
    transit_planet: str,
    transit_nakshatra_index: int,
) -> SBCVedhaResult:
    """Compute SBC vedha for a transiting planet at a given nakshatra.

    Given a planet's transit nakshatra, determines which grid cells are
    geometrically struck via all three vedha types (across, fore, hind).

    The products layer should then apply the motion rule to decide which
    vedha types are active (e.g., fore for fast planets, hind for retrograde).

    Args:
        transit_planet: Planet name (e.g., "Jupiter", "Saturn", "Rahu").
        transit_nakshatra_index: 0-based nakshatra index (0=Ashwini … 26=Revati).

    Returns:
        SBCVedhaResult with raw cell lists and derived name/tithi/vara summaries.

    Raises:
        ValueError: If nakshatra_index is outside 0-26.
    """
    if not 0 <= transit_nakshatra_index <= 26:
        raise ValueError(f"transit_nakshatra_index must be 0-26, got {transit_nakshatra_index}")

    sbc_num = transit_nakshatra_index + 1  # Convert to 1-based SBC number
    row, col = _NAKSHATRA_POSITIONS[sbc_num]
    nakshatra_name = NAKSHATRAS[transit_nakshatra_index]

    across = _across_cells(row, col)
    fore = _fore_cells(row, col)
    hind = _hind_cells(row, col)

    return SBCVedhaResult(
        transit_planet=transit_planet,
        transit_nakshatra_num=sbc_num,
        transit_nakshatra=nakshatra_name,
        planet_row=row,
        planet_col=col,
        across_vedha=across,
        fore_vedha=fore,
        hind_vedha=hind,
        struck_nakshatras_across=_nakshatra_names(across),
        struck_nakshatras_fore=_nakshatra_names(fore),
        struck_nakshatras_hind=_nakshatra_names(hind),
        struck_tithis_across=_tithi_groups(across),
        struck_varas_across=_varas(across),
    )


def is_nakshatra_struck(
    vedha_result: SBCVedhaResult,
    nakshatra_index: int,
    vedha_types: list[str] | None = None,
) -> bool:
    """Check whether a natal nakshatra is struck by the transiting planet.

    Args:
        vedha_result: Result from compute_sbc_vedha().
        nakshatra_index: 0-based index (0=Ashwini … 26=Revati) of the natal star.
        vedha_types: Which vedha types to check. Defaults to all three.
                     Accepts any subset of ['across', 'fore', 'hind'].

    Returns:
        True if the natal nakshatra appears in any of the requested vedha types.
    """
    if not 0 <= nakshatra_index <= 26:
        raise ValueError(f"nakshatra_index must be 0-26, got {nakshatra_index}")

    check = set(vedha_types) if vedha_types else {"across", "fore", "hind"}
    name = NAKSHATRAS[nakshatra_index]

    if "across" in check and name in vedha_result.struck_nakshatras_across:
        return True
    if "fore" in check and name in vedha_result.struck_nakshatras_fore:
        return True
    return "hind" in check and name in vedha_result.struck_nakshatras_hind
