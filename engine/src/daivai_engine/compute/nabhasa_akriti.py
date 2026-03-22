"""Nabhasa Akriti Yoga detection — BPHS Chapter 13."""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData
from daivai_engine.compute.nabhasa_ashraya_dala import _BENEFICS, _MALEFICS, _consec, _r
from daivai_engine.models.yoga import YogaResult


# House groups
_KENDRAS = frozenset([1, 4, 7, 10])
_PANAPHARA = frozenset([2, 5, 8, 11])
_APOKLIMA = frozenset([3, 6, 9, 12])
_TRIKONAS = frozenset([1, 5, 9])
_ODD = frozenset([1, 3, 5, 7, 9, 11])
_EVEN = frozenset([2, 4, 6, 8, 10, 12])

# Adjacent kendra pairs (sequential order: 1→4→7→10→1)
_ADJ_KENDRA_PAIRS: list[frozenset[int]] = [
    frozenset([1, 4]),
    frozenset([4, 7]),
    frozenset([7, 10]),
    frozenset([10, 1]),
]

# Data-driven tables for consecutive-house pattern yogas
_FOUR_CONSEC: list[tuple[int, str, str, str, str]] = [
    (
        1,
        "Yupa Yoga",
        "यूप योग",
        "All planets in houses 1-4 — sacrifice post, renunciation, devotion",
        "benefic",
    ),
    (
        4,
        "Ishu Yoga",
        "इषु योग",
        "All planets in houses 4-7 — arrow, piercing intellect, forceful career",
        "mixed",
    ),
    (
        7,
        "Shakti Yoga",
        "शक्ति योग",
        "All planets in houses 7-10 — power, achievements through partnerships",
        "mixed",
    ),
    (
        10,
        "Danda Yoga",
        "दण्ड योग",
        "All planets in houses 10-1 — staff of authority, discipline, governance",
        "mixed",
    ),
]

_SEVEN_NAMED: list[tuple[int, str, str, str, str]] = [
    (
        1,
        "Naukaa Yoga",
        "नौका योग",
        "All planets in 7 houses from H1 — boat, trade, travel, adventure",
        "mixed",
    ),
    (
        4,
        "Koota Yoga",
        "कूट योग",
        "All planets in 7 houses from H4 — mountain peak, secretive, strategic",
        "mixed",
    ),
    (
        7,
        "Chhatra Yoga",
        "छत्र योग",
        "All planets in 7 houses from H7 — royal umbrella, protection, patronage",
        "benefic",
    ),
    (
        10,
        "Chaapa Yoga",
        "चाप योग",
        "All planets in 7 houses from H10 — bow shape, skilled focus, craftsmanship",
        "mixed",
    ),
]


def _chart_house(chart: ChartData, planet: str) -> int:
    """Return house number for a classical planet (0 if planet absent)."""
    p = chart.planets.get(planet)
    return p.house if p else 0


