"""All 16 Tajaka Yogas for Varshphal (Annual Chart) analysis.

Tajaka is the Perso-Arabic annual astrology system integrated into Vedic
jyotish. The 16 yogas describe planetary relationship states in the annual
chart and determine whether significations will be fulfilled, delayed,
blocked, or transferred in the year.

Aspects used in Tajaka (sign-based, bidirectional):
  Conjunction (0°): same sign
  Sextile   (60°): 3 signs apart
  Square    (90°): 4 signs apart
  Trine    (120°): 5 signs apart
  Opposition(180°): 7 signs apart

Orb: 5° from exact aspect degree (standard Tajaka orb).
"Applying" = fast planet approaching aspect with slow planet.
"Separating" = fast planet moving away from aspect with slow planet.

Sources: Tajaka Neelakanthi (Nilakantha), Dr. B.V. Raman's "Varshphal",
         Jahangir's Tajaka Manual, Komilla Sutton commentary.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from daivai_engine.compute.tajaka_helpers import (
    _TAJAKA_ORB,
    _compute_tajaka_aspect,
    _fast_slow,
    _find_blocking_planet,
    _is_mutual_reception,
    check_moon_yogas,
    check_musaripha,
    check_no_aspect_yogas,
)
from daivai_engine.models.chart import ChartData, PlanetData


class TajakaYoga(BaseModel):
    """A single detected Tajaka yoga between two planets in an annual chart."""

    model_config = ConfigDict(frozen=True)

    name: str  # Yoga name (e.g., "Ithasala")
    name_hi: str  # Hindi/Sanskrit name
    fast_planet: str  # Faster-moving planet
    slow_planet: str  # Slower-moving planet
    aspect_type: str  # conjunction/sextile/square/trine/opposition
    orb: float = Field(ge=0)  # Degrees from exact aspect
    is_applying: bool  # True=applying (fast→slow), False=separating
    is_positive: bool  # Generally favorable yoga or not
    description: str  # Brief interpretation


def detect_all_tajaka_yogas(chart: ChartData) -> list[TajakaYoga]:
    """Detect all 16 Tajaka yogas in the given chart (annual or natal).

    Iterates over all planet pairs and checks each of the 16 yoga conditions.
    Multiple yogas can fire for the same pair. Results are sorted with
    positive yogas first.

    Args:
        chart: Annual chart (Varshphal) or natal chart.

    Returns:
        List of detected TajakaYoga, sorted positive-first.
    """
    planets = {n: p for n, p in chart.planets.items() if n not in ("Rahu", "Ketu")}
    planet_list = list(planets.items())

    yogas: list[TajakaYoga] = []
    for i, (n1, p1) in enumerate(planet_list):
        for j, (n2, p2) in enumerate(planet_list):
            if i >= j:
                continue
            fast, slow, fp, sp = _fast_slow(n1, p1, n2, p2)
            if fast is None or slow is None or fp is None or sp is None:
                continue

            pair_yogas = _check_pair(fast, fp, slow, sp, chart)
            yogas.extend(pair_yogas)

    # Also check Moon-specific yogas (Kamboola, Gairi-Kamboola)
    check_moon_yogas(chart, yogas, TajakaYoga)

    yogas.sort(key=lambda y: (not y.is_positive, y.orb))
    return yogas


def _check_pair(
    fast_name: str,
    fast: PlanetData,
    slow_name: str,
    slow: PlanetData,
    chart: ChartData,
) -> list[TajakaYoga]:
    """Check all yoga conditions for a single fast-slow planet pair."""
    results: list[TajakaYoga] = []

    aspect = _compute_tajaka_aspect(fast, slow)
    if aspect is None:
        results += check_no_aspect_yogas(fast_name, fast, slow_name, slow, TajakaYoga)
        return results

    aspect_type, orb, is_applying = aspect

    # 1. Ithasala — applying aspect (the primary good yoga)
    if is_applying and not fast.is_combust and fast.dignity != "debilitated":
        results.append(
            TajakaYoga(
                name="Ithasala",
                name_hi="इत्थशाल",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=True,
                is_positive=True,
                description=(
                    f"{fast_name} applying {aspect_type} to {slow_name} "
                    f"(orb {orb:.1f}°) — significations will be fulfilled."
                ),
            )
        )

    # 2. Ishrafa — separating aspect (missed opportunity)
    if not is_applying and orb <= _TAJAKA_ORB:
        results.append(
            TajakaYoga(
                name="Ishrafa",
                name_hi="इशराफ",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=False,
                is_positive=False,
                description=(
                    f"{fast_name} separating from {aspect_type} to {slow_name} "
                    f"(orb {orb:.1f}°) — matter was initiated but may not complete."
                ),
            )
        )

    # 3. Ikkabal — fast planet has greater degrees in sign (applying but faster)
    if is_applying and fast.degree_in_sign < slow.degree_in_sign:
        results.append(
            TajakaYoga(
                name="Ikkabal",
                name_hi="इकबाल",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=True,
                is_positive=True,
                description=(
                    f"{fast_name} in Ikkabal with {slow_name} — "
                    "vigorous application, matter comes to fruition quickly."
                ),
            )
        )

    # 4. Induvara — exact or near-exact aspect (both same degree)
    if orb <= 1.0:
        results.append(
            TajakaYoga(
                name="Induvara",
                name_hi="इन्दुवर",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=is_applying,
                is_positive=True,
                description=(
                    f"{fast_name} and {slow_name} at near-exact {aspect_type} "
                    f"(orb {orb:.2f}°) — Induvara: extremely powerful indication."
                ),
            )
        )

    # 5. Nakta — Moon transfers light between fast and slow
    from daivai_engine.compute.tajaka_helpers import _check_nakta

    moon = chart.planets.get("Moon")
    if moon and fast_name != "Moon" and slow_name != "Moon":
        nakta_data = _check_nakta(fast_name, fast, slow_name, slow, moon)
        if nakta_data:
            results.append(TajakaYoga(**nakta_data))

    # 6. Yamaya — mutual reception (in each other's sign) with aspect
    if _is_mutual_reception(fast_name, fast, slow_name, slow):
        results.append(
            TajakaYoga(
                name="Yamaya",
                name_hi="यमाय",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=is_applying,
                is_positive=True,
                description=(
                    f"{fast_name} and {slow_name} in mutual reception "
                    f"with {aspect_type} — Yamaya: strong promise of results."
                ),
            )
        )

    # 7. Drippha — fast planet combust, still applying
    if is_applying and fast.is_combust:
        results.append(
            TajakaYoga(
                name="Drippha",
                name_hi="द्रिप्फा",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=True,
                is_positive=False,
                description=(
                    f"{fast_name} combust but applying to {slow_name} — "
                    "Drippha: matter may begin but weakens before completion."
                ),
            )
        )

    # 8. Kuttha — fast planet debilitated, applying
    if is_applying and fast.dignity == "debilitated":
        results.append(
            TajakaYoga(
                name="Kuttha",
                name_hi="कुत्था",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=True,
                is_positive=False,
                description=(
                    f"{fast_name} debilitated, applying to {slow_name} — "
                    "Kuttha: degraded application; results come with humiliation or loss."
                ),
            )
        )

    # 9. Tambira — fast planet in inimical sign, applying
    if is_applying and fast.dignity in ("enemy",) and not fast.is_combust:
        results.append(
            TajakaYoga(
                name="Tambira",
                name_hi="तम्बीर",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=True,
                is_positive=False,
                description=(
                    f"{fast_name} in enemy sign, applying to {slow_name} — "
                    "Tambira: application happens under hostile conditions."
                ),
            )
        )

    # 10. Durupha — both planets in adverse dignity (debilitated or combust)
    slow_adverse = slow.dignity == "debilitated" or (slow.is_combust and slow_name != "Sun")
    fast_adverse = fast.dignity == "debilitated" or fast.is_combust
    if fast_adverse and slow_adverse and is_applying:
        results.append(
            TajakaYoga(
                name="Durupha",
                name_hi="दुरुफा",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=True,
                is_positive=False,
                description=(
                    f"Both {fast_name} and {slow_name} in adverse condition — "
                    "Durupha: matter will not fructify; double obstruction."
                ),
            )
        )

    # 11. Radda — frustration (another planet blocks between fast and slow)
    if is_applying:
        blocker = _find_blocking_planet(fast_name, fast, slow_name, slow, chart)
        if blocker:
            results.append(
                TajakaYoga(
                    name="Radda",
                    name_hi="रद्दा",
                    fast_planet=fast_name,
                    slow_planet=slow_name,
                    aspect_type=aspect_type,
                    orb=orb,
                    is_applying=True,
                    is_positive=False,
                    description=(
                        f"{fast_name} applying to {slow_name} but blocked by {blocker} — "
                        "Radda: application is frustrated; matter interrupted."
                    ),
                )
            )

    # 16. Musaripha — fast planet separating from slow while applying to another
    if not is_applying:
        musaripha = check_musaripha(fast_name, fast, slow_name, slow, chart, TajakaYoga)
        if musaripha:
            results.append(musaripha)  # type: ignore[arg-type]

    return results
