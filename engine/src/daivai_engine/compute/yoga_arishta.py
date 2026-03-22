"""Arishta, Bandhana, Kemadruma-Bhanga, and Raja Yoga Bhanga detection. Orchestrator.

Covers:
  - Bandhana Yogas (bondage/imprisonment)
  - Arishta Bhanga (cancellation of danger yogas)
  - Kemadruma Bhanga with all 8 classical cancellation rules
  - Raja Yoga Bhanga (cancellation of royal yogas)

Source: BPHS Ch.19,32,40; Phaladeepika Ch.14; Saravali Ch.11.
"""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData, get_house_lord
from daivai_engine.compute.yoga_bandhana import _detect_bandhana_yogas
from daivai_engine.compute.yoga_kemadruma import _detect_arishta_bhanga, _detect_kemadruma_full
from daivai_engine.constants import KENDRAS, TRIKONAS
from daivai_engine.models.yoga import YogaResult


_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
_BENEFICS_NATURAL = {"Jupiter", "Venus"}
_BENEFICS_ALL = {"Jupiter", "Venus", "Mercury"}


def detect_arishta_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect all arishta-related yogas.

    Args:
        chart: Computed birth chart.

    Returns:
        List of YogaResults for Bandhana, Arishta Bhanga, Kemadruma Bhanga,
        and Raja Yoga Bhanga yogas.
    """
    yogas: list[YogaResult] = []
    yogas.extend(_detect_bandhana_yogas(chart))
    yogas.extend(_detect_arishta_bhanga(chart))
    yogas.extend(_detect_kemadruma_full(chart))
    yogas.extend(_detect_raja_yoga_bhanga(chart))
    return yogas


def _detect_raja_yoga_bhanga(chart: ChartData) -> list[YogaResult]:
    """Detect conditions that cancel or weaken Raj Yogas — BPHS Ch.40."""
    yogas: list[YogaResult] = []
    rahu = chart.planets["Rahu"]
    ketu = chart.planets["Ketu"]

    # Check all kendra lords for Raj Yoga Bhanga by Rahu/Ketu
    for h in KENDRAS:
        kendra_lord = get_house_lord(chart, h)
        kl = chart.planets.get(kendra_lord)
        if not kl:
            continue
        if kl.sign_index in (rahu.sign_index, ketu.sign_index):
            node = "Rahu" if kl.sign_index == rahu.sign_index else "Ketu"
            yogas.append(
                YogaResult(
                    name="Raja Yoga Bhanga (Node Conjunction)",
                    name_hindi="राज योग भंग (राहु/केतु युति)",
                    is_present=True,
                    planets_involved=[kendra_lord, node],
                    houses_involved=[h, kl.house],
                    description=(
                        f"{h}th lord ({kendra_lord}) conjunct {node} — "
                        "Raj Yoga results are shadowed and made unstable"
                    ),
                    effect="mixed",
                )
            )

    # Raja Yoga Bhanga by combustion
    for h in KENDRAS:
        lord = get_house_lord(chart, h)
        p = chart.planets.get(lord)
        if p and p.is_combust:
            yogas.append(
                YogaResult(
                    name="Raja Yoga Bhanga (Combustion)",
                    name_hindi="राज योग भंग (अस्त)",
                    is_present=True,
                    planets_involved=[lord, "Sun"],
                    houses_involved=[h, p.house],
                    description=(
                        f"{h}th lord ({lord}) combust — Raj Yoga promise "
                        "is weakened by the Sun's overwhelming radiance"
                    ),
                    effect="mixed",
                )
            )

    # Raja Yoga formed in 6th/8th house
    kendra_lords = {get_house_lord(chart, h) for h in KENDRAS}
    trikona_lords = {get_house_lord(chart, h) for h in TRIKONAS}
    for kl_name in kendra_lords:
        for tl_name in trikona_lords:
            if kl_name == tl_name:
                continue
            kp = chart.planets.get(kl_name)
            tp = chart.planets.get(tl_name)
            if kp and tp and kp.sign_index == tp.sign_index and kp.house in (6, 8):
                yogas.append(
                    YogaResult(
                        name="Raja Yoga Bhanga (Dusthana Formation)",
                        name_hindi="राज योग भंग (दुस्थान युति)",
                        is_present=True,
                        planets_involved=[kl_name, tl_name],
                        houses_involved=[kp.house],
                        description=(
                            f"Raj Yoga of {kl_name}+{tl_name} formed in "
                            f"H{kp.house} (dusthana) — royal results greatly weakened"
                        ),
                        effect="mixed",
                    )
                )

    return yogas
