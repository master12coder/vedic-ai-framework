"""Per-planet weight factor computation for gemstone recommendations.

Each factor returns a WeightFactor with a multiplier that adjusts the
base ratti. Ten factors are computed per planet.
"""

from __future__ import annotations

from typing import Any

from daivai_products.plugins.remedies._gemstone_tables import (
    AVASTHA_MULT,
    BASE_DIVISOR,
    DIGNITY_MULT,
    GOOD_HOUSES,
    PURPOSE_MULT,
    STONE_ENERGY,
    TRIK_HOUSES,
)
from daivai_products.plugins.remedies.models import WeightFactor


def compute_factors(
    p: Any,
    planet: str,
    base: float,
    kg: float,
    sav: Any,
    md: Any,
    ad: Any,
    benefics: set[str],
    malefics: set[str],
    houses: list[int],
    stone: str,
    purpose: str,
) -> list[WeightFactor]:
    """Build all 10 weight factors for a single planet.

    Args:
        p: PlanetData for the planet being evaluated.
        planet: Planet name string.
        base: Base ratti (body_weight_kg / divisor).
        kg: Body weight in kilograms.
        sav: AshtakavargaResult from compute_ashtakavarga().
        md: Current Mahadasha DashaPeriod.
        ad: Current Antardasha DashaPeriod.
        benefics: Set of functional benefic planet names for this lagna.
        malefics: Set of functional malefic planet names for this lagna.
        houses: List of house numbers owned by this planet.
        stone: English stone name (for energy density lookup).
        purpose: 'protection', 'growth', or 'maximum'.

    Returns:
        List of 10 WeightFactor objects.
    """
    factors: list[WeightFactor] = []

    # 1. Body weight
    factors.append(
        WeightFactor(
            name="Body Weight",
            raw_value=f"{kg} kg",
            multiplier=1.00,
            explanation=f"Base = {kg} / {BASE_DIVISOR.get(planet, 10)} = {base:.1f} ratti",
        )
    )
    # 2. Avastha
    av_m = AVASTHA_MULT.get(p.avastha, 1.0)
    factors.append(
        WeightFactor(
            name="Avastha",
            raw_value=f"{p.avastha} ({p.degree_in_sign:.0f}°)",
            multiplier=av_m,
            explanation=_avastha_note(p.avastha),
        )
    )
    # 3. Ashtakavarga
    bav_m, bav_v = _ashtakavarga_factor(planet, p.sign_index, sav)
    factors.append(
        WeightFactor(
            name="Ashtakavarga",
            raw_value=f"{bav_v} bindus",
            multiplier=bav_m,
            explanation="Strong planet needs less stone"
            if bav_m < 1
            else "Average"
            if bav_m == 1
            else "Weak — needs more support",
        )
    )
    # 4. Dignity
    dig_m = DIGNITY_MULT.get(p.dignity, 1.0)
    factors.append(
        WeightFactor(
            name="Dignity",
            raw_value=p.dignity,
            multiplier=dig_m,
            explanation=_dignity_note(p.dignity),
        )
    )
    # 5. Combustion
    comb_m = 0.85 if p.is_combust else 1.0
    factors.append(
        WeightFactor(
            name="Combustion",
            raw_value="combust" if p.is_combust else "clear",
            multiplier=comb_m,
            explanation="Combust — stone effectiveness reduced" if p.is_combust else "Not combust",
        )
    )
    # 6. Retrograde
    factors.append(
        WeightFactor(
            name="Retrograde",
            raw_value="retrograde" if p.is_retrograde else "direct",
            multiplier=1.0,
            explanation="Retrograde — delayed effect, standard weight"
            if p.is_retrograde
            else "Direct motion",
        )
    )
    # 7. Current Dasha
    dasha_m = 0.85 if md.lord == planet else (0.90 if ad.lord == planet else 1.0)
    dasha_label = f"MD={md.lord}, AD={ad.lord}"
    factors.append(
        WeightFactor(
            name="Current Dasha",
            raw_value=dasha_label,
            multiplier=dasha_m,
            explanation=f"Running own {'MD' if md.lord == planet else 'AD'} — planet amplified, less stone needed"
            if dasha_m < 1
            else "Not in own dasha period",
        )
    )
    # 8. Lordship quality
    lord_m = _lordship_factor(planet, benefics, malefics, houses)
    factors.append(
        WeightFactor(
            name="Lordship",
            raw_value=f"houses {houses}",
            multiplier=lord_m,
            explanation="Pure benefic houses"
            if lord_m <= 0.90
            else "Mixed lordship"
            if lord_m <= 1.0
            else "Has trik house",
        )
    )
    # 9. Stone energy density
    se_m = STONE_ENERGY.get(stone, 1.0)
    factors.append(
        WeightFactor(
            name="Stone Energy",
            raw_value=stone,
            multiplier=se_m,
            explanation="High potency per ratti — less needed"
            if se_m < 1
            else "Standard energy density",
        )
    )
    # 10. Purpose
    pu_m = PURPOSE_MULT.get(purpose, 0.9)
    factors.append(
        WeightFactor(
            name="Purpose",
            raw_value=purpose,
            multiplier=pu_m,
            explanation={
                "protection": "Minimal for protection",
                "growth": "Moderate for growth",
                "maximum": "Full strength",
            }.get(purpose, purpose),
        )
    )
    return factors


# ── Internal helpers ──────────────────────────────────────────────────────


def _ashtakavarga_factor(planet: str, sign_idx: int, sav: Any) -> tuple[float, int]:
    """Return (multiplier, bindus) from Bhinnashtakavarga."""
    if planet in ("Rahu", "Ketu") or planet not in sav.bhinna:
        return 1.0, 0
    bindus = sav.bhinna[planet][sign_idx]
    if bindus <= 2:
        return 1.10, bindus
    if bindus <= 4:
        return 1.00, bindus
    if bindus <= 6:
        return 0.90, bindus
    return 0.80, bindus


def _lordship_factor(
    planet: str, benefics: set[str], malefics: set[str], houses: list[int]
) -> float:
    """Determine lordship quality multiplier from house ownership."""
    good = all(h in GOOD_HOUSES for h in houses) if houses else False
    has_trik = any(h in TRIK_HOUSES for h in houses)
    if planet in benefics and not has_trik and good:
        return 0.85
    if planet in benefics:
        return 0.95
    if planet in malefics:
        return 1.05
    return 1.00


def _avastha_note(avastha: str) -> str:
    """Human-readable explanation for planetary Avastha state."""
    notes = {
        "Bala": "Child state — planet developing, moderate stone",
        "Kumara": "Youth state — planet growing, near standard",
        "Yuva": "Prime state — full strength, standard weight",
        "Vriddha": "Old state — energy declining, less stone effective",
        "Mruta": "Deceased state — minimal energy, reduce weight",
    }
    return notes.get(avastha, "Unknown state")


def _dignity_note(dignity: str) -> str:
    """Human-readable explanation for planetary dignity."""
    notes = {
        "exalted": "Exalted — already strong, needs less stone",
        "mooltrikona": "Mooltrikona — very strong, less needed",
        "own": "Own sign — strong, moderate stone suffices",
        "neutral": "Neutral — standard weight applies",
        "enemy": "Enemy sign — slightly weakened",
        "debilitated": "Debilitated — stone fights debilitation, reduced effectiveness",
    }
    return notes.get(dignity, "Unknown dignity")
