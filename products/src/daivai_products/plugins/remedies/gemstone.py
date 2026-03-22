"""Multi-factor gemstone weight engine — 10 chart-based factors for personalized ratti.

Computes recommended gemstone weight using planetary strength indicators from the
birth chart. Each stone gets a base weight (body_weight_kg / divisor) modified by
10 astrological factors. Includes website comparison and free alternatives.

Public API:
    compute_gemstone_weights(chart, body_weight_kg, purpose) -> list[GemstoneWeightResult]

Sub-modules:
    _gemstone_tables  — lookup tables (divisors, stone names, multipliers, free alts)
    _gemstone_factors — per-planet factor computation (10 factors)
    models            — Pydantic result models (WeightFactor, GemstoneWeightResult)
"""

from __future__ import annotations

from daivai_engine.compute.ashtakavarga import compute_ashtakavarga
from daivai_engine.compute.dasha import find_current_dasha
from daivai_engine.models.chart import ChartData
from daivai_products.interpret.context import build_lordship_context
from daivai_products.plugins.remedies._gemstone_factors import compute_factors
from daivai_products.plugins.remedies._gemstone_tables import (
    AVASTHA_MULT,
    BASE_DIVISOR,
    DIGNITY_MULT,
    FREE_ALT,
    PLANET_STONE,
    PURPOSE_MULT,
    STONE_ENERGY,
)
from daivai_products.plugins.remedies.models import GemstoneWeightResult, WeightFactor


# Re-export tables that external code may reference
_BASE_DIVISOR = BASE_DIVISOR
_FREE_ALT = FREE_ALT

__all__ = [
    "AVASTHA_MULT",
    "DIGNITY_MULT",
    "PLANET_STONE",
    "PURPOSE_MULT",
    "STONE_ENERGY",
    "GemstoneWeightResult",
    "WeightFactor",
    "compute_gemstone_weights",
]


def compute_gemstone_weights(
    chart: ChartData,
    body_weight_kg: float,
    purpose: str = "growth",
) -> list[GemstoneWeightResult]:
    """Compute personalized gemstone weights for all 9 planetary stones.

    Args:
        chart: Computed birth chart.
        body_weight_kg: Native's body weight in kg.
        purpose: 'protection', 'growth', or 'maximum'.

    Returns:
        List of GemstoneWeightResult — one per planet, sorted: recommended first,
        then test_with_caution, then prohibited.
    """
    ctx = build_lordship_context(chart.lagna_sign)
    if not ctx:
        return []

    ashtakavarga = compute_ashtakavarga(chart)
    md, ad, _pd = find_current_dasha(chart)

    rec_map = _build_recommendation_map(ctx)
    benefics = {e["planet"] for e in ctx.get("functional_benefics", [])}
    malefics = {e["planet"] for e in ctx.get("functional_malefics", [])}
    houses_map = _build_houses_map(ctx)

    results: list[GemstoneWeightResult] = []
    for planet, (stone_en, stone_hi) in PLANET_STONE.items():
        status, reason = rec_map.get(planet, ("neutral", ""))
        if status == "prohibited":
            results.append(_prohibited_result(planet, stone_en, stone_hi, reason))
            continue

        p_data = chart.planets.get(planet)
        if p_data is None:
            continue

        base = body_weight_kg / BASE_DIVISOR.get(planet, 10)
        factors = compute_factors(
            p_data,
            planet,
            base,
            body_weight_kg,
            ashtakavarga,
            md,
            ad,
            benefics,
            malefics,
            houses_map.get(planet, []),
            stone_en,
            purpose,
        )
        total_mult = 1.0
        for f in factors:
            total_mult *= f.multiplier
        recommended = round(base * total_mult * 4) / 4  # round to nearest 0.25
        recommended = max(recommended, 1.0)  # absolute floor 1 ratti

        results.append(
            GemstoneWeightResult(
                planet=planet,
                stone_name=stone_en,
                stone_name_hi=stone_hi,
                status="recommended" if status == "recommended" else "test_with_caution",
                base_ratti=round(base, 2),
                recommended_ratti=recommended,
                factors=factors,
                website_comparisons=_website_estimates(body_weight_kg, planet),
                pros_cons=_pros_cons(recommended, base),
                free_alternatives=FREE_ALT.get(planet, {}),
                prohibition_reason=None,
            )
        )

    order = {"recommended": 0, "test_with_caution": 1, "prohibited": 2}
    results.sort(key=lambda r: order.get(r.status, 9))
    return results


# ── Helpers ──────────────────────────────────────────────────────────────


def _build_recommendation_map(ctx: dict) -> dict[str, tuple[str, str]]:
    """Map planet name → (status, reason) from lordship context."""
    m: dict[str, tuple[str, str]] = {}
    for s in ctx.get("recommended_stones", []):
        m[s["planet"]] = ("recommended", s.get("reasoning", ""))
    for s in ctx.get("test_stones", []):
        m[s["planet"]] = ("test", s.get("reasoning", ""))
    for s in ctx.get("prohibited_stones", []):
        m[s["planet"]] = ("prohibited", s.get("reasoning", ""))
    return m


def _build_houses_map(ctx: dict) -> dict[str, list[int]]:
    """Map planet → list of houses owned from house_lords."""
    result: dict[str, list[int]] = {}
    for house_str, planet in ctx.get("house_lords", {}).items():
        result.setdefault(planet, []).append(int(house_str))
    return result


def _prohibited_result(
    planet: str, stone_en: str, stone_hi: str, reason: str
) -> GemstoneWeightResult:
    """Build a GemstoneWeightResult for a prohibited stone."""
    return GemstoneWeightResult(
        planet=planet,
        stone_name=stone_en,
        stone_name_hi=stone_hi,
        status="prohibited",
        base_ratti=0,
        recommended_ratti=0,
        factors=[],
        website_comparisons={},
        pros_cons={},
        free_alternatives=FREE_ALT.get(planet, {}),
        prohibition_reason=reason[:120] if reason else f"{planet} stone prohibited for this lagna",
    )


def _website_estimates(kg: float, planet: str) -> dict[str, float]:
    """Static estimates from popular gemstone websites (body-weight-based)."""
    base = kg / BASE_DIVISOR.get(planet, 10)
    return {
        "GemPundit": round(base, 1),
        "BrahmaGems": round(max(3.0, base * 0.9), 1),
        "GemsMantra": round(base + 1.0, 1),
        "ShubhGems": round(max(5.0, base * 1.2), 1),
        "MyRatna": round(base, 1),
    }


def _pros_cons(rec: float, base: float) -> dict[str, list[str]]:
    """Generate pros/cons for light, medium, heavy weight."""
    light = max(1.0, rec * 0.7)
    heavy = rec * 1.4
    return {
        f"Light ({light:.1f}r)": [
            "Lower cost, easier to source high quality",
            "Subtle effect — good for sensitive people",
            "May not be enough for severely afflicted planet",
        ],
        f"Medium ({rec:.1f}r)": [
            "Balanced cost and effectiveness",
            "Computed recommendation based on 10 chart factors",
            "Best starting point for most natives",
        ],
        f"Heavy ({heavy:.1f}r)": [
            "Stronger effect for severely weak planet",
            "Higher cost, quality harder to maintain",
            "Risk of over-activation if planet has mixed lordship",
        ],
    }
