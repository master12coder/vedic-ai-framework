"""Family gemstone synergy — cross-chart gemstone analysis.

Computes per-member gemstone profiles (including Rahu/Ketu rashyadhipati
resolution and conjunction penalties) and detects cross-member synergy
patterns like karmic complementarity ("जो एक के लिए विष, दूसरे के लिए अमृत").

Source: Traditional Pandit Ji family consultation wisdom, systematised
for DaivAI Family Bond Kundali.
"""

from __future__ import annotations

from daivai_engine.compute.conjunction_penalty import compute_conjunction_penalty
from daivai_engine.compute.functional_nature import get_shadow_planet_nature
from daivai_engine.compute.gem_therapy_core import compute_gem_recommendation
from daivai_engine.models.chart import ChartData
from daivai_engine.models.family_bond import (
    ConjunctionPenalty,
    FamilyGemSynergyResult,
    FamilyMemberGemProfile,
    GemSynergyPair,
)
from daivai_engine.models.functional_nature import ShadowPlanetNature


def compute_family_gem_synergy(charts: list[ChartData]) -> FamilyGemSynergyResult:
    """Analyse gemstone recommendations across family members.

    For each member:
        1. Run standard gem_therapy recommendation (lordship-based).
        2. Resolve Rahu/Ketu via rashyadhipati (sign lord functional nature).
        3. Compute conjunction penalties for recommended planets.

    Cross-member:
        4. Detect karmic complementarity (A's prohibited = B's recommended).
        5. Find family-safe stones (recommended or safe for ALL members).

    Args:
        charts: List of computed birth charts for family members.

    Returns:
        FamilyGemSynergyResult with per-member profiles and synergy pairs.
    """
    members: list[FamilyMemberGemProfile] = []
    for chart in charts:
        profile = _build_member_profile(chart)
        members.append(profile)

    synergy_pairs = _find_synergy_pairs(members)
    family_safe = _find_family_safe_stones(members)

    summary = _build_summary(members, synergy_pairs, family_safe)

    return FamilyGemSynergyResult(
        members=members,
        synergy_pairs=synergy_pairs,
        family_safe_stones=family_safe,
        summary=summary,
    )


def _build_member_profile(chart: ChartData) -> FamilyMemberGemProfile:
    """Build complete gemstone profile for one family member."""
    recs = compute_gem_recommendation(chart)

    recommended: list[str] = []
    prohibited: list[str] = []
    test_with_caution: list[str] = []

    for rec in recs:
        if rec.status == "recommended":
            recommended.append(rec.stone_name)
        elif rec.status == "prohibited":
            prohibited.append(rec.stone_name)
        elif rec.status == "test_with_caution":
            test_with_caution.append(rec.stone_name)

    # Rashyadhipati for Rahu/Ketu
    rahu_gem: ShadowPlanetNature | None = None
    ketu_gem: ShadowPlanetNature | None = None
    if "Rahu" in chart.planets:
        rahu_gem = get_shadow_planet_nature("Rahu", chart)
    if "Ketu" in chart.planets:
        ketu_gem = get_shadow_planet_nature("Ketu", chart)

    # Conjunction penalties for recommended stones' planets
    penalties: list[ConjunctionPenalty] = []
    for rec in recs:
        if rec.status == "recommended":
            penalty = compute_conjunction_penalty(chart, rec.planet)
            if penalty.has_penalty:
                penalties.append(penalty)

    return FamilyMemberGemProfile(
        name=chart.name,
        lagna_sign=chart.lagna_sign,
        recommended=recommended,
        prohibited=prohibited,
        test_with_caution=test_with_caution,
        rahu_gem=rahu_gem,
        ketu_gem=ketu_gem,
        conjunction_penalties=penalties,
    )


def _find_synergy_pairs(members: list[FamilyMemberGemProfile]) -> list[GemSynergyPair]:
    """Detect cross-member gemstone relationships."""
    pairs: list[GemSynergyPair] = []
    for i, ma in enumerate(members):
        for mb in members[i + 1 :]:
            # Karmic complement: A's prohibited = B's recommended
            for stone in ma.prohibited:
                if stone in mb.recommended:
                    pairs.append(
                        GemSynergyPair(
                            person_a=ma.name,
                            person_b=mb.name,
                            stone=stone,
                            planet=_stone_to_planet(stone),
                            relationship="karmic_complement",
                            description=(
                                f"{stone} is prohibited for {ma.name} but recommended for "
                                f"{mb.name} — जो एक के लिए विष, दूसरे के लिए अमृत"
                            ),
                        )
                    )
            # Reverse direction
            for stone in mb.prohibited:
                if stone in ma.recommended:
                    pairs.append(
                        GemSynergyPair(
                            person_a=mb.name,
                            person_b=ma.name,
                            stone=stone,
                            planet=_stone_to_planet(stone),
                            relationship="karmic_complement",
                            description=(
                                f"{stone} is prohibited for {mb.name} but recommended for "
                                f"{ma.name} — जो एक के लिए विष, दूसरे के लिए अमृत"
                            ),
                        )
                    )
            # Shared recommendation
            shared = set(ma.recommended) & set(mb.recommended)
            for stone in shared:
                pairs.append(
                    GemSynergyPair(
                        person_a=ma.name,
                        person_b=mb.name,
                        stone=stone,
                        planet=_stone_to_planet(stone),
                        relationship="shared_recommend",
                        description=f"{stone} is recommended for both {ma.name} and {mb.name}.",
                    )
                )
    return pairs


_STONE_TO_PLANET = {
    "Ruby (Manikya)": "Sun",
    "Pearl (Moti)": "Moon",
    "Red Coral (Moonga)": "Mars",
    "Emerald (Panna)": "Mercury",
    "Yellow Sapphire (Pukhraj)": "Jupiter",
    "Diamond (Heera)": "Venus",
    "Blue Sapphire (Neelam)": "Saturn",
    "Hessonite (Gomed)": "Rahu",
    "Cat's Eye (Lehsunia)": "Ketu",
}


def _stone_to_planet(stone: str) -> str:
    """Map stone name to planet name."""
    return _STONE_TO_PLANET.get(stone, "Unknown")


def _find_family_safe_stones(members: list[FamilyMemberGemProfile]) -> list[str]:
    """Find stones that are recommended or safe for ALL family members."""
    if not members:
        return []
    safe_sets = []
    for m in members:
        safe = set(m.recommended) | set(m.test_with_caution)
        safe_sets.append(safe)
    return (
        sorted(safe_sets[0].intersection(*safe_sets[1:]))
        if len(safe_sets) > 1
        else sorted(safe_sets[0])
    )


def _build_summary(
    members: list[FamilyMemberGemProfile],
    synergy_pairs: list[GemSynergyPair],
    family_safe: list[str],
) -> str:
    """Build a one-paragraph summary."""
    complements = [p for p in synergy_pairs if p.relationship == "karmic_complement"]
    parts = [f"Family of {len(members)} members analysed."]
    if complements:
        parts.append(f"{len(complements)} karmic complement(s) found.")
    if family_safe:
        parts.append(f"Family-safe stones: {', '.join(family_safe)}.")
    return " ".join(parts)
