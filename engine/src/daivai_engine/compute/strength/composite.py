"""Composite Shadbala aggregation — final computation and backward-compat API.

Assembles all six Shadbala components and provides the backward-compatible
``compute_planet_strengths`` API used by interpreters and formatters.
Source: BPHS Chapter 23.
"""

from __future__ import annotations

from daivai_engine.compute.strength.cheshta_bala import (
    SHADBALA_PLANETS,
    compute_cheshta_bala,
    compute_dig_bala,
    compute_drik_bala,
    compute_yuddha_bala_adjustments,
)
from daivai_engine.compute.strength.kala_bala import compute_kala_bala
from daivai_engine.compute.strength.sthana_bala import compute_sthana_bala
from daivai_engine.models.chart import ChartData
from daivai_engine.models.strength import PlanetStrength, ShadbalaResult


# Naisargika Bala (natural strength) — fixed values in shashtiyamsas
# Fractions of 60: Sun=60*7/7, Moon=60*6/7, Mars=60*2/7, Mercury=60*3/7,
# Jupiter=60*4/7, Venus=60*5/7, Saturn=60*1/7  (BPHS Ch.23)
NAISARGIKA: dict[str, float] = {
    "Sun": 60.00,
    "Moon": 51.43,
    "Mars": 17.14,
    "Mercury": 25.71,
    "Jupiter": 34.29,
    "Venus": 42.86,
    "Saturn": 8.57,
}

# Minimum required total Shadbala (shashtiyamsas)
REQUIRED_SHADBALA: dict[str, float] = {
    "Sun": 390.0,
    "Moon": 360.0,
    "Mars": 300.0,
    "Mercury": 420.0,
    "Jupiter": 390.0,
    "Venus": 330.0,
    "Saturn": 300.0,
}


def _naisargika_bala(planet_name: str) -> float:
    """Fixed natural strength per planet."""
    return NAISARGIKA.get(planet_name, 0.0)


def compute_shadbala(chart: ChartData) -> list[ShadbalaResult]:
    """Compute full six-fold Shadbala for the seven classical planets.

    Returns a list of ShadbalaResult sorted by total (descending), with
    ranks assigned (1 = strongest).
    """
    results: list[ShadbalaResult] = []
    yuddha_adj = compute_yuddha_bala_adjustments(chart)

    for planet_name in SHADBALA_PLANETS:
        sb = compute_sthana_bala(chart, planet_name)
        db = compute_dig_bala(chart, planet_name)
        kb = compute_kala_bala(chart, planet_name)
        cb = compute_cheshta_bala(chart, planet_name)
        nb = _naisargika_bala(planet_name)
        drk = compute_drik_bala(chart, planet_name)
        yb = yuddha_adj.get(planet_name, 0.0)
        total = round(sb + db + kb + cb + nb + drk + yb, 2)
        req = REQUIRED_SHADBALA[planet_name]
        ratio = round(total / req, 3) if req > 0 else 0.0

        results.append(
            ShadbalaResult(
                planet=planet_name,
                sthana_bala=sb,
                dig_bala=db,
                kala_bala=kb,
                cheshta_bala=cb,
                naisargika_bala=nb,
                drik_bala=drk,
                yuddha_bala=yb,
                total=total,
                required=req,
                ratio=ratio,
                is_strong=ratio >= 1.0,
                rank=0,
            )
        )

    # Assign ranks by total descending
    results.sort(key=lambda r: r.total, reverse=True)
    for i, r in enumerate(results):
        r.rank = i + 1

    return results


def compute_planet_strengths(chart: ChartData) -> list[PlanetStrength]:
    """Compute relative strengths for all planets (backward-compatible).

    Wraps the full Shadbala for the 7 classical planets and adds simplified
    entries for Rahu and Ketu to maintain API compatibility.
    """
    shadbala = compute_shadbala(chart)
    strengths: list[PlanetStrength] = []

    # Build a lookup for ratio-based normalization
    max_total = max(r.total for r in shadbala) if shadbala else 1.0

    for r in shadbala:
        # Normalize to 0-1 range for backward compatibility
        norm_sthana = min(1.0, r.sthana_bala / 180.0)
        norm_dig = min(1.0, r.dig_bala / 60.0)
        norm_kala = min(1.0, r.kala_bala / 120.0)
        total_rel = min(1.0, r.total / max_total) if max_total > 0 else 0.0

        strengths.append(
            PlanetStrength(
                planet=r.planet,
                sthana_bala=round(norm_sthana, 3),
                dig_bala=round(norm_dig, 3),
                kala_bala=round(norm_kala, 3),
                total_relative=round(total_rel, 3),
                rank=0,
                is_strong=r.is_strong,
            )
        )

    # Add simplified entries for Rahu and Ketu
    for node_name in ("Rahu", "Ketu"):
        if node_name in chart.planets:
            p = chart.planets[node_name]
            dignity_scores = {
                "exalted": 1.0,
                "mooltrikona": 0.85,
                "own": 0.75,
                "neutral": 0.4,
                "debilitated": 0.1,
            }
            sb = dignity_scores.get(p.dignity, 0.4)
            # Simplified dig/kala for nodes
            db = 0.5
            kb = 0.5
            total_rel = sb * 0.5 + db * 0.25 + kb * 0.25
            strengths.append(
                PlanetStrength(
                    planet=node_name,
                    sthana_bala=round(sb, 3),
                    dig_bala=round(db, 3),
                    kala_bala=round(kb, 3),
                    total_relative=round(total_rel, 3),
                    rank=0,
                    is_strong=total_rel >= 0.55,
                )
            )

    # Assign ranks by total_relative descending
    strengths.sort(key=lambda s: s.total_relative, reverse=True)
    for i, s in enumerate(strengths):
        s.rank = i + 1

    return strengths


def get_strongest_planet(chart: ChartData) -> str:
    """Return the name of the strongest planet in the chart."""
    strengths = compute_planet_strengths(chart)
    return strengths[0].planet


def get_weakest_planet(chart: ChartData) -> str:
    """Return the name of the weakest planet in the chart."""
    strengths = compute_planet_strengths(chart)
    return strengths[-1].planet
