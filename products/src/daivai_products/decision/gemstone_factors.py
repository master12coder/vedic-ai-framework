"""Individual factor computations for the 10-Factor Gemstone Weight Engine.

Each factor returns (multiplier, reasoning_string). Constants for seed mantras,
colors, daan, stone density, and avastha/dignity mappings live here.
Source: BPHS Ch.87 (ratna-adhyaya) + remedy_rules.yaml.
"""

from __future__ import annotations

import math
from typing import Any

from daivai_engine.models.analysis import FullChartAnalysis


# ── Stone energy density (relative scale, Diamond highest) ─────────────────
STONE_DENSITY: dict[str, float] = {
    "Panna": 1.0,
    "Pukhraj": 1.1,
    "Neelam": 1.2,
    "Manikya": 1.0,
    "Moti": 0.8,
    "Moonga": 0.9,
    "Heera": 1.3,
    "Gomed": 0.9,
    "Lehsunia": 0.9,
}

# ── Avastha (planetary age) multipliers — BPHS Ch.45 ──────────────────────
AVASTHA_MULTIPLIER: dict[str, float] = {
    "Bala": 0.7,
    "Kumara": 0.9,
    "Yuva": 1.0,
    "Vriddha": 0.8,
    "Mruta": 0.5,
}

# ── Dignity multipliers — BPHS Ch.3 ───────────────────────────────────────
DIGNITY_MULTIPLIER: dict[str, float] = {
    "exalted": 1.3,
    "mooltrikona": 1.2,
    "own": 1.1,
    "friendly": 1.0,
    "neutral": 0.9,
    "enemy": 0.7,
    "debilitated": 0.5,
}

# ── Purpose multipliers ───────────────────────────────────────────────────
PURPOSE_MULTIPLIER: dict[str, float] = {
    "protection": 0.8,
    "growth": 1.0,
    "maximum": 1.2,
}

# ── Free alternatives: seed mantras, colors, daan per planet ──────────────
SEED_MANTRAS: dict[str, str] = {
    "Sun": "Om Hraam Hreem Hraum Sah Suryaya Namaha",
    "Moon": "Om Shraam Shreem Shraum Sah Chandraya Namaha",
    "Mars": "Om Kraam Kreem Kraum Sah Bhaumaya Namaha",
    "Mercury": "Om Braam Breem Braum Sah Budhaya Namaha",
    "Jupiter": "Om Graam Greem Graum Sah Gurave Namaha",
    "Venus": "Om Draam Dreem Draum Sah Shukraya Namaha",
    "Saturn": "Om Praam Preem Praum Sah Shanaischaraya Namaha",
    "Rahu": "Om Bhraam Bhreem Bhraum Sah Rahave Namaha",
    "Ketu": "Om Sraam Sreem Sraum Sah Ketave Namaha",
}

PLANET_COLORS: dict[str, str] = {
    "Sun": "Red / Copper",
    "Moon": "White / Silver",
    "Mars": "Red / Coral",
    "Mercury": "Green",
    "Jupiter": "Yellow / Gold",
    "Venus": "White / Cream",
    "Saturn": "Black / Dark Blue",
    "Rahu": "Smoky Blue / Ultraviolet",
    "Ketu": "Gray / Brown",
}

PLANET_DAAN: dict[str, str] = {
    "Sun": "Wheat, jaggery, copper on Sunday",
    "Moon": "Rice, milk, white cloth, silver on Monday",
    "Mars": "Red lentils, red cloth, copper on Tuesday",
    "Mercury": "Green moong, green cloth, vegetables on Wednesday",
    "Jupiter": "Chana dal, turmeric, yellow cloth, books on Thursday",
    "Venus": "White rice, sweets, white cloth, perfume on Friday",
    "Saturn": "Black sesame, mustard oil, iron, dark cloth on Saturday",
    "Rahu": "Black sesame, coconut, blue cloth on Saturday",
    "Ketu": "Seven grains mix, gray cloth on Tuesday",
}


# ── Utility helpers ────────────────────────────────────────────────────────


