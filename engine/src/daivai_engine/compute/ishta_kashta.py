"""Ishta-Kashta Phala — good/bad result potential from Shadbala.

Derives benefic and malefic potential from a planet's Uchcha Bala
and Cheshta Bala components. Positive net = more good than harm.

Source: BPHS Chapter 27.
"""

from __future__ import annotations

import math

from daivai_engine.constants import EXALTATION, EXALTATION_DEGREE
from daivai_engine.models.chart import ChartData
from daivai_engine.models.strength import IshtaKashtaPhala, ShadbalaResult


def compute_ishta_kashta(
    chart: ChartData,
    shadbala_results: list[ShadbalaResult],
) -> list[IshtaKashtaPhala]:
    """Compute Ishta-Kashta Phala for each planet.

    Formula (BPHS Ch.27):
    - Uchcha Bala = (180 - |planet_lon - exaltation_lon|) / 3, capped 0-60
    - Cheshta Bala = from shadbala computation
    - Ishta Phala = sqrt(Uchcha_Bala * Cheshta_Bala)
    - Kashta Phala = sqrt((60 - Uchcha_Bala) * (60 - Cheshta_Bala))
    - Net = Ishta - Kashta

    Args:
        chart: Computed birth chart.
        shadbala_results: Pre-computed shadbala results.

    Returns:
        List of IshtaKashtaPhala, one per planet.
    """
    results: list[IshtaKashtaPhala] = []

    for sb in shadbala_results:
        name = sb.planet
        p = chart.planets.get(name)
        if p is None:
            continue

        uchcha = _uchcha_bala(name, p.longitude)
        cheshta = min(max(sb.cheshta_bala, 0.0), 60.0)

        # BPHS formula: square root of products
        ishta = math.sqrt(max(uchcha * cheshta, 0.0))
        kashta = math.sqrt(max((60.0 - uchcha) * (60.0 - cheshta), 0.0))
        net = ishta - kashta

        classification = _classify(net)
        results.append(
            IshtaKashtaPhala(
                planet=name,
                ishta_phala=round(ishta, 2),
                kashta_phala=round(kashta, 2),
                net_effect=round(net, 2),
                classification=classification,
            )
        )

    return results


def _uchcha_bala(planet: str, longitude: float) -> float:
    """Compute Uchcha Bala (exaltation strength) in shashtiyamsas.

    = (180 - |planet_longitude - exaltation_longitude|) / 3
    Range: 0 to 60.
    """
    exalt_sign = EXALTATION.get(planet)
    exalt_deg = EXALTATION_DEGREE.get(planet)
    if exalt_sign is None or exalt_deg is None:
        return 30.0  # Neutral for Rahu/Ketu (shouldn't reach here)

    exalt_lon = exalt_sign * 30.0 + exalt_deg
    diff = abs(longitude - exalt_lon) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    return max(0.0, min(60.0, (180.0 - diff) / 3.0))


def _classify(net: float) -> str:
    """Classify net effect into 5 categories."""
    if net > 20.0:
        return "strongly_benefic"
    if net > 5.0:
        return "mildly_benefic"
    if net > -5.0:
        return "neutral"
    if net > -20.0:
        return "mildly_malefic"
    return "strongly_malefic"
