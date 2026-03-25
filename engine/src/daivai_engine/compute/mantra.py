"""Mantra computation - planetary beej mantras and nakshatra deity mantras.

Derives personalized mantra recommendations from a ChartData by:
  1. Always recommending the lagna lord's mantra (strengthens the native).
  2. Recommending the current dasha lord's mantra when chart has dasha info.
  3. Adding mantras for debilitated or combust planets (need strength).
  4. Providing the natal Moon nakshatra deity mantra.

Source: BPHS, Muhurta Chintamani, traditional graha shanti vidhi.
"""

from __future__ import annotations

from typing import cast

from daivai_engine.constants import PLANETS_HI, SIGN_LORDS
from daivai_engine.knowledge.loader import load_mantra_rules
from daivai_engine.models.chart import ChartData
from daivai_engine.models.remedies import MantraRecommendation, NakshatraMantra


# ── Planet Hindi names lookup ─────────────────────────────────────────────────

_PLANET_NAMES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
_PLANET_HI: dict[str, str] = dict(zip(_PLANET_NAMES, PLANETS_HI, strict=True))


def get_mantra_for_planet(planet: str) -> MantraRecommendation | None:
    """Return the mantra recommendation data for a single planet.

    Loads from mantra_rules.yaml. Returns None if planet not found.

    Args:
        planet: Planet name — one of the 9 Vedic grahas.

    Returns:
        MantraRecommendation or None.
    """
    rules = load_mantra_rules()
    planet_rules = rules.get("planets", {})
    data = planet_rules.get(planet)
    if not data:
        return None

    timing = data.get("timing", {})
    return MantraRecommendation(
        planet=planet,
        planet_hi=data.get("name_hi", _PLANET_HI.get(planet, planet)),
        beej=data["beej"],
        beej_mantra=data["beej_mantra"],
        beej_mantra_en=data["beej_mantra_en"],
        moola_mantra=data["moola_mantra"],
        gayatri=data["gayatri"],
        japa_daily=data["japa_daily"],
        japa_total=data["japa_total"],
        best_day=timing.get("best_day", ""),
        best_time=timing.get("best_time", ""),
        facing_direction=data.get("facing_direction", "East"),
        mala=data.get("mala", ""),
        deity=data.get("deity", ""),
        reason="",  # caller fills this in
    )


def get_nakshatra_mantra(nakshatra_name: str) -> NakshatraMantra | None:
    """Return the deity mantra for a given nakshatra.

    Matches by name_en (case-insensitive). Returns None if not found.

    Args:
        nakshatra_name: English nakshatra name (e.g. "Rohini", "Ashwini").

    Returns:
        NakshatraMantra or None.
    """
    rules = load_mantra_rules()
    entries = rules.get("nakshatra_mantras", [])
    target = nakshatra_name.strip().lower()
    for entry in entries:
        if entry.get("name_en", "").lower() == target:
            return NakshatraMantra(
                nakshatra_number=entry["number"],
                nakshatra_en=entry["name_en"],
                nakshatra_hi=entry["name_hi"],
                deity=entry["deity"],
                deity_hi=entry["deity_hi"],
                mantra=entry["mantra"],
                mantra_en=entry["mantra_en"],
                extended_mantra=entry["extended_mantra"],
                japa_count=entry["japa_count"],
                deity_domain=entry["deity_domain"],
            )
    return None


def get_nakshatra_mantra_by_number(number: int) -> NakshatraMantra | None:
    """Return the deity mantra for a nakshatra by its 1-based index.

    Args:
        number: Nakshatra number 1-27.

    Returns:
        NakshatraMantra or None.
    """
    rules = load_mantra_rules()
    entries = rules.get("nakshatra_mantras", [])
    for entry in entries:
        if entry.get("number") == number:
            return NakshatraMantra(
                nakshatra_number=entry["number"],
                nakshatra_en=entry["name_en"],
                nakshatra_hi=entry["name_hi"],
                deity=entry["deity"],
                deity_hi=entry["deity_hi"],
                mantra=entry["mantra"],
                mantra_en=entry["mantra_en"],
                extended_mantra=entry["extended_mantra"],
                japa_count=entry["japa_count"],
                deity_domain=entry["deity_domain"],
            )
    return None


def _with_reason(rec: MantraRecommendation, reason: str) -> MantraRecommendation:
    """Return a copy of MantraRecommendation with a specific reason set."""
    return cast(MantraRecommendation, rec.model_copy(update={"reason": reason}))


def compute_remedy_mantras(chart: ChartData) -> list[MantraRecommendation]:
    """Derive personalized mantra recommendations from a birth chart.

    Priority order (duplicates de-duped by planet, keeping highest-priority):
      1. Lagna lord — always recommended to strengthen the native.
      2. Current dasha lord (from chart's Moon nakshatra lord as proxy when
         no explicit dasha is present).
      3. Debilitated planets — need energy reinforcement.
      4. Combust planets — hidden/suppressed, mantra restores potency.
      5. Retrograde planets if debilitated as well (double weakness).

    Rahu and Ketu are included when they are dasha lords or debilitated.

    Args:
        chart: Computed birth chart.

    Returns:
        Ordered list of MantraRecommendation, highest priority first.
        At most 5 mantras are returned to avoid overwhelming the native.
    """
    seen: dict[str, MantraRecommendation] = {}

    def _add(planet: str, reason: str) -> None:
        if planet in seen:
            return
        rec = get_mantra_for_planet(planet)
        if rec:
            seen[planet] = _with_reason(rec, reason)

    # 1. Lagna lord
    lagna_lord = SIGN_LORDS.get(chart.lagna_sign_index, "")
    if lagna_lord:
        _add(lagna_lord, f"Lagna lord of {chart.lagna_sign} — strengthens the native")

    # 2. Current dasha lord (proxy: Moon nakshatra lord = Vimshottari dasha seed)
    moon = chart.planets.get("Moon")
    if moon:
        dasha_lord = moon.nakshatra_lord
        if dasha_lord and dasha_lord != lagna_lord:
            _add(
                dasha_lord,
                f"Vimshottari dasha lord (Moon in {moon.nakshatra}) — propitiate current period",
            )

    # 3. Debilitated planets
    for pname, pdata in chart.planets.items():
        if pname in seen:
            continue
        if pdata.dignity == "debilitated":
            _add(pname, f"{pname} is debilitated in {pdata.sign} — mantra strengthens it")

    # 4. Combust planets
    for pname, pdata in chart.planets.items():
        if pname in seen:
            continue
        if pdata.is_combust and pname not in ("Sun", "Rahu", "Ketu"):
            _add(pname, f"{pname} is combust — mantra restores its significations")

    # 5. Retrograde + debilitated (double weakness)
    for pname, pdata in chart.planets.items():
        if pname in seen:
            continue
        if pdata.is_retrograde and pdata.dignity == "debilitated":
            _add(
                pname,
                f"{pname} is retrograde and debilitated — needs mantra reinforcement",
            )

    # Return top 5 in priority order
    return list(seen.values())[:5]