def round_quarter(value: float) -> float:
    """Round to the nearest 0.25 ratti."""
    return round(value * 4) / 4


def extract_hindi_name(gemstone_str: str) -> str:
    """Extract Hindi stone name from 'English (Hindi)' format."""
    if "(" in gemstone_str and ")" in gemstone_str:
        return gemstone_str.split("(")[1].rstrip(")")
    return gemstone_str.split()[0]


def build_free_alternatives(planet_name: str) -> list[str]:
    """Build free alternative remedies (mantra, color therapy, daan)."""
    alternatives: list[str] = []
    mantra = SEED_MANTRAS.get(planet_name)
    if mantra:
        alternatives.append(f"Mantra: {mantra}")
    color = PLANET_COLORS.get(planet_name)
    if color:
        alternatives.append(f"Color therapy: wear {color} on planet's day")
    daan = PLANET_DAAN.get(planet_name)
    if daan:
        alternatives.append(f"Daan: {daan}")
    return alternatives


# ── Factor computation functions (each returns multiplier + reasoning) ─────


def compute_body_weight_base(body_weight_kg: float) -> float:
    """Factor 1: body_weight / 10, rounded to 0.25, clamped [3.0, 12.0]."""
    raw = body_weight_kg / 10.0
    rounded = round_quarter(raw)
    return max(3.0, min(12.0, rounded))


def factor_avastha(planet_name: str, analysis: FullChartAnalysis) -> tuple[float, str]:
    """Factor 2: planetary age avastha (Bala/Kumara/Yuva/Vriddha/Mruta)."""
    planet_data = analysis.chart.planets.get(planet_name)
    if planet_data is None:
        return 1.0, "planet not in chart"
    avastha = planet_data.avastha
    multiplier = AVASTHA_MULTIPLIER.get(avastha, 1.0)
    return multiplier, avastha


def factor_bav(planet_name: str, analysis: FullChartAnalysis) -> tuple[float, str]:
    """Factor 3: BAV bindus in occupied sign (>=5->1.2, 4->1.0, 3->0.8, <=2->0.6)."""
    planet_data = analysis.chart.planets.get(planet_name)
    if planet_data is None:
        return 1.0, "planet not in chart"

    bhinna = analysis.ashtakavarga.bhinna.get(planet_name)
    if not bhinna or len(bhinna) < 12:
        return 1.0, "BAV data unavailable"

    bindus = bhinna[planet_data.sign_index]
    if bindus >= 5:
        return 1.2, f"{bindus} bindus (strong)"
    if bindus == 4:
        return 1.0, f"{bindus} bindus (average)"
    if bindus == 3:
        return 0.8, f"{bindus} bindus (below average)"
    return 0.6, f"{bindus} bindus (weak)"


def factor_dignity(planet_name: str, analysis: FullChartAnalysis) -> tuple[float, str]:
    """Factor 4: dignity multiplier — exalted to debilitated."""
    planet_data = analysis.chart.planets.get(planet_name)
    if planet_data is None:
        return 1.0, "planet not in chart"
    dignity = planet_data.dignity
    return DIGNITY_MULTIPLIER.get(dignity, 1.0), dignity


def factor_combustion(planet_name: str, analysis: FullChartAnalysis) -> tuple[float, str]:
    """Factor 5: combustion severely weakens gem potency."""
    planet_data = analysis.chart.planets.get(planet_name)
    if planet_data is None:
        return 1.0, "planet not in chart"
    if planet_data.is_combust:
        return 0.6, "combust — gem potency reduced"
    return 1.0, "not combust"


def factor_retrograde(planet_name: str, analysis: FullChartAnalysis) -> tuple[float, str]:
    """Factor 6: retrograde planet — cautious 0.85 multiplier."""
    planet_data = analysis.chart.planets.get(planet_name)
    if planet_data is None:
        return 1.0, "planet not in chart"
    if planet_data.is_retrograde:
        return 0.85, "retrograde — cautious reduction"
    return 1.0, "direct motion"


