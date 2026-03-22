"""Medical Astrology — Kala Purusha body part vulnerability analysis.

Helper utilities and body part vulnerability computation from birth chart.

Sources: BPHS Ch.7 (Kala Purusha), Ch.68 (Arishta Adhyaya);
         Saravali Ch.6; Phaladeepika Ch.6.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from daivai_engine.compute.chart import has_aspect
from daivai_engine.constants import NAKSHATRA_SPAN_DEG, NAKSHATRAS, SIGN_LORDS, SIGNS, SIGNS_HI
from daivai_engine.models.chart import ChartData
from daivai_engine.models.medical import BodyPartVulnerability


_RULES_FILE = Path(__file__).parent.parent / "knowledge" / "medical_rules.yaml"

_DUSTHANAS = {6, 8, 12}
_TRIKONAS = {1, 5, 9}


@lru_cache(maxsize=1)
def _load_rules() -> dict:
    """Load medical rules YAML (cached after first call)."""
    with _RULES_FILE.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)  # type: ignore[no-any-return]


def _natural_malefics() -> set[str]:
    """Return the set of natural malefic planets from YAML."""
    return set(_load_rules().get("natural_malefics", ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]))


def _is_afflicted_by_malefic(chart: ChartData, planet_name: str) -> bool:
    """Return True if the given planet is conjunct (same sign) with any natural malefic.

    "Affliction" in whole-sign Jyotish means a malefic shares the same sign
    as the planet being assessed.

    Source: BPHS Ch.68 v.1-3 — general principle of graha pida (planetary affliction).
    """
    malefics = _natural_malefics()
    p = chart.planets[planet_name]
    for mal in malefics:
        if mal == planet_name:
            continue
        mal_data = chart.planets.get(mal)
        if mal_data and mal_data.sign_index == p.sign_index:
            return True
    return False


def _is_aspected_by_malefic(chart: ChartData, house: int) -> bool:
    """Return True if any natural malefic aspects the given house number."""
    malefics = _natural_malefics()
    return any(has_aspect(chart, mal, house) for mal in malefics)


def _afflicting_malefics_in_sign(chart: ChartData, sign_index: int) -> list[str]:
    """Return malefics placed in the given sign index."""
    malefics = _natural_malefics()
    result: list[str] = []
    for planet_name in malefics:
        p = chart.planets.get(planet_name)
        if p and p.sign_index == sign_index:
            result.append(planet_name)
    return result


def _afflicting_malefics_aspecting_sign(chart: ChartData, sign_index: int) -> list[str]:
    """Return malefics that aspect the house corresponding to sign_index from lagna.

    The house number for a sign is: ((sign_index - lagna_sign_index) % 12) + 1
    """
    malefics = _natural_malefics()
    house = ((sign_index - chart.lagna_sign_index) % 12) + 1
    result: list[str] = []
    for planet_name in malefics:
        if has_aspect(chart, planet_name, house):
            result.append(planet_name)
    return result


def _sphuta_nakshatra(longitude: float) -> str:
    """Return nakshatra name for a given sidereal longitude."""
    idx = int(longitude / NAKSHATRA_SPAN_DEG) % 27
    return NAKSHATRAS[idx]


def _lagnesh(chart: ChartData) -> str:
    """Return the name of the lagna lord (lord of ascendant sign)."""
    return SIGN_LORDS[chart.lagna_sign_index]


def _sixth_lord(chart: ChartData) -> str:
    """Return the lord of the 6th house (sign that is 6th from lagna)."""
    sixth_sign_index = (chart.lagna_sign_index + 5) % 12
    return SIGN_LORDS[sixth_sign_index]


# ── Body Part Vulnerability ───────────────────────────────────


def analyze_body_part_vulnerabilities(chart: ChartData) -> list[BodyPartVulnerability]:
    """Compute body part vulnerability for all 12 Kala Purusha zones.

    For each sign (body zone), assess affliction by:
      - Natural malefics placed in that sign (strongest affliction).
      - Natural malefics aspecting the corresponding house from lagna.

    Vulnerability levels:
      "high"     — 2+ malefics in sign, OR 1 malefic in sign + 1 aspecting
      "moderate" — 1 malefic in sign, OR 2+ malefics aspecting
      "low"      — 1 malefic aspecting only
      "none"     — no malefic influence

    Source: BPHS Ch.7 Kala Purusha Adhyaya; Saravali Ch.6 v.1-5.

    Args:
        chart: Fully computed birth chart.

    Returns:
        List of 12 BodyPartVulnerability records (one per sign).
    """
    rules = _load_rules()
    body_map: dict = rules["kala_purusha_body_mapping"]
    result: list[BodyPartVulnerability] = []

    for idx in range(12):
        zone = body_map[idx]
        in_sign = _afflicting_malefics_in_sign(chart, idx)
        aspecting = [p for p in _afflicting_malefics_aspecting_sign(chart, idx) if p not in in_sign]
        all_afflictors = in_sign + aspecting

        if len(in_sign) >= 2 or (len(in_sign) >= 1 and len(aspecting) >= 1):
            level = "high"
            reason = f"Malefics in sign: {', '.join(in_sign)}"
            if aspecting:
                reason += f"; aspecting: {', '.join(aspecting)}"
        elif len(in_sign) == 1:
            level = "moderate"
            reason = f"{in_sign[0]} placed in {zone['sign_en']} sign"
        elif len(aspecting) >= 2:
            level = "moderate"
            reason = f"Multiple malefics aspecting: {', '.join(aspecting)}"
        elif len(aspecting) == 1:
            level = "low"
            reason = f"{aspecting[0]} aspects this zone"
        else:
            level = "none"
            reason = "No malefic influence on this body zone"

        result.append(
            BodyPartVulnerability(
                sign_index=idx,
                sign=SIGNS[idx],
                sign_hi=SIGNS_HI[idx],
                body_parts=zone["body_parts"],
                body_parts_hi=zone["body_parts_hi"],
                afflicting_planets=all_afflictors,
                vulnerability_level=level,
                reason=reason,
            )
        )

    return result
