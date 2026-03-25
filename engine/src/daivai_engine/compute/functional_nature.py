"""Functional nature classification of planets per lagna.

Resolves the functional benefic/malefic/yogakaraka/maraka status of any planet
for a given lagna, and extends this to shadow planets (Rahu/Ketu) via their
sign lord (rashyadhipati principle).

Source: BPHS lordship principles — Kendra/Trikona lords gain beneficence,
Dusthana lords are malefic, Yogakaraka owns both kendra and trikona.
"""

from __future__ import annotations

from typing import Any

from daivai_engine.constants.houses import DUSTHANAS
from daivai_engine.constants.signs import SIGN_LORDS, SIGNS, SIGNS_EN
from daivai_engine.knowledge.loader import load_lordship_rules
from daivai_engine.models.chart import ChartData
from daivai_engine.models.functional_nature import FunctionalNature, ShadowPlanetNature


_SHADOW_STONE = {
    "Rahu": "Hessonite (Gomed)",
    "Ketu": "Cat's Eye (Lehsunia)",
}

# Lordship YAML keys are lowercase Sanskrit: mesha, vrishabha, mithuna, ...
# Accept both English ("Gemini") and Vedic ("Mithuna") sign names.
_SIGN_TO_YAML_KEY: dict[str, str] = {}
for _i, (_vedic, _en) in enumerate(zip(SIGNS, SIGNS_EN, strict=True)):
    _key = _vedic.lower()
    _SIGN_TO_YAML_KEY[_vedic] = _key  # "Mithuna" → "mithuna"
    _SIGN_TO_YAML_KEY[_en] = _key  # "Gemini" → "mithuna"
    _SIGN_TO_YAML_KEY[_key] = _key  # "mithuna" → "mithuna"
    _SIGN_TO_YAML_KEY[_en.lower()] = _key  # "gemini" → "mithuna"


def get_functional_nature(planet: str, lagna_sign: str) -> FunctionalNature:
    """Look up functional classification of a planet for the given lagna.

    Searches yogakaraka, functional_benefics, functional_malefics, and maraka
    lists in lordship_rules.yaml.  Returns a structured classification.

    Args:
        planet: Classical planet name (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn).
        lagna_sign: Lagna sign in English (e.g., "Gemini", "Scorpio").

    Returns:
        FunctionalNature with classification, houses_owned, and reasoning.
    """
    lordship = load_lordship_rules()
    lagna_key = _SIGN_TO_YAML_KEY.get(lagna_sign, lagna_sign.lower())
    lagna_data: dict[str, Any] = lordship.get("lagnas", {}).get(lagna_key, {})

    # Check yogakaraka
    yogakaraka = lagna_data.get("yogakaraka", {})
    if yogakaraka.get("planet") == planet:
        houses = _find_houses(planet, lagna_data)
        return FunctionalNature(
            planet=planet,
            lagna_sign=lagna_sign,
            classification="yogakaraka",
            houses_owned=houses,
            reasoning=yogakaraka.get("reasoning", "").strip(),
            is_yogakaraka=True,
            is_maraka=_is_maraka(planet, lagna_data),
        )

    # Check functional benefics
    for entry in lagna_data.get("functional_benefics", []):
        if entry.get("planet") == planet:
            return FunctionalNature(
                planet=planet,
                lagna_sign=lagna_sign,
                classification="benefic",
                houses_owned=entry.get("houses_owned", []),
                reasoning=entry.get("reasoning", "").strip(),
                is_maraka=_is_maraka(planet, lagna_data),
            )

    # Check functional malefics
    for entry in lagna_data.get("functional_malefics", []):
        if entry.get("planet") == planet:
            return FunctionalNature(
                planet=planet,
                lagna_sign=lagna_sign,
                classification="malefic",
                houses_owned=entry.get("houses_owned", []),
                reasoning=entry.get("reasoning", "").strip(),
                is_maraka=_is_maraka(planet, lagna_data),
            )

    # Not found — neutral
    houses = _find_houses(planet, lagna_data)
    return FunctionalNature(
        planet=planet,
        lagna_sign=lagna_sign,
        classification="neutral",
        houses_owned=houses,
        reasoning=f"{planet} is not classified as benefic or malefic for {lagna_sign} lagna.",
        is_maraka=_is_maraka(planet, lagna_data),
    )


def get_shadow_planet_nature(shadow_planet: str, chart: ChartData) -> ShadowPlanetNature:
    """Resolve Rahu/Ketu functional nature via sign lord (rashyadhipati).

    BPHS: "छाया ग्रह जिस राशि में हो, उस राशि के स्वामी का फल देता है"
    — Shadow planets give results of the lord of the sign they occupy.

    Algorithm:
        1. Get shadow planet's sign_index from chart.
        2. Look up classical sign lord via SIGN_LORDS.
        3. Get that lord's functional nature for this lagna.
        4. Classify gemstone safety based on nature + dusthana involvement.

    Args:
        shadow_planet: "Rahu" or "Ketu".
        chart: Computed birth chart.

    Returns:
        ShadowPlanetNature with sign lord, functional nature, and gemstone safety.
    """
    planet_data = chart.planets[shadow_planet]
    sign_idx = planet_data.sign_index
    sign_lord = SIGN_LORDS[sign_idx]
    sign_name = SIGNS[sign_idx]

    nature = get_functional_nature(sign_lord, chart.lagna_sign)
    safety = _classify_gemstone_safety(nature)
    stone = _SHADOW_STONE.get(shadow_planet, "")

    reasoning = (
        f"{shadow_planet} in {sign_name} → sign lord = {sign_lord} "
        f"→ {sign_lord} is {nature.classification} ({nature.houses_owned}) "
        f"for {chart.lagna_sign} lagna → {stone} is {safety}."
    )

    return ShadowPlanetNature(
        shadow_planet=shadow_planet,
        sign_index=sign_idx,
        sign_name=sign_name,
        sign_lord=sign_lord,
        sign_lord_nature=nature,
        gemstone_safety=safety,
        gemstone_name=stone,
        reasoning=reasoning,
    )


def _classify_gemstone_safety(nature: FunctionalNature) -> str:
    """Map functional nature to gemstone safety level.

    Conservative approach for stones — even benefic planets with dusthana
    involvement get 'test_with_caution' because the stone amplifies all
    house significations, including the dusthana.
    """
    if nature.classification == "yogakaraka":
        return "safe"
    if nature.classification == "benefic":
        has_dusthana = any(h in DUSTHANAS for h in nature.houses_owned)
        return "test_with_caution" if has_dusthana else "safe"
    if nature.classification in ("malefic", "maraka"):
        return "unsafe"
    # neutral
    return "test_with_caution"


def _is_maraka(planet: str, lagna_data: dict[str, Any]) -> bool:
    """Check if planet appears in the maraka list for this lagna."""
    return any(m.get("planet") == planet for m in lagna_data.get("maraka", []))


def _find_houses(planet: str, lagna_data: dict[str, Any]) -> list[int]:
    """Find all houses owned by a planet from the house_lords mapping."""
    house_lords: dict[str, str] = lagna_data.get("house_lords", {})
    return [int(h) for h, lord in house_lords.items() if lord == planet]
