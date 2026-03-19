"""Moorthy Nirnaya — transit quality classification from SAV bindus.

Classifies the quality of a planet's transit through a sign based on
how many Sarvashtakavarga bindus that sign has.

Source: BPHS Ashtakavarga chapter.
"""

from __future__ import annotations

from daivai_engine.compute.ashtakavarga import compute_ashtakavarga
from daivai_engine.models.chart import ChartData
from daivai_engine.models.special import MoorthyNirnaya


def classify_transit_moorthy(
    chart: ChartData,
    planet: str,
    transit_sign: int,
) -> MoorthyNirnaya:
    """Classify transit quality using SAV bindus.

    Classification:
    - 5+ bindus = Swarna (Gold) = excellent results
    - 4 bindus = Rajata (Silver) = good results
    - 3 bindus = Tamra (Copper) = mixed results
    - 0-2 bindus = Loha (Iron) = poor results

    Args:
        chart: Natal chart (for ashtakavarga computation).
        planet: Transiting planet name.
        transit_sign: Sign index (0-11) being transited.

    Returns:
        MoorthyNirnaya classification.
    """
    avk = compute_ashtakavarga(chart)
    bindus = avk.sarva[transit_sign] if transit_sign < len(avk.sarva) else 0

    if bindus >= 30:
        cls, cls_hi = "swarna", "स्वर्ण"
    elif bindus >= 25:
        cls, cls_hi = "rajata", "रजत"
    elif bindus >= 22:
        cls, cls_hi = "tamra", "ताम्र"
    else:
        cls, cls_hi = "loha", "लोह"

    return MoorthyNirnaya(
        planet=planet,
        transit_sign=transit_sign,
        bindus=bindus,
        classification=cls,
        classification_hi=cls_hi,
    )
