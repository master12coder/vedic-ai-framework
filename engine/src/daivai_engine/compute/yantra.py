"""Yantra computation - planetary magic squares and remedy yantra selection.

Constructs the 3x3 Navagraha magic squares using the Lo Shu offset algorithm
and derives a personalized yantra plan from chart analysis.

Algorithm:
  Vedic planet numbers: Sun=1, Moon=2, Jupiter=3, Rahu=4, Mercury=5,
                        Venus=6, Ketu=7, Saturn=8, Mars=9
  Offset for planet k: (k - 1) * 9
  Base Lo Shu grid:
    2  7  6
    9  5  1
    4  3  8
  Add offset to each cell -> planet's magic square (magic_sum = 15 + offset * 3).

Source: Yantra Chintamani, Sri Yantra Sarvasva, traditional Navagraha texts.
"""

from __future__ import annotations

from typing import cast

from daivai_engine.constants import SIGN_LORDS
from daivai_engine.knowledge.loader import load_yantra_data
from daivai_engine.models.chart import ChartData
from daivai_engine.models.remedies import YantraRecommendation


# ── Lo Shu base grid (row-major) ──────────────────────────────────────────────

_LO_SHU: list[list[int]] = [
    [2, 7, 6],
    [9, 5, 1],
    [4, 3, 8],
]

# Vedic planet -> number (1-based)
_VEDIC_NUMBERS: dict[str, int] = {
    "Sun": 1,
    "Moon": 2,
    "Jupiter": 3,
    "Rahu": 4,
    "Mercury": 5,
    "Venus": 6,
    "Ketu": 7,
    "Saturn": 8,
    "Mars": 9,
}


def construct_yantra_grid(planet: str) -> list[list[int]]:
    """Construct the 3x3 magic square for a planet using the Lo Shu offset.

    Each planet has a Vedic number k (1-9). The offset = (k - 1) * 9 is
    added to every cell of the base Lo Shu grid to produce the planet's
    unique magic square.

    Args:
        planet: Planet name - one of the 9 Vedic grahas.

    Returns:
        3x3 list of lists with the planet's magic square.

    Raises:
        ValueError: If the planet name is not recognised.
    """
    k = _VEDIC_NUMBERS.get(planet)
    if k is None:
        raise ValueError(f"Unknown planet for yantra construction: {planet!r}")
    offset = (k - 1) * 9
    return [[cell + offset for cell in row] for row in _LO_SHU]


def validate_yantra(grid: list[list[int]]) -> bool:
    """Verify that a 3x3 grid is a valid magic square.

    Checks that all rows, columns, and both diagonals sum to the same value.

    Args:
        grid: 3x3 list of lists of integers.

    Returns:
        True if all sums are equal, False otherwise.
    """
    if len(grid) != 3 or any(len(row) != 3 for row in grid):
        return False
    target = sum(grid[0])
    # rows
    if any(sum(row) != target for row in grid):
        return False
    # columns
    if any(sum(grid[r][c] for r in range(3)) != target for c in range(3)):
        return False
    # diagonals
    if sum(grid[i][i] for i in range(3)) != target:
        return False
    return sum(grid[i][2 - i] for i in range(3)) == target


def get_yantra_data(planet: str) -> YantraRecommendation | None:
    """Return full yantra data for a planet, loaded from YAML + computed grid.

    Combines the static YAML metadata (material, installation instructions,
    purpose) with the algorithmically constructed magic square.

    Args:
        planet: Planet name.

    Returns:
        YantraRecommendation or None if not found in YAML.
    """
    data = load_yantra_data()
    yantras = data.get("yantras", {})
    entry = yantras.get(planet)
    if not entry:
        return None

    grid = construct_yantra_grid(planet)
    install = entry.get("installation", {})

    return YantraRecommendation(
        planet=planet,
        planet_hi=entry.get("name_hi", ""),
        vedic_number=entry["vedic_number"],
        grid=grid,
        magic_sum=entry["magic_sum"],
        center_number=entry["center_number"],
        material_primary=entry.get("material", {}).get("primary", ""),
        installation_day=install.get("day", ""),
        installation_time=install.get("time", ""),
        energizing_mantra=install.get("mantra_for_energizing", ""),
        purpose=entry.get("purpose", []),
        reason="",  # caller fills this in
    )


def _with_reason(rec: YantraRecommendation, reason: str) -> YantraRecommendation:
    """Return a copy of YantraRecommendation with a specific reason set."""
    return cast(YantraRecommendation, rec.model_copy(update={"reason": reason}))


def compute_remedy_yantras(chart: ChartData) -> list[YantraRecommendation]:
    """Derive personalized yantra recommendations from a birth chart.

    Priority order (duplicates de-duped by planet):
      1. Lagna lord yantra - always installed to protect the native.
      2. Moon nakshatra lord yantra - pacify current Vimshottari dasha.
      3. Debilitated planet yantras - restore planetary strength.
      4. Combust planet yantras - unblock suppressed significations.

    Returns at most 3 yantras - installing too many simultaneously
    dilutes the energy and creates conflicting vibrations.

    Args:
        chart: Computed birth chart.

    Returns:
        Ordered list of YantraRecommendation, highest priority first.
    """
    seen: dict[str, YantraRecommendation] = {}

    def _add(planet: str, reason: str) -> None:
        if planet in seen:
            return
        rec = get_yantra_data(planet)
        if rec:
            seen[planet] = _with_reason(rec, reason)

    # 1. Lagna lord
    lagna_lord = SIGN_LORDS.get(chart.lagna_sign_index, "")
    if lagna_lord:
        _add(lagna_lord, f"Lagna lord yantra - protects {chart.lagna_sign} lagna natives")

    # 2. Current dasha lord (Moon nakshatra lord as proxy)
    moon = chart.planets.get("Moon")
    if moon and moon.nakshatra_lord and moon.nakshatra_lord != lagna_lord:
        _add(
            moon.nakshatra_lord,
            f"Dasha lord yantra (Moon in {moon.nakshatra}) - harmonise current period",
        )

    # 3. Debilitated planets
    for pname, pdata in chart.planets.items():
        if pname in seen:
            continue
        if pdata.dignity == "debilitated":
            _add(pname, f"{pname} debilitated in {pdata.sign} - yantra restores strength")

    # 4. Combust planets
    for pname, pdata in chart.planets.items():
        if pname in seen:
            continue
        if pdata.is_combust and pname not in ("Sun", "Rahu", "Ketu"):
            _add(pname, f"{pname} combust - yantra unblocks its significations")

    return list(seen.values())[:3]
