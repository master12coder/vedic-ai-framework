"""Parivartana Yoga detection — mutual sign exchange between two house lords.

Checks all 66 possible house pairs (C(12,2) = 66).

Classification per BPHS, Phaladeepika, and Saravali:
  Maha:   Both houses are kendra/trikona (1, 4, 5, 7, 9, 10)
  Khala:  One or both houses are 2, 3, or 11
  Dainya: One or both houses are dusthana (6, 8, 12)

Also provides:
  - is_vargottama(): D1-D9 agreement check for any planet
  - apply_yoga_strength(): post-processor for combustion / retrograde / vargottama
"""

from __future__ import annotations

from itertools import combinations

from daivai_engine.compute.chart import ChartData, get_house_lord
from daivai_engine.models.chart import PlanetData
from daivai_engine.models.yoga import YogaResult


# ── D9 start sign by sign element (BPHS navamsha table) ─────────────────────
# Fire (0,4,8) → Aries (0); Earth (1,5,9) → Capricorn (9)
# Air  (2,6,10)→ Libra (6); Water(3,7,11) → Cancer   (3)
_D9_START: dict[int, int] = {s: [0, 9, 6, 3][s % 4] for s in range(12)}

# ── House type sets for Parivartana classification ───────────────────────────
_MAHA_HOUSES = frozenset([1, 4, 5, 7, 9, 10])  # kendra + trikona
_KHALA_HOUSES = frozenset([2, 3, 11])  # upachaya (non-dusthana)
_DAINYA_HOUSES = frozenset([6, 8, 12])  # dusthana


# ── Vargottama utility ────────────────────────────────────────────────────────


def is_vargottama(planet: PlanetData) -> bool:
    """Return True if planet occupies the same sign in D1 and D9 (Navamsha).

    A Vargottama planet is considered extremely powerful — its essential
    dignity from D1 persists through all 9 navamsha divisions.

    Computation: D9 sign = (d9_start_for_element + navamsha_index) % 12
    where navamsha_index = int(degree_in_sign * 9 / 30).

    Source: BPHS Ch.6 v.14; Phaladeepika Ch.2.

    Args:
        planet: PlanetData with sign_index and degree_in_sign fields.

    Returns:
        True if the planet's D9 sign equals its D1 sign.
    """
    nav_idx = int(planet.degree_in_sign * 9 / 30)  # 0-8
    d9_sign = (_D9_START[planet.sign_index] + nav_idx) % 12
    return d9_sign == planet.sign_index


# ── Yoga strength post-processor ──────────────────────────────────────────────


def apply_yoga_strength(yogas: list[YogaResult], chart: ChartData) -> list[YogaResult]:
    """Apply combustion, debilitation, retrograde, and Vargottama modifiers.

    Rules applied in priority order:
      1. Yoga planet combust AND debilitated → "cancelled"
      2. Yoga planet combust OR debilitated (benefic yoga) → "partial"
      3. Yoga planet Vargottama OR retrograde (benefic yoga) → "enhanced"
      4. Default → unchanged (typically "full")

    Malefic yogas (effect="malefic") are not upgraded to "enhanced".
    Strength set during yoga detection (e.g. Hina Adhi) is only downgraded,
    never upgraded beyond what detection already set.

    Args:
        yogas: Detected yoga results (may already have non-default strength).
        chart: Computed birth chart.

    Returns:
        New list with updated strength fields where applicable.
    """
    result: list[YogaResult] = []
    for yoga in yogas:
        if not yoga.planets_involved:
            result.append(yoga)
            continue

        planet_objects = [chart.planets[p] for p in yoga.planets_involved if p in chart.planets]
        if not planet_objects:
            result.append(yoga)
            continue

        any_combust = any(p.is_combust for p in planet_objects)
        any_debilitated = any(p.dignity == "debilitated" for p in planet_objects)
        any_vargottama = any(is_vargottama(p) for p in planet_objects)
        any_retrograde = any(
            p.is_retrograde and p.name not in ("Rahu", "Ketu") for p in planet_objects
        )

        current = yoga.strength
        if any_combust and any_debilitated:
            new_strength = "cancelled"
        elif any_combust or (any_debilitated and yoga.effect == "benefic"):
            # Only downgrade; don't override an already-worse value
            new_strength = "cancelled" if current == "cancelled" else "partial"
        elif yoga.effect == "benefic" and (any_vargottama or any_retrograde):
            # Only upgrade if currently at full strength
            new_strength = "enhanced" if current == "full" else current
        else:
            new_strength = current

        if new_strength != current:
            result.append(yoga.model_copy(update={"strength": new_strength}))
        else:
            result.append(yoga)

    return result


