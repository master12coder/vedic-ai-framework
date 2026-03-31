"""Extended yoga detection — 70+ additional yogas beyond the basic set.

Covers: Nabhasa yogas, lunar yogas, solar yogas, Neech Bhanga,
Kartari yogas, Daridra yogas, marriage yogas, spiritual yogas.

Source: BPHS, Phaladeepika, Saravali.
"""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData
from daivai_engine.compute.yoga_extended_life import (
    detect_marriage_yogas as _detect_marriage_yogas,
)
from daivai_engine.compute.yoga_extended_life import (
    detect_spiritual_yogas as _detect_spiritual_yogas,
)
from daivai_engine.compute.yoga_extended_life import (
    detect_wealth_yogas as _detect_wealth_yogas,
)
from daivai_engine.compute.yoga_extended_lunar_solar import (
    detect_lunar_yogas as _detect_lunar_yogas,
)
from daivai_engine.compute.yoga_extended_lunar_solar import (
    detect_neech_bhanga as _detect_neech_bhanga,
)
from daivai_engine.compute.yoga_extended_lunar_solar import (
    detect_solar_yogas as _detect_solar_yogas,
)
from daivai_engine.compute.yoga_extended_misc import (
    detect_conjunction_doshas as _detect_conjunction_doshas,
)
from daivai_engine.compute.yoga_extended_misc import (
    detect_kartari_yogas as _detect_kartari_yogas,
)
from daivai_engine.compute.yoga_extended_misc import (
    detect_nabhasa_extended as _detect_nabhasa_yogas,
)
from daivai_engine.compute.yoga_extended_misc import (
    detect_vipreet_detailed as _detect_vipreet_detailed,
)
from daivai_engine.models.yoga import YogaResult


def detect_extended_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect 70+ additional yogas beyond the basic Panch Mahapurush/Raj/Dhan set.

    Args:
        chart: Computed birth chart.

    Returns:
        List of YogaResult for all detected yogas.
    """
    yogas: list[YogaResult] = []
    yogas.extend(_detect_lunar_yogas(chart))
    yogas.extend(_detect_solar_yogas(chart))
    yogas.extend(_detect_neech_bhanga(chart))
    yogas.extend(_detect_kartari_yogas(chart))
    yogas.extend(_detect_conjunction_doshas(chart))
    yogas.extend(_detect_vipreet_detailed(chart))
    yogas.extend(_detect_nabhasa_yogas(chart))
    yogas.extend(_detect_wealth_yogas(chart))
    yogas.extend(_detect_spiritual_yogas(chart))
    yogas.extend(_detect_marriage_yogas(chart))
    return yogas