def _akriti_yogas(chart: ChartData, houses: list[int], house_set: set[int]) -> list[YogaResult]:
    """Akriti Yogas — 20 geometric house-pattern yogas. BPHS 13.8-27."""
    yogas: list[YogaResult] = []

    def fit(valid: frozenset[int]) -> bool:
        """True when all classical planet houses lie within `valid`."""
        return house_set <= valid

    # ── 6. Gada — all planets in 2 adjacent kendra houses ──
    for pair in _ADJ_KENDRA_PAIRS:
        if fit(pair):
            yogas.append(
                _r(
                    "Gada Yoga",
                    "गदा योग",
                    sorted(pair),
                    f"All planets in adjacent kendra houses {sorted(pair)} — Vishnu's mace, authority",
                    "benefic",
                )
            )
            break

    # ── 7. Shakata — all planets only in H1 and H7 ──
    if fit(frozenset([1, 7])):
        yogas.append(
            _r(
                "Shakata Yoga",
                "शकट योग",
                [1, 7],
                "All planets in H1 and H7 — cart wheel, rises and falls in fortune",
                "mixed",
            )
        )

    # ── 8. Shringataka — all planets in trikona houses (1, 5, 9) ──
    if fit(_TRIKONAS):
        yogas.append(
            _r(
                "Shringataka Yoga",
                "श्रृंगाटक योग",
                [1, 5, 9],
                "All planets in trikona houses — triangular peak, powerful and blessed",
                "benefic",
            )
        )

    # ── 9. Hala — all planets in 3 consecutive houses from a trikona ──
    for ts in (1, 5, 9):
        h3 = _consec(ts, 3)
        if fit(h3):
            yogas.append(
                _r(
                    "Hala Yoga",
                    "हल योग",
                    sorted(h3),
                    f"All planets in 3 houses from trikona {ts} — plough, agricultural, industrious",
                    "mixed",
                )
            )
            break

    # ── 10. Vajra — benefics in H1/H7, malefics in H4/H10 ──
    b_set = {_chart_house(chart, n) for n in _BENEFICS}
    m_set = {_chart_house(chart, n) for n in _MALEFICS}
    if b_set <= {1, 7} and m_set <= {4, 10}:
        yogas.append(
            _r(
                "Vajra Yoga",
                "वज्र योग",
                [1, 4, 7, 10],
                "Benefics in H1/H7, malefics in H4/H10 — thunderbolt, courageous, enduring",
                "benefic",
            )
        )

    # ── 11. Yava — malefics in H1/H7, benefics in H4/H10 ──
    if m_set <= {1, 7} and b_set <= {4, 10}:
        yogas.append(
            _r(
                "Yava Yoga",
                "यव योग",
                [1, 4, 7, 10],
                "Malefics in H1/H7, benefics in H4/H10 — barley grain, comfortable middle life",
                "mixed",
            )
        )

    # ── 12. Kamala (Padma) — all planets in 4 kendra houses ──
    if fit(_KENDRAS):
        yogas.append(
            _r(
                "Kamala Yoga",
                "कमल योग",
                [1, 4, 7, 10],
                "All planets in kendras — lotus, exceptional fortune and kingly status",
                "benefic",
            )
        )

    # ── 13. Vaapi — all in panaphara OR apoklima houses ──
    if fit(_PANAPHARA):
        yogas.append(
            _r(
                "Vaapi Yoga",
                "वापी योग",
                [2, 5, 8, 11],
                "All planets in panaphara houses — well-digger, self-made, persistent effort",
                "mixed",
            )
        )
    elif fit(_APOKLIMA):
        yogas.append(
            _r(
                "Vaapi Yoga",
                "वापी योग",
                [3, 6, 9, 12],
                "All planets in apoklima houses — hidden effort, spiritual and charitable nature",
                "mixed",
            )
        )

    # ── 14-17. Four-consecutive-house yogas (Yupa / Ishu / Shakti / Danda) ──
    for start, name, name_hi, desc, effect in _FOUR_CONSEC:
        h4 = _consec(start, 4)
        if fit(h4):
            yogas.append(_r(name, name_hi, sorted(h4), desc, effect))

    # ── 18-21. Seven-consecutive-house yogas (Naukaa / Koota / Chhatra / Chaapa) ──
    seven_named_found = False
    for start, name, name_hi, desc, effect in _SEVEN_NAMED:
        h7 = _consec(start, 7)
        if fit(h7):
            yogas.append(_r(name, name_hi, sorted(h7), desc, effect))
            seven_named_found = True

    # ── 22. Ardha Chandra — 7 consecutive houses, NOT starting at 1/4/7/10 ──
    if not seven_named_found:
        for start in (2, 3, 5, 6, 8, 9, 11, 12):
            h7 = _consec(start, 7)
            if fit(h7):
                yogas.append(
                    _r(
                        "Ardha Chandra Yoga",
                        "अर्धचन्द्र योग",
                        sorted(h7),
                        f"All planets in 7 consecutive houses from H{start} — half moon, handsome, balanced",
                        "benefic",
                    )
                )
                break

    # ── 23. Chakra — all planets in odd houses ──
    if fit(_ODD):
        yogas.append(
            _r(
                "Chakra Yoga",
                "चक्र योग",
                sorted(_ODD),
                "All planets in odd houses — wheel of sovereignty, powerful ruler",
                "benefic",
            )
        )

    # ── 24. Samudra — all planets in even houses ──
    if fit(_EVEN):
        yogas.append(
            _r(
                "Samudra Yoga",
                "समुद्र योग",
                sorted(_EVEN),
                "All planets in even houses — ocean of wealth, commanding, affluent",
                "benefic",
            )
        )

    return yogas