# ── Parivartana classification helper ────────────────────────────────────────


def _classify_parivartana(house_a: int, house_b: int) -> tuple[str, str, str, str]:
    """Classify a Parivartana Yoga based on involved house types.

    Args:
        house_a: First house number (1-12).
        house_b: Second house number (1-12).

    Returns:
        Tuple of (name_en, name_hi, effect, classification_suffix).
    """
    either_dainya = house_a in _DAINYA_HOUSES or house_b in _DAINYA_HOUSES
    either_khala = house_a in _KHALA_HOUSES or house_b in _KHALA_HOUSES
    both_maha = house_a in _MAHA_HOUSES and house_b in _MAHA_HOUSES

    if either_dainya:
        return (
            "Dainya Parivartana Yoga",
            "दैन्य परिवर्तन योग",
            "malefic",
            "dusthana exchange — results mixed with hardship and obstacles",
        )
    if either_khala:
        return (
            "Khala Parivartana Yoga",
            "खल परिवर्तन योग",
            "mixed",
            "upachaya exchange — results come through sustained effort",
        )
    if both_maha:
        return (
            "Maha Parivartana Yoga",
            "महा परिवर्तन योग",
            "benefic",
            "kendra/trikona exchange — great power, prosperity, and status",
        )
    # Houses 2 and 11 alone (maraka / labha) fall under Khala by extension
    return (
        "Khala Parivartana Yoga",
        "खल परिवर्तन योग",
        "mixed",
        "exchange of house lords — results require effort",
    )


# ── Main detection ────────────────────────────────────────────────────────────


def detect_parivartana_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect all Parivartana (mutual sign exchange) Yogas in a chart.

    Parivartana occurs when the lord of house A is in house B AND the lord
    of house B is in house A (whole-sign system). All 66 house pairs are
    checked. Pairs where the same planet lords both houses are skipped (a
    planet cannot exchange with itself). Rahu/Ketu are not sign lords per
    BPHS and are excluded.

    Strength is set to "enhanced" when either exchanging planet is
    Vargottama; otherwise "full".

    Args:
        chart: Computed birth chart.

    Returns:
        List of detected Parivartana YogaResults (is_present=True).
    """
    yogas: list[YogaResult] = []

    for house_a, house_b in combinations(range(1, 13), 2):
        lord_a = get_house_lord(chart, house_a)
        lord_b = get_house_lord(chart, house_b)

        # Same lord rules both houses (e.g. Mercury → Gemini + Virgo) — skip
        if lord_a == lord_b:
            continue

        # Nodes are not sign lords in classical BPHS
        if lord_a in ("Rahu", "Ketu") or lord_b in ("Rahu", "Ketu"):
            continue

        planet_a = chart.planets.get(lord_a)
        planet_b = chart.planets.get(lord_b)

        if planet_a is None or planet_b is None:
            continue

        # Core condition: lord of A in B AND lord of B in A
        if planet_a.house != house_b or planet_b.house != house_a:
            continue

        name, name_hi, effect, suffix = _classify_parivartana(house_a, house_b)

        varg_lords = [
            lord for lord, p in ((lord_a, planet_a), (lord_b, planet_b)) if is_vargottama(p)
        ]
        varg_note = (
            f" {', '.join(varg_lords)} also Vargottama — extremely powerful." if varg_lords else ""
        )
        strength = "enhanced" if varg_lords else "full"

        yogas.append(
            YogaResult(
                name=name,
                name_hindi=name_hi,
                is_present=True,
                planets_involved=[lord_a, lord_b],
                houses_involved=[house_a, house_b],
                description=(
                    f"{lord_a} (H{house_a} lord) in H{house_b} ↔ "
                    f"{lord_b} (H{house_b} lord) in H{house_a} — {suffix}.{varg_note}"
                ),
                effect=effect,
                strength=strength,
            )
        )

    return yogas
