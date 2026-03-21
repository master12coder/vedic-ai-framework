"""Advanced Dasha features — Sandhi, Sookshma (L4), Prana (L5).

Extends the existing 3-level dasha system to 5 levels for precision timing.
Also computes dasha sandhi (junction turbulence periods).

Source: BPHS Dasha chapter, Laghu Parashari.
"""

from __future__ import annotations

from datetime import timedelta

from pydantic import BaseModel

from daivai_engine.constants import DASHA_SEQUENCE, DASHA_TOTAL_YEARS, DASHA_YEARS
from daivai_engine.models.dasha import DashaPeriod


class DashaSandhi(BaseModel):
    """Junction period between two dasha transitions."""

    ending_lord: str
    starting_lord: str
    sandhi_start: str  # ISO datetime
    sandhi_end: str
    nature: str  # easy / challenging / transformative
    severity: int = 1  # 1=mild, 2=moderate, 3=severe
    is_malefic_transition: bool = False  # Both lords are natural malefics
    level: str = "MD"  # MD or AD
    description: str


def compute_dasha_sandhi(mahadashas: list[DashaPeriod]) -> list[DashaSandhi]:
    """Compute sandhi (junction) periods between Mahadashas.

    The last 10% of ending dasha + first 10% of starting dasha
    is a turbulent transition period.

    Source: Laghu Parashari, widely used in practice.
    """
    results: list[DashaSandhi] = []
    for i in range(len(mahadashas) - 1):
        ending = mahadashas[i]
        starting = mahadashas[i + 1]

        ending_duration = (ending.end - ending.start).total_seconds()
        starting_duration = (starting.end - starting.start).total_seconds()

        # Last 10% of ending + first 10% of starting
        sandhi_start = ending.end - timedelta(seconds=ending_duration * 0.1)
        sandhi_end = starting.start + timedelta(seconds=starting_duration * 0.1)

        nature, severity = _classify_transition(ending.lord, starting.lord)
        is_malefic = ending.lord in _NATURAL_MALEFICS and starting.lord in _NATURAL_MALEFICS

        results.append(
            DashaSandhi(
                ending_lord=ending.lord,
                starting_lord=starting.lord,
                sandhi_start=sandhi_start.isoformat(),
                sandhi_end=sandhi_end.isoformat(),
                nature=nature,
                severity=severity,
                is_malefic_transition=is_malefic,
                level="MD",
                description=f"{ending.lord} → {starting.lord} transition ({nature}, severity {severity})",
            )
        )

    return results


def compute_sookshma_dasha(pd: DashaPeriod) -> list[DashaPeriod]:
    """Compute Sookshma Dasha (Level 4) from a Pratyantardasha.

    Same proportional division as PD→SD.
    Duration = PD_duration * (lord_years / 120).

    Source: BPHS Dasha chapter.
    """
    return _subdivide(pd, "SD")


def compute_prana_dasha(sd: DashaPeriod) -> list[DashaPeriod]:
    """Compute Prana Dasha (Level 5) from a Sookshma Dasha.

    Finest level. Used for pinpointing exact dates.

    Source: BPHS Dasha chapter.
    """
    return _subdivide(sd, "PR")


def _subdivide(parent: DashaPeriod, level: str) -> list[DashaPeriod]:
    """Subdivide a dasha period into 9 sub-periods proportionally."""
    parent_days = (parent.end - parent.start).total_seconds() / 86400.0
    start_idx = DASHA_SEQUENCE.index(parent.lord)

    results: list[DashaPeriod] = []
    current = parent.start

    for i in range(9):
        lord = DASHA_SEQUENCE[(start_idx + i) % 9]
        duration_days = parent_days * DASHA_YEARS[lord] / DASHA_TOTAL_YEARS
        end = current + timedelta(days=duration_days)
        results.append(
            DashaPeriod(
                level=level,
                lord=lord,
                start=current,
                end=end,
                parent_lord=parent.lord,
            )
        )
        current = end

    return results


_NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
_NATURAL_BENEFICS = {"Jupiter", "Venus", "Moon", "Mercury"}


def _classify_transition(ending: str, starting: str) -> tuple[str, int]:
    """Classify the nature and severity of a dasha transition.

    Returns:
        (nature, severity) — nature is easy/challenging/transformative;
        severity is 1 (mild), 2 (moderate), or 3 (severe).
    """
    e_malefic = ending in _NATURAL_MALEFICS
    s_malefic = starting in _NATURAL_MALEFICS
    if not e_malefic and not s_malefic:
        return "easy", 1
    if e_malefic and s_malefic:
        return "challenging", 3
    return "transformative", 2


def detect_dasha_sandhi(
    mahadashas: list[DashaPeriod],
    antardashas: list[DashaPeriod] | None = None,
) -> list[DashaSandhi]:
    """Detect sandhi at MD level and optionally AD level.

    Extends compute_dasha_sandhi to handle Antardasha transitions as well.
    Malefic-to-malefic transitions are flagged with severity 3.

    Args:
        mahadashas: List of 9 Mahadasha periods.
        antardashas: Optional list of Antardasha periods for finer detection.

    Returns:
        Combined list of MD and AD sandhi periods.
    """
    results = compute_dasha_sandhi(mahadashas)

    if antardashas:
        for i in range(len(antardashas) - 1):
            ending = antardashas[i]
            starting = antardashas[i + 1]

            ending_dur = (ending.end - ending.start).total_seconds()
            starting_dur = (starting.end - starting.start).total_seconds()

            sandhi_start = ending.end - timedelta(seconds=ending_dur * 0.1)
            sandhi_end = starting.start + timedelta(seconds=starting_dur * 0.1)

            nature, severity = _classify_transition(ending.lord, starting.lord)
            is_malefic = ending.lord in _NATURAL_MALEFICS and starting.lord in _NATURAL_MALEFICS

            results.append(
                DashaSandhi(
                    ending_lord=ending.lord,
                    starting_lord=starting.lord,
                    sandhi_start=sandhi_start.isoformat(),
                    sandhi_end=sandhi_end.isoformat(),
                    nature=nature,
                    severity=severity,
                    is_malefic_transition=is_malefic,
                    level="AD",
                    description=(
                        f"[AD] {ending.lord} → {starting.lord} ({nature}, severity {severity})"
                    ),
                )
            )

    return results