def factor_dasha(planet_name: str, analysis: FullChartAnalysis) -> tuple[float, str]:
    """Factor 7: wearing during own dasha is most effective."""
    if planet_name == analysis.current_md.lord:
        return 1.3, f"MD lord ({analysis.current_md.lord}) — peak effectiveness"
    if planet_name == analysis.current_ad.lord:
        return 1.15, f"AD lord ({analysis.current_ad.lord}) — enhanced effectiveness"
    return 1.0, "not current dasha lord"


def factor_lordship(planet_name: str, lordship_ctx: dict[str, Any]) -> tuple[float, str]:
    """Factor 8: lordship quality (yogakaraka 1.4, benefic 1.2, malefic 0.6, maraka 0.3)."""
    yogakaraka = lordship_ctx.get("yogakaraka", {})
    if yogakaraka.get("planet") == planet_name:
        return 1.4, "yogakaraka"

    for m in lordship_ctx.get("maraka", []):
        if m.get("planet") == planet_name:
            houses = m.get("houses", [])
            return 0.3, f"maraka ({', '.join(str(h) for h in houses)})"

    for b in lordship_ctx.get("functional_benefics", []):
        if b.get("planet") == planet_name:
            return 1.2, "functional benefic"

    for m in lordship_ctx.get("functional_malefics", []):
        if m.get("planet") == planet_name:
            return 0.6, "functional malefic"

    return 1.0, "neutral"


def factor_stone_density(stone_hindi: str) -> tuple[float, str]:
    """Factor 9: stone energy density (fixed per stone type)."""
    density = STONE_DENSITY.get(stone_hindi, 1.0)
    return density, f"{stone_hindi} density={density}"


def factor_purpose(purpose: str) -> tuple[float, str]:
    """Factor 10: purpose multiplier — protection/growth/maximum."""
    multiplier = PURPOSE_MULTIPLIER.get(purpose, 1.0)
    return multiplier, f"{purpose} mode"


def compute_all_factors(
    planet_name: str,
    analysis: FullChartAnalysis,
    lordship_ctx: dict[str, Any],
    stone_hindi: str,
    purpose: str,
) -> tuple[dict[str, float], list[str]]:
    """Compute factors 2-10 for one planet. Returns (name->multiplier, reasoning)."""
    factors: dict[str, float] = {}
    reasoning: list[str] = []

    f2, r2 = factor_avastha(planet_name, analysis)
    factors["avastha"] = f2
    reasoning.append(f"Avastha: {r2} (x{f2})")

    f3, r3 = factor_bav(planet_name, analysis)
    factors["bav_bindus"] = f3
    reasoning.append(f"BAV: {r3} (x{f3})")

    f4, r4 = factor_dignity(planet_name, analysis)
    factors["dignity"] = f4
    reasoning.append(f"Dignity: {r4} (x{f4})")

    f5, r5 = factor_combustion(planet_name, analysis)
    factors["combustion"] = f5
    reasoning.append(f"Combustion: {r5} (x{f5})")

    f6, r6 = factor_retrograde(planet_name, analysis)
    factors["retrograde"] = f6
    reasoning.append(f"Retrograde: {r6} (x{f6})")

    f7, r7 = factor_dasha(planet_name, analysis)
    factors["dasha"] = f7
    reasoning.append(f"Dasha: {r7} (x{f7})")

    f8, r8 = factor_lordship(planet_name, lordship_ctx)
    factors["lordship"] = f8
    reasoning.append(f"Lordship: {r8} (x{f8})")

    f9, r9 = factor_stone_density(stone_hindi)
    factors["stone_density"] = f9
    reasoning.append(f"Density: {r9} (x{f9})")

    f10, r10 = factor_purpose(purpose)
    factors["purpose"] = f10
    reasoning.append(f"Purpose: {r10} (x{f10})")

    return factors, reasoning


def compute_weighted_ratti(base_ratti: float, factors: dict[str, float]) -> float:
    """Multiply base ratti by all factor multipliers, round, and clamp.

    Returns recommended ratti in [2.0, 15.0], rounded to nearest 0.25.
    """
    product = math.prod(factors.values())
    raw = base_ratti * product
    clamped = max(2.0, min(15.0, round_quarter(raw)))
    return clamped
