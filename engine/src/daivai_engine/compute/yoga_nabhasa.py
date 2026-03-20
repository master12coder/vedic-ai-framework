"""All 32 Nabhasa Yoga detection — BPHS Chapter 13.

Nabhasa yogas are "sky patterns" based on how the 7 classical planets
(Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn) are distributed
across signs and houses. Rahu and Ketu are excluded per BPHS.

Categories
----------
Ashraya (3)  — sign modality: all in movable / fixed / dual signs
Dala (2)     — benefic or malefic planets exclusively in kendras
Akriti (20)  — geometric house-distribution patterns
Sankhya (7)  — based on number of distinct houses occupied

Precedence: Akriti yogas take precedence over Sankhya yogas.
Among Sankhya yogas, exactly one applies (mutually exclusive).

Source: BPHS Chapter 13.
"""

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


# ── Public API ────────────────────────────────────────────────────────────


def detect_nabhasa_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect all 32 Nabhasa (sky pattern) yogas — BPHS Ch.13.

    Only the 7 classical planets are considered; Rahu/Ketu are excluded.
    Akriti yogas take precedence over Sankhya yogas when both conditions
    are satisfied.  Among Sankhya yogas, exactly one applies.

    Args:
        chart: Computed birth chart.

    Returns:
        List of detected Nabhasa YogaResults (all have is_present=True).
    """
    # Gather sign indices and house numbers for the 7 classical planets
    signs: list[int] = []
    houses: list[int] = []
    for name, p in chart.planets.items():
        if name in _CLASSICAL:
            signs.append(p.sign_index)
            houses.append(p.house)

    house_set = set(houses)
    n_houses = len(house_set)

    yogas: list[YogaResult] = []
    yogas.extend(_ashraya_yogas(signs))
    yogas.extend(_dala_yogas(chart))

    akriti = _akriti_yogas(chart, houses, house_set)
    yogas.extend(akriti)

    # Sankhya yogas only when no Akriti yoga applies
    if not akriti:
        sankhya = _sankhya_yoga(n_houses)
        if sankhya:
            yogas.append(sankhya)

    return yogas


# ── Helpers ───────────────────────────────────────────────────────────────


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


# ── Category 1: Ashraya Yogas ─────────────────────────────────────────────


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


# ── Category 2: Dala Yogas ────────────────────────────────────────────────


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


# ── Category 3: Akriti Yogas ──────────────────────────────────────────────


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


def _chart_house(chart: ChartData, planet: str) -> int:
    """Return house number for a classical planet (0 if planet absent)."""
    p = chart.planets.get(planet)
    return p.house if p else 0


# ── Category 4: Sankhya Yogas ─────────────────────────────────────────────

_SANKHYA_MAP: dict[int, tuple[str, str, str, str]] = {
    1: (
        "Vallaki Yoga",
        "वल्लकी योग",
        "All 7 planets in 1 house — Veena (lute), musical, artistic, royal performer",
        "benefic",
    ),
    2: (
        "Dama Yoga",
        "दाम योग",
        "All 7 planets in 2 houses — garland, community leader, generous and wealthy",
        "benefic",
    ),
    3: (
        "Paasha Yoga",
        "पाश योग",
        "All 7 planets in 3 houses — noose, scheming, enslaved to work and duties",
        "malefic",
    ),
    4: (
        "Kedara Yoga",
        "केदार योग",
        "All 7 planets in 4 houses — field, helps many, service-oriented life",
        "mixed",
    ),
    5: (
        "Shoola Yoga",
        "शूल योग",
        "All 7 planets in 5 houses — trident, combative, faces many hardships",
        "malefic",
    ),
    6: (
        "Yuga Yoga",
        "युग योग",
        "All 7 planets in 6 houses — yoke, heretical views, poor and wretched",
        "malefic",
    ),
    7: (
        "Gola Yoga",
        "गोल योग",
        "All 7 planets in 7 houses — sphere, lonely, impoverished, helpless",
        "malefic",
    ),
}


def _sankhya_yoga(n_houses: int) -> YogaResult | None:
    """Return the applicable Sankhya Yoga based on distinct houses occupied. BPHS 13.28-34.

    Exactly one Sankhya yoga applies (they are mutually exclusive by definition).
    Maximum n_houses for 7 planets is 7.
    """
    count = min(n_houses, 7)
    entry = _SANKHYA_MAP.get(count)
    if not entry:
        return None
    name, name_hi, desc, effect = entry
    return _r(name, name_hi, [], desc, effect)
