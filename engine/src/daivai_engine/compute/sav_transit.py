"""Sarvashtakavarga (SAV) Pinda-based transit analysis.

Uses the aggregate SAV bindu count per sign to weight transit predictions.
This is layered on top of the per-planet BAV scoring in transit_scoring.py.

SAV Pinda measures the overall "receptivity" of a sign — signs with high
SAV totals are more supportive for any transit passing through them,
regardless of which planet it is.

Thresholds from classical texts (BPHS Ch.72, Mantreswara):
  SAV >= 30 in a sign -> excellent results for transits
  SAV 25-29           -> good results
  SAV 20-24           -> average / mixed
  SAV 15-19           -> difficult
  SAV < 15            -> very adverse

Source: BPHS Chapter 72 (Trikona Shodhana, Ekadhipatya Shodhana excluded —
this is the raw Sarvashtakavarga before reductions).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from daivai_engine.compute.ashtakavarga import compute_ashtakavarga
from daivai_engine.constants import SIGNS, SIGNS_EN
from daivai_engine.models.chart import ChartData


# SAV pinda score → label (total across 7 planets per sign, max 56)
_SAV_THRESHOLDS: list[tuple[int, str, str]] = [
    (30, "Excellent", "excellent"),
    (25, "Good", "good"),
    (20, "Average", "average"),
    (15, "Difficult", "difficult"),
    (0, "Very adverse", "very_adverse"),
]

# SAV modifier for transit scoring (additive to combined score)
_SAV_MODIFIERS: list[tuple[int, int]] = [
    (30, +1),  # ≥30: boost any transit
    (20, 0),  # 20-29: neutral
    (0, -1),  # <20: reduce any transit
]

# Per-planet BAV threshold for individual transit quality
# Source: Mantreswara Phaladeepika — ≥4 bindus favorable, ≤2 difficult
BAV_GOOD_THRESHOLD = 4  # ≥4 bindus → planet transits well through this sign
BAV_BAD_THRESHOLD = 2  # ≤2 bindus → difficult transit for this planet


class SavSignProfile(BaseModel):
    """SAV profile for a single sign — bindu count and quality classification."""

    sign_index: int = Field(ge=0, le=11)
    sign: str
    sign_en: str
    sav_total: int = Field(ge=0, le=56)  # Max 56 (7 planets x 8 sources)
    label: str
    label_key: str  # excellent/good/average/difficult/very_adverse
    sav_modifier: int  # -1, 0, +1 — additive modifier for any transit


class SavPindaResult(BaseModel):
    """SAV Pinda analysis — receptivity of all 12 signs for transits."""

    sign_profiles: list[SavSignProfile]
    strongest_sign_index: int
    weakest_sign_index: int
    total_bindus: int  # Always 337


class SavTransitScore(BaseModel):
    """Combined transit score using both BAV (planet-specific) and SAV (aggregate)."""

    planet: str
    transit_sign_index: int
    sign: str
    sign_en: str
    bav_bindus: int  # Planet's own BAV count in this sign
    bav_quality: str  # good / average / difficult
    sav_total: int  # Aggregate SAV for this sign
    sav_modifier: int  # SAV contribution to score
    combined_score: int  # bav_modifier + sav_modifier (clamped -3..+3)
    label: str


def compute_sav_pinda(chart: ChartData) -> SavPindaResult:
    """Compute SAV Pinda — aggregate sign receptivity from Sarvashtakavarga.

    Returns the SAV total for each of the 12 signs and their quality
    classification. Use this to determine which signs are generally
    auspicious for any planet to transit.

    Args:
        chart: Natal birth chart.

    Returns:
        SavPindaResult with profile for each sign.
    """
    ak = compute_ashtakavarga(chart)
    sarva = ak.sarva  # List of 12 SAV totals per sign

    profiles: list[SavSignProfile] = []
    for i, total in enumerate(sarva):
        label, label_key = _classify_sav(total)
        modifier = _sav_modifier(total)
        profiles.append(
            SavSignProfile(
                sign_index=i,
                sign=SIGNS[i],
                sign_en=SIGNS_EN[i],
                sav_total=total,
                label=label,
                label_key=label_key,
                sav_modifier=modifier,
            )
        )

    strongest = max(range(12), key=lambda i: sarva[i])
    weakest = min(range(12), key=lambda i: sarva[i])

    return SavPindaResult(
        sign_profiles=profiles,
        strongest_sign_index=strongest,
        weakest_sign_index=weakest,
        total_bindus=sum(sarva),
    )


def compute_sav_transit_scores(
    chart: ChartData,
    transit_sign_map: dict[str, int],
) -> list[SavTransitScore]:
    """Compute SAV-enhanced transit scores for all given planets.

    Combines per-planet BAV bindu quality with SAV aggregate sign strength
    for a refined transit prediction. This is complementary to the Gochara
    + Vedha scoring in transit_scoring.py.

    Args:
        chart: Natal birth chart.
        transit_sign_map: Dict mapping planet name to current transit
            sign index (0-11). E.g. {"Saturn": 3, "Jupiter": 7, ...}

    Returns:
        List of SavTransitScore sorted by combined_score descending.
    """
    ak = compute_ashtakavarga(chart)
    bav_by_planet = ak.bhinna  # per-planet BAV tables
    sarva = ak.sarva  # SAV totals per sign

    scores: list[SavTransitScore] = []
    for planet, sign_idx in transit_sign_map.items():
        # Per-planet BAV count in this sign
        if planet in bav_by_planet:
            bav_bindus = bav_by_planet[planet][sign_idx]
        else:
            bav_bindus = 4  # Rahu/Ketu not in BAV — use neutral

        bav_quality = _bav_quality(bav_bindus)
        bav_mod = _bav_modifier_from_bindus(bav_bindus)

        # SAV aggregate for the transiting sign
        sav_total = sarva[sign_idx]
        sav_mod = _sav_modifier(sav_total)

        combined = max(-3, min(3, bav_mod + sav_mod))
        label = _score_label(combined)

        scores.append(
            SavTransitScore(
                planet=planet,
                transit_sign_index=sign_idx,
                sign=SIGNS[sign_idx],
                sign_en=SIGNS_EN[sign_idx],
                bav_bindus=bav_bindus,
                bav_quality=bav_quality,
                sav_total=sav_total,
                sav_modifier=sav_mod,
                combined_score=combined,
                label=label,
            )
        )

    scores.sort(key=lambda x: x.combined_score, reverse=True)
    return scores


def get_best_transit_signs(
    chart: ChartData,
    planet: str,
    top_n: int = 3,
) -> list[SavSignProfile]:
    """Return the top N signs for a planet to transit through.

    A sign is good for transit when BOTH:
    - Planet's BAV count ≥ BAV_GOOD_THRESHOLD (≥4)
    - SAV total is reasonably high (≥20)

    Args:
        chart: Natal birth chart.
        planet: Planet name (e.g. "Saturn", "Jupiter").
        top_n: Number of signs to return.

    Returns:
        List of SavSignProfile for the best transit signs, sorted by
        combined quality (BAV x SAV) descending.
    """
    ak = compute_ashtakavarga(chart)
    bav = ak.bhinna.get(planet, [4] * 12)
    sarva = ak.sarva

    # Score each sign: bav_bindus x sav_weight
    def _combined(i: int) -> float:
        return bav[i] * (sarva[i] / 28.0)  # normalize SAV by average

    ranked = sorted(range(12), key=_combined, reverse=True)[:top_n]

    profiles: list[SavSignProfile] = []
    for i in ranked:
        label, label_key = _classify_sav(sarva[i])
        profiles.append(
            SavSignProfile(
                sign_index=i,
                sign=SIGNS[i],
                sign_en=SIGNS_EN[i],
                sav_total=sarva[i],
                label=label,
                label_key=label_key,
                sav_modifier=_sav_modifier(sarva[i]),
            )
        )
    return profiles


# ── Private helpers ────────────────────────────────────────────────────────


def _classify_sav(total: int) -> tuple[str, str]:
    """Return (label, label_key) for a given SAV total."""
    for threshold, label, key in _SAV_THRESHOLDS:
        if total >= threshold:
            return label, key
    return "Very adverse", "very_adverse"


def _sav_modifier(total: int) -> int:
    """Map SAV total to additive score modifier."""
    for threshold, mod in _SAV_MODIFIERS:
        if total >= threshold:
            return mod
    return -1


def _bav_modifier_from_bindus(bindus: int) -> int:
    """Map per-planet BAV bindu count to score modifier.

    ≥4 bindus → good transit for this planet in this sign.
    ≤2 bindus → difficult transit.
    """
    if bindus >= BAV_GOOD_THRESHOLD:
        return +1
    if bindus <= BAV_BAD_THRESHOLD:
        return -1
    return 0  # 3 bindus = neutral/borderline


def _bav_quality(bindus: int) -> str:
    """Human-readable quality label for BAV bindu count."""
    if bindus >= BAV_GOOD_THRESHOLD:
        return "good"
    if bindus <= BAV_BAD_THRESHOLD:
        return "difficult"
    return "average"


def _score_label(score: int) -> str:
    """Human-readable label for combined score."""
    labels = {
        3: "Very favorable",
        2: "Favorable",
        1: "Slightly favorable",
        0: "Neutral",
        -1: "Slightly difficult",
        -2: "Difficult",
        -3: "Very difficult",
    }
    return labels.get(score, "Neutral")
