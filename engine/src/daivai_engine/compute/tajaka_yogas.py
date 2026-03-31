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

from daivai_engine.compute.tajaka_helpers import _fast_slow
from daivai_engine.compute.tajaka_yoga_checks import check_moon_yogas
from daivai_engine.compute.tajaka_yoga_detectors import _check_pair
from daivai_engine.models.chart import ChartData


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

            pair_yogas = _check_pair(fast, fp, slow, sp, chart, TajakaYoga)
            yogas.extend(pair_yogas)

    # Also check Moon-specific yogas (Kamboola, Gairi-Kamboola)
    check_moon_yogas(chart, yogas, TajakaYoga)

    yogas.sort(key=lambda y: (not y.is_positive, y.orb))
    return yogas
