"""Kalachakra Dasha — "most respectable dasha" per Parashar (BPHS Ch.46).

Loads all lookup tables from knowledge/kalachakra_dasha_data.yaml.
No hardcoded sequences — the YAML is the single source of truth.
Every output includes provenance (source citation, confidence, alternatives).

Source: BPHS Chapter 46 "Kalachakra Dasha Adhyaya"
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from daivai_engine.constants import SIGNS, SIGNS_HI
from daivai_engine.models.chart import ChartData


_DATA_FILE = Path(__file__).parent.parent / "knowledge" / "kalachakra_dasha_data.yaml"
_DATA: dict[str, Any] | None = None
_PADA_SPAN_DEG = 10.0 / 3.0  # 3.3333 degrees = 3 deg 20 min


def _load() -> dict[str, Any]:
    """Load and cache the Kalachakra YAML data."""
    global _DATA
    if _DATA is None:
        with open(_DATA_FILE) as f:
            _DATA = yaml.safe_load(f)
    return _DATA


class GatiJump(BaseModel):
    """A non-linear jump detected in a Kalachakra sequence."""

    model_config = ConfigDict(frozen=True)

    gati_type: str  # simhavalokana / manduka / markati
    gati_name_hi: str
    from_sign: int
    to_sign: int
    from_sign_name: str
    to_sign_name: str
    description: str
    severity: str  # severe / moderate
    source: str


class KalachakraDashaPeriod(BaseModel):
    """One period in the Kalachakra Dasha sequence."""

    model_config = ConfigDict(frozen=True)

    sign_index: int
    sign_name: str
    sign_hi: str
    years: int
    start: datetime
    end: datetime
    is_deha: bool
    is_jeeva: bool
    cycle: str


class KalachakraDashaResult(BaseModel):
    """Complete Kalachakra Dasha result with provenance."""

    model_config = ConfigDict(frozen=True)

    group: str
    nakshatra: str
    pada: int
    paramayus: int
    balance_years: float
    deha_sign: int
    deha_sign_name: str
    jeeva_sign: int
    jeeva_sign_name: str
    periods: list[KalachakraDashaPeriod]
    gatis: list[GatiJump]
    source: str
    confidence: str


def compute_kalachakra_dasha(chart: ChartData) -> KalachakraDashaResult:
    """Compute Kalachakra Dasha from YAML-driven 108-pada mapping.

    All lookup tables loaded from knowledge/kalachakra_dasha_data.yaml.
    Every output includes source citation from BPHS Ch.46.

    Args:
        chart: Computed birth chart.

    Returns:
        KalachakraDashaResult with gatis, deha/jeeva, and provenance.
    """
    data = _load()
    sign_years = {int(k): int(v) for k, v in data["sign_years"]["values"].items()}
    moon = chart.planets["Moon"]

    # Classify nakshatra into group
    group = _classify_group(moon.nakshatra, data)

    # Get pada sequence from YAML
    pada_key = f"pada_{moon.pada}"
    pada_data = data["sequences"][group][pada_key]
    seq = pada_data["signs"]
    deha = pada_data["deha"]
    jeeva = pada_data["jeeva"]
    paramayus = pada_data["paramayus"]
    source = pada_data.get("source", "BPHS Ch.46")

    # Build Gati objects
    gatis = _build_gatis(pada_data.get("gatis", []), data, source)

    # Balance calculation (BPHS Ch.46: fraction of pada remaining x first sign years)
    nak_start = moon.nakshatra_index * (360.0 / 27.0)
    pada_start = nak_start + (moon.pada - 1) * _PADA_SPAN_DEG
    pada_end = pada_start + _PADA_SPAN_DEG
    remaining = pada_end - moon.longitude
    if remaining < 0:
        remaining += 360.0
    balance_frac = min(1.0, max(0.0, remaining / _PADA_SPAN_DEG))
    balance_years = sign_years[seq[0]] * balance_frac

    # Generate periods
    from daivai_engine.compute.datetime_utils import parse_birth_datetime

    birth_dt = parse_birth_datetime(chart.dob, chart.tob, chart.timezone_name)
    periods: list[KalachakraDashaPeriod] = []
    current = birth_dt
    for i, sign_idx in enumerate(seq):
        yrs = sign_years[sign_idx]
        actual = balance_years if i == 0 else float(yrs)
        end = current + timedelta(days=actual * 365.25)
        periods.append(
            KalachakraDashaPeriod(
                sign_index=sign_idx,
                sign_name=SIGNS[sign_idx],
                sign_hi=SIGNS_HI[sign_idx],
                years=yrs,
                start=current,
                end=end,
                is_deha=(sign_idx == deha),
                is_jeeva=(sign_idx == jeeva),
                cycle=group,
            )
        )
        current = end

    return KalachakraDashaResult(
        group=group,
        nakshatra=moon.nakshatra,
        pada=moon.pada,
        paramayus=paramayus,
        balance_years=round(balance_years, 4),
        deha_sign=deha,
        deha_sign_name=SIGNS[deha],
        jeeva_sign=jeeva,
        jeeva_sign_name=SIGNS[jeeva],
        periods=periods,
        gatis=gatis,
        source=source,
        confidence=data["metadata"]["confidence"],
    )


def _classify_group(nakshatra: str, data: dict[str, Any]) -> str:
    """Classify nakshatra into one of 4 groups from YAML data."""
    groups = data["nakshatra_groups"]
    for group_name in ("savya_i", "savya_ii", "apasavya_i", "apasavya_ii"):
        if nakshatra in groups[group_name]["nakshatras"]:
            return group_name
    return "savya_i"


def _build_gatis(
    raw_gatis: list[dict[str, Any]], data: dict[str, Any], fallback_source: str
) -> list[GatiJump]:
    """Build GatiJump objects from YAML gati data."""
    gati_defs = data.get("gati_types", {}).get("types", {})
    result: list[GatiJump] = []
    for g in raw_gatis:
        gtype = g["type"]
        gdef = gati_defs.get(gtype, {})
        result.append(
            GatiJump(
                gati_type=gtype,
                gati_name_hi=gdef.get("name_hi", ""),
                from_sign=g["from_sign"],
                to_sign=g["to_sign"],
                from_sign_name=SIGNS[g["from_sign"]],
                to_sign_name=SIGNS[g["to_sign"]],
                description=g.get("description", ""),
                severity=gdef.get("severity", "moderate"),
                source=g.get("source", fallback_source),
            )
        )
    return result
