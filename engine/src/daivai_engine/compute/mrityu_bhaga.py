"""Mrityu Bhaga (death degree) detection — BPHS and Jataka Parijata.

Each planet has a specific "death degree" in every sign. When a planet
occupies its Mrityu Bhaga degree (within orb), it suffers extreme weakness
regardless of other dignities such as exaltation or own-sign placement.

Orbs: ≤1° = severe, ≤3° = moderate, >3° = clear (no affliction).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from daivai_engine.constants import PLANETS, SIGNS, SIGNS_EN
from daivai_engine.models.chart import ChartData
from daivai_engine.models.mrityu_bhaga import MrityuBhagaResult


_DATA_FILE = Path(__file__).parent.parent / "knowledge" / "mrityu_bhaga.yaml"


def _load_data() -> dict:  # type: ignore[type-arg]
    """Load Mrityu Bhaga degree table from YAML (cached at module level)."""
    with _DATA_FILE.open() as fh:
        data: dict = yaml.safe_load(fh)  # type: ignore[assignment]
        return data


_DATA = _load_data()
_DEGREES: dict[str, list[int]] = _DATA["degrees"]
_ORB_SEVERE: float = float(_DATA["orbs"]["severe"])
_ORB_MODERATE: float = float(_DATA["orbs"]["moderate"])

# All bodies checked: 9 planets + Lagna
_BODIES = [*PLANETS, "Lagna"]


def _severity(distance: float) -> str:
    """Classify affliction severity based on distance from Mrityu Bhaga."""
    if distance <= _ORB_SEVERE:
        return "severe"
    if distance <= _ORB_MODERATE:
        return "moderate"
    return "clear"


def _check_body(
    body: str,
    sign_index: int,
    actual_degree: float,
) -> MrityuBhagaResult:
    """Build one MrityuBhagaResult for a body at a given sign position."""
    mrityu_deg = _DEGREES[body][sign_index]
    distance = abs(actual_degree - mrityu_deg)
    return MrityuBhagaResult(
        body=body,
        sign_index=sign_index,
        sign=SIGNS[sign_index],
        sign_en=SIGNS_EN[sign_index],
        mrityu_degree=mrityu_deg,
        actual_degree=actual_degree,
        distance=distance,
        severity=_severity(distance),
    )


def check_mrityu_bhaga(chart: ChartData) -> list[MrityuBhagaResult]:
    """Check every planet and Lagna for Mrityu Bhaga affliction.

    For each body, determines whether it falls within the severe (≤1°) or
    moderate (≤3°) orb of its tabulated Mrityu Bhaga degree in the sign it
    currently occupies.

    Args:
        chart: A fully computed birth chart with planetary positions.

    Returns:
        List of MrityuBhagaResult — one entry per body (10 total: 9 planets
        + Lagna), ordered as Sun … Ketu, then Lagna.
        Only ``severity != "clear"`` entries represent actual afflictions.
    """
    results: list[MrityuBhagaResult] = []

    for planet in PLANETS:
        p = chart.planets[planet]
        results.append(_check_body(planet, p.sign_index, p.degree_in_sign))

    # Lagna
    results.append(_check_body("Lagna", chart.lagna_sign_index, chart.lagna_degree))

    return results


def get_afflicted_bodies(chart: ChartData) -> list[MrityuBhagaResult]:
    """Return only the bodies that are within Mrityu Bhaga orb (severe or moderate).

    Args:
        chart: A fully computed birth chart.

    Returns:
        Filtered list of results where severity is "severe" or "moderate".
    """
    return [r for r in check_mrityu_bhaga(chart) if r.severity != "clear"]
