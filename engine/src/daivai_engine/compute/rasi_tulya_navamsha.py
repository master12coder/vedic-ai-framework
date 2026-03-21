"""Rasi Tulya Navamsha (RTN) — timing via D9-on-D1 overlay.

For each planet, the D9 sign is overlaid onto the D1 chart. The sign
relationship (kendra, trikona, dusthana, etc.) reveals how and when
planetary results manifest: when a transit activates the D9 sign in D1,
the planet's karmic promise is triggered.

Pushkara Navamsha integration: planets in Pushkara positions at birth
deliver results with enhanced auspiciousness when activated.

Source: Parashari timing principles; Jaimini system cross-reference.
"""

from __future__ import annotations

from daivai_engine.compute.divisional import compute_navamsha_sign
from daivai_engine.compute.pushkara import check_pushkara
from daivai_engine.constants import PLANETS, SIGNS
from daivai_engine.models.chart import ChartData
from daivai_engine.models.rasi_tulya import RTNPlanet, RTNResult


# Sign distances and their classifications per task specification:
# vargottama=0, kendra=3/6/9, trikona=4/8, dusthana=5/7/11, neutral=1/2/10
_KENDRA_DISTANCES = frozenset({3, 6, 9})
_TRIKONA_DISTANCES = frozenset({4, 8})
_DUSTHANA_DISTANCES = frozenset({5, 7, 11})


def _classify_relationship(d1_sign: int, d9_sign: int) -> tuple[int, str]:
    """Return (sign_distance, relationship) for D1→D9 sign pair.

    Distance is measured forward (0-11) from D1 sign to D9 sign.
    """
    dist = (d9_sign - d1_sign) % 12
    if dist == 0:
        return 0, "vargottama"
    if dist in _KENDRA_DISTANCES:
        return dist, "kendra"
    if dist in _TRIKONA_DISTANCES:
        return dist, "trikona"
    if dist in _DUSTHANA_DISTANCES:
        return dist, "dusthana"
    return dist, "neutral"  # 1, 2, 10


def _timing_note(d9_sign: int, relationship: str) -> str:
    """Return timing guidance based on RTN relationship."""
    sign_name = SIGNS[d9_sign]
    match relationship:
        case "vargottama":
            return (
                f"Results activate readily — D9 sign same as D1 ({sign_name}). "
                "Planet is at maximum promise."
            )
        case "kendra":
            return (
                f"Results manifest when transit activates {sign_name} (D9 kendra alignment). "
                "Delivery is structured and directional."
            )
        case "trikona":
            return (
                f"Results flow naturally when {sign_name} is transited (trikona support). "
                "Ease and grace in delivery."
            )
        case "dusthana":
            return (
                f"Delayed or obstructed results; transit of {sign_name} may trigger challenges. "
                "Effort required to manifest."
            )
        case _:
            return (
                f"Results emerge gradually when {sign_name} is activated. "
                "Neutral — requires chart context."
            )


def compute_rtn(chart: ChartData) -> RTNResult:
    """Compute Rasi Tulya Navamsha overlay for all planets.

    For each of the 9 planets, determines the sign relationship between
    its D1 placement and its D9 sign. Integrates Pushkara Navamsha status
    from the existing pushkara module.

    Args:
        chart: A fully computed birth chart.

    Returns:
        RTNResult with per-planet RTN data, summary of vargottama and
        Pushkara-active planets.
    """
    pushkara_map = {p.planet: p for p in check_pushkara(chart)}

    rtn_planets: list[RTNPlanet] = []
    vargottama: list[str] = []
    pushkara_active: list[str] = []

    for planet_name in PLANETS:
        p = chart.planets[planet_name]
        d9_sign = compute_navamsha_sign(p.longitude)
        dist, rel = _classify_relationship(p.sign_index, d9_sign)

        pk = pushkara_map.get(planet_name)
        in_pushkara = pk.is_pushkara_navamsha if pk else False
        pk_type = pk.pushkara_type if pk else "none"

        if rel == "vargottama":
            vargottama.append(planet_name)
        if pk_type != "none":
            pushkara_active.append(planet_name)

        rtn_planets.append(
            RTNPlanet(
                planet=planet_name,
                d1_sign_index=p.sign_index,
                d9_sign_index=d9_sign,
                d1_sign=SIGNS[p.sign_index],
                d9_sign=SIGNS[d9_sign],
                sign_distance=dist,
                relationship=rel,
                is_pushkara_navamsha=in_pushkara,
                pushkara_type=pk_type,
                timing_note=_timing_note(d9_sign, rel),
            )
        )

    summary = _build_summary(vargottama, pushkara_active)
    return RTNResult(
        planets=rtn_planets,
        vargottama_planets=vargottama,
        pushkara_planets=pushkara_active,
        summary=summary,
    )


def _build_summary(vargottama: list[str], pushkara: list[str]) -> str:
    """Compose a one-line RTN summary."""
    parts: list[str] = []
    if vargottama:
        parts.append(f"Vargottama: {', '.join(vargottama)} — full karmic delivery")
    if pushkara:
        parts.append(f"Pushkara-active: {', '.join(pushkara)} — auspiciously timed results")
    return "; ".join(parts) if parts else "No special RTN alignments in this chart"
