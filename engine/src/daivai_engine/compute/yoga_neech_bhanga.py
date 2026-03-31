"""Neech Bhanga Raj Yoga detection — debilitation cancellation.

Source: BPHS Ch.28.
"""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData
from daivai_engine.constants import (
    DEBILITATION,
    EXALTATION,
    KENDRAS,
    SIGN_LORDS,
)
from daivai_engine.models.yoga import YogaResult


def detect_neech_bhanga(chart: ChartData) -> list[YogaResult]:
    """Detect Neech Bhanga (debilitation cancellation) — BPHS Ch.28."""
    yogas: list[YogaResult] = []

    for name, p in chart.planets.items():
        if name in ("Rahu", "Ketu"):
            continue
        if DEBILITATION.get(name) != p.sign_index:
            continue

        cancellation_reasons: list[str] = []

        # Rule 1: debilitation lord in kendra from Lagna or Moon
        debil_sign_lord = SIGN_LORDS[p.sign_index]
        lord_planet = chart.planets.get(debil_sign_lord)
        if lord_planet:
            lord_from_lagna = ((lord_planet.sign_index - chart.lagna_sign_index) % 12) + 1
            lord_from_moon = ((lord_planet.sign_index - chart.planets["Moon"].sign_index) % 12) + 1
            if lord_from_lagna in KENDRAS:
                cancellation_reasons.append(
                    f"Debilitation lord {debil_sign_lord} in kendra from Lagna"
                )
            if lord_from_moon in KENDRAS:
                cancellation_reasons.append(
                    f"Debilitation lord {debil_sign_lord} in kendra from Moon"
                )

        # Rule 2: exaltation lord of the debilitated planet in kendra
        exalt_sign = EXALTATION.get(name)
        if exalt_sign is not None:
            exalt_lord = SIGN_LORDS[exalt_sign]
            el_planet = chart.planets.get(exalt_lord)
            if el_planet:
                el_from_lagna = ((el_planet.sign_index - chart.lagna_sign_index) % 12) + 1
                if el_from_lagna in KENDRAS:
                    cancellation_reasons.append(f"Exaltation lord {exalt_lord} in kendra")

        # Rule 3: debilitated planet itself in kendra
        if p.house in KENDRAS:
            cancellation_reasons.append(f"{name} debilitated but in kendra house {p.house}")

        # Rule 4: debilitated planet is retrograde — BPHS, widely accepted
        if p.is_retrograde:
            cancellation_reasons.append(
                f"{name} debilitated but retrograde — reversal cancels weakness"
            )

        if cancellation_reasons:
            yogas.append(
                YogaResult(
                    name="Neech Bhanga Raj Yoga",
                    name_hindi="नीच भंग राज योग",
                    is_present=True,
                    planets_involved=[name],
                    houses_involved=[p.house],
                    description=f"{name} debilitated but cancelled: {'; '.join(cancellation_reasons)}",
                    effect="benefic",
                )
            )

    return yogas
