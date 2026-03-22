"""Nabhasa Ashraya and Dala Yoga detection — BPHS Chapter 13."""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData
from daivai_engine.models.yoga import YogaResult


# ── 7 classical planets (Rahu/Ketu excluded per BPHS Nabhasa rules) ──────
_CLASSICAL = frozenset(["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"])

# Natural benefics / malefics (Nabhasa classification, BPHS Ch.13)
_BENEFICS = frozenset(["Jupiter", "Venus", "Mercury", "Moon"])
_MALEFICS = frozenset(["Sun", "Mars", "Saturn"])

# Sign modality sets (sign_index values)
_CHARA = frozenset([0, 3, 6, 9])  # Movable: Aries, Cancer, Libra, Capricorn
_STHIRA = frozenset([1, 4, 7, 10])  # Fixed: Taurus, Leo, Scorpio, Aquarius
_DVISVA = frozenset([2, 5, 8, 11])  # Dual: Gemini, Virgo, Sagittarius, Pisces

# House groups
_KENDRAS = frozenset([1, 4, 7, 10])


def _consec(start: int, n: int) -> frozenset[int]:
    """Return n consecutive house numbers starting from `start` (wraps at 12)."""
    return frozenset(((start - 1 + i) % 12) + 1 for i in range(n))


def _r(
    name: str,
    name_hi: str,
    houses: list[int],
    desc: str,
    effect: str,
) -> YogaResult:
    """Shorthand factory for a detected Nabhasa YogaResult."""
    return YogaResult(
        name=name,
        name_hindi=name_hi,
        is_present=True,
        planets_involved=[],
        houses_involved=houses,
        description=desc,
        effect=effect,
    )


def _ashraya_yogas(signs: list[int]) -> list[YogaResult]:
    """Ashraya Yogas — all 7 planets in one modality class. BPHS 13.3-5."""
    sign_set = set(signs)
    yogas: list[YogaResult] = []

    if sign_set <= _CHARA:
        yogas.append(
            _r(
                "Rajju Yoga",
                "रज्जु योग",
                [],
                "All planets in movable (chara) signs — restless, travels widely, adaptable",
                "mixed",
            )
        )
    if sign_set <= _STHIRA:
        yogas.append(
            _r(
                "Musala Yoga",
                "मुसल योग",
                [],
                "All planets in fixed (sthira) signs — stable, determined, accumulates wealth",
                "benefic",
            )
        )
    if sign_set <= _DVISVA:
        yogas.append(
            _r(
                "Nala Yoga",
                "नल योग",
                [],
                "All planets in dual (dvisvabhava) signs — versatile, skilled in many fields",
                "mixed",
            )
        )
    return yogas


def _dala_yogas(chart: ChartData) -> list[YogaResult]:
    """Dala Yogas — benefics or malefics exclusively in kendra houses. BPHS 13.6-7."""
    yogas: list[YogaResult] = []

    b_houses = [chart.planets[n].house for n in _BENEFICS if n in chart.planets]
    m_houses = [chart.planets[n].house for n in _MALEFICS if n in chart.planets]

    if b_houses and all(h in _KENDRAS for h in b_houses):
        yogas.append(
            _r(
                "Maala Yoga",
                "माला योग",
                sorted(_KENDRAS),
                "All benefics in kendra houses — garlanded with fortune, joy and prosperity",
                "benefic",
            )
        )
    if m_houses and all(h in _KENDRAS for h in m_houses):
        yogas.append(
            _r(
                "Sarpa Yoga",
                "सर्प योग",
                sorted(_KENDRAS),
                "All malefics in kendra houses — cruel, wicked, dependent on others, poverty",
                "malefic",
            )
        )
    return yogas
