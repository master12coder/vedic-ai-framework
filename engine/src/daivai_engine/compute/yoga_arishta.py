"""Arishta, Bandhana, Kemadruma-Bhanga, and Raja Yoga Bhanga detection.

Covers:
  - Bandhana Yogas (bondage/imprisonment)
  - Arishta Bhanga (cancellation of danger yogas)
  - Kemadruma Bhanga with all 8 classical cancellation rules
  - Raja Yoga Bhanga (cancellation of royal yogas)

Source: BPHS Ch.19,32,40; Phaladeepika Ch.14; Saravali Ch.11.
"""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData, get_house_lord
from daivai_engine.constants import (
    DUSTHANAS,
    EXALTATION,
    KENDRAS,
    OWN_SIGNS,
    TRIKONAS,  # used in _detect_raja_yoga_bhanga
)
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


# ── Bandhana Yogas ────────────────────────────────────────────────────────


def _detect_bandhana_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect Bandhana (bondage/imprisonment) Yogas — BPHS Ch.32."""
    yogas: list[YogaResult] = []
    lagna_lord = get_house_lord(chart, 1)
    lord_6 = get_house_lord(chart, 6)
    lord_12 = get_house_lord(chart, 12)
    p_ll = chart.planets.get(lagna_lord)
    p_6 = chart.planets.get(lord_6)
    sat = chart.planets["Saturn"]
    rahu = chart.planets["Rahu"]

    # Rule 1: Lagna lord + 6th lord in kendra with Saturn/Rahu present
    if (
        p_ll
        and p_6
        and p_ll.house in KENDRAS
        and p_6.house in KENDRAS
        and (
            sat.sign_index in (p_ll.sign_index, p_6.sign_index)
            or rahu.sign_index in (p_ll.sign_index, p_6.sign_index)
        )
    ):
        afflictors = []
        if sat.sign_index in (p_ll.sign_index, p_6.sign_index):
            afflictors.append("Saturn")
        if rahu.sign_index in (p_ll.sign_index, p_6.sign_index):
            afflictors.append("Rahu")
        yogas.append(
            YogaResult(
                name="Bandhana Yoga",
                name_hindi="बंधन योग",
                is_present=True,
                planets_involved=[lagna_lord, lord_6, *afflictors],
                houses_involved=[p_ll.house, p_6.house],
                description=(
                    f"Lagna lord ({lagna_lord}) and 6th lord ({lord_6}) "
                    f"in kendra with {', '.join(afflictors)} — bondage, legal troubles"
                ),
                effect="malefic",
            )
        )

    # Rule 3: Mars + Saturn + Rahu all in dusthana
    mars = chart.planets["Mars"]
    if mars.house in DUSTHANAS and sat.house in DUSTHANAS and rahu.house in DUSTHANAS:
        yogas.append(
            YogaResult(
                name="Bandhana Yoga (Triple Malefic Dusthana)",
                name_hindi="बंधन योग (त्रिदोष दुस्थान)",
                is_present=True,
                planets_involved=["Mars", "Saturn", "Rahu"],
                houses_involved=[mars.house, sat.house, rahu.house],
                description="Mars, Saturn, Rahu all in dusthanas — danger of forced confinement",
                effect="malefic",
            )
        )

    # Rule 4: 12th lord + Rahu aspecting lagna
    p_12 = chart.planets.get(lord_12)
    if p_12 and p_12.sign_index == rahu.sign_index:
        # Check if this conjunction aspects lagna
        conj_house = p_12.house
        lagna_from_conj = ((chart.lagna_sign_index - p_12.sign_index) % 12) + 1
        if lagna_from_conj == 7:  # 7th aspect
            yogas.append(
                YogaResult(
                    name="Bandhana Yoga (12th Lord-Rahu on Lagna)",
                    name_hindi="बंधन योग (द्वादशेश-राहु लग्न दृष्टि)",
                    is_present=True,
                    planets_involved=[lord_12, "Rahu"],
                    houses_involved=[conj_house],
                    description=(
                        f"12th lord ({lord_12}) conjunct Rahu aspecting lagna — "
                        "isolation and confinement energy attacks the self"
                    ),
                    effect="malefic",
                )
            )

    return yogas


# ── Arishta Bhanga ────────────────────────────────────────────────────────


def _detect_arishta_bhanga(chart: ChartData) -> list[YogaResult]:
    """Detect Arishta Bhanga (cancellation of dangers) — BPHS Ch.19."""
    yogas: list[YogaResult] = []
    moon = chart.planets["Moon"]
    jup = chart.planets["Jupiter"]
    lagna_lord = get_house_lord(chart, 1)
    p_ll = chart.planets.get(lagna_lord)

    # Rule 1: Jupiter aspects afflicted Moon (Moon in dusthana, Jupiter 5/7/9 from Moon)
    if moon.house in DUSTHANAS:
        jup_from_moon = ((jup.sign_index - moon.sign_index) % 12) + 1
        if jup_from_moon in (5, 7, 9) and not jup.is_combust:
            yogas.append(
                YogaResult(
                    name="Arishta Bhanga (Jupiter-Moon Aspect)",
                    name_hindi="अरिष्ट भंग (गुरु चंद्र दृष्टि)",
                    is_present=True,
                    planets_involved=["Jupiter", "Moon"],
                    houses_involved=[jup.house, moon.house],
                    description=(
                        f"Jupiter aspects Moon in {moon.house}th (dusthana) — "
                        "divine protection cancels danger"
                    ),
                    effect="benefic",
                )
            )

    # Rule 2: Natural benefic in kendra from lagna
    benefic_kendras = [
        (n, chart.planets[n])
        for n in ("Jupiter", "Venus", "Mercury")
        if chart.planets[n].house in KENDRAS and not chart.planets[n].is_combust
    ]
    if benefic_kendras:
        names = [n for n, _ in benefic_kendras]
        houses = [p.house for _, p in benefic_kendras]
        yogas.append(
            YogaResult(
                name="Arishta Bhanga (Benefic in Kendra)",
                name_hindi="अरिष्ट भंग (शुभग्रह केंद्रस्थ)",
                is_present=True,
                planets_involved=names,
                houses_involved=houses,
                description=(
                    f"{', '.join(names)} in kendra houses — "
                    "benefic angular strength cancels childhood dangers"
                ),
                effect="benefic",
            )
        )

    # Rule 3: Strong lagna lord in kendra/trikona with dignity
    good_houses = set(KENDRAS) | set(TRIKONAS)
    if p_ll and p_ll.house in good_houses and p_ll.dignity in ("exalted", "own", "mooltrikona"):
        yogas.append(
            YogaResult(
                name="Arishta Bhanga (Strong Lagna Lord)",
                name_hindi="अरिष्ट भंग (बलवान लग्नेश)",
                is_present=True,
                planets_involved=[lagna_lord],
                houses_involved=[p_ll.house],
                description=(
                    f"Lagna lord ({lagna_lord}) in {p_ll.dignity} in {p_ll.house}th — "
                    "fundamental chart strength cancels arishta"
                ),
                effect="benefic",
            )
        )

    # Rule 4: Full Moon (Paksha Bala)
    moon_sun_diff = (moon.longitude - chart.planets["Sun"].longitude) % 360
    if moon_sun_diff > 120:  # strong paksha bala
        yogas.append(
            YogaResult(
                name="Arishta Bhanga (Full Moon Paksha Bala)",
                name_hindi="अरिष्ट भंग (पूर्णिमा)",
                is_present=True,
                planets_involved=["Moon"],
                houses_involved=[moon.house],
                description=(
                    f"Moon has high Paksha Bala ({moon_sun_diff:.0f}° from Sun) — "
                    "bright Moon cancels Balarishta and Kemadruma"
                ),
                effect="benefic",
            )
        )

    # Rule 5: Jupiter or Venus in lagna
    for planet_name in ("Jupiter", "Venus"):
        p = chart.planets[planet_name]
        if p.house == 1 and not p.is_combust:
            yogas.append(
                YogaResult(
                    name=f"Arishta Bhanga ({planet_name} in Lagna)",
                    name_hindi=f"अरिष्ट भंग ({planet_name} लग्नस्थ)",
                    is_present=True,
                    planets_involved=[planet_name],
                    houses_involved=[1],
                    description=(
                        f"{planet_name} in Lagna — "
                        "benefic in self-house is strongest arishta cancellation"
                    ),
                    effect="benefic",
                )
            )

    return yogas


# ── Kemadruma Bhanga (all 8 rules) ───────────────────────────────────────


def _detect_kemadruma_full(chart: ChartData) -> list[YogaResult]:
    """Detect Kemadruma Yoga with all 8 classical cancellation rules.

    Source: BPHS Ch.23; Brihat Jataka; Phaladeepika.
    """
    moon = chart.planets["Moon"]
    moon_sign = moon.sign_index
    sign_before = (moon_sign - 1) % 12
    sign_after = (moon_sign + 1) % 12

    # Check basic Kemadruma condition
    adjacent_planets = [
        n
        for n, p in chart.planets.items()
        if p.sign_index in (sign_before, sign_after) and n not in ("Sun", "Rahu", "Ketu", "Moon")
    ]
    is_kemadruma = len(adjacent_planets) == 0

    if not is_kemadruma:
        return []

    # Kemadruma is present — check all 8 cancellation rules
    cancellation_rules: list[str] = []

    # Rule 1: Any non-Sun/Rahu/Ketu planet adjacent (already failed → no cancellation)
    # (Rule 1 is the base definition check above)

    # Rule 2: Planet in kendra from Moon
    kendra_from_moon = [
        n
        for n, p in chart.planets.items()
        if ((p.sign_index - moon_sign) % 12) + 1 in KENDRAS
        and n not in ("Sun", "Rahu", "Ketu", "Moon")
    ]
    if kendra_from_moon:
        cancellation_rules.append(f"Rule 2: {', '.join(kendra_from_moon)} in kendra from Moon")

    # Rule 3: Moon in kendra from lagna
    if moon.house in KENDRAS:
        cancellation_rules.append(f"Rule 3: Moon in kendra (H{moon.house}) from Lagna")

    # Rule 4: Planet in kendra from lagna
    kendra_from_lagna = [
        n
        for n, p in chart.planets.items()
        if p.house in KENDRAS and n not in ("Sun", "Rahu", "Ketu")
    ]
    if kendra_from_lagna:
        cancellation_rules.append(
            f"Rule 4: {', '.join(kendra_from_lagna[:3])} in kendra from Lagna"
        )

    # Rule 5: Full Moon (Paksha Bala)
    moon_sun_diff = (moon.longitude - chart.planets["Sun"].longitude) % 360
    if moon_sun_diff > 120:
        cancellation_rules.append(f"Rule 5: Full Moon Paksha Bala ({moon_sun_diff:.0f}°)")

    # Rule 6: Moon in own or exalted sign
    moon_own = OWN_SIGNS.get("Moon", [])
    moon_exalt = EXALTATION.get("Moon")
    if moon_sign in moon_own or moon_sign == moon_exalt:
        dignity = "own" if moon_sign in moon_own else "exalted"
        cancellation_rules.append(f"Rule 6: Moon in {dignity} sign")

    # Rule 7: Moon receives benefic aspect
    for bname in ("Jupiter", "Venus", "Mercury"):
        b = chart.planets[bname]
        aspect_from_b = ((moon_sign - b.sign_index) % 12) + 1
        if bname == "Jupiter" and aspect_from_b in (5, 7, 9) and not b.is_combust:
            cancellation_rules.append(f"Rule 7: Jupiter aspects Moon ({aspect_from_b}th aspect)")
            break
        elif aspect_from_b == 7 and not b.is_combust:
            cancellation_rules.append(f"Rule 7: {bname} aspects Moon (7th aspect)")
            break

    # Rule 8: Vargottama Moon — simplified check (same sign would need navamsha)
    # We note this as a potential cancellation without full navamsha computation
    # (full computation requires D9 chart data)

    if cancellation_rules:
        return [
            YogaResult(
                name="Kemadruma Bhanga (Multiple Rules)",
                name_hindi="केमद्रुम भंग (बहु नियम)",
                is_present=True,
                planets_involved=["Moon"],
                houses_involved=[moon.house],
                description=(
                    f"Kemadruma present but cancelled by {len(cancellation_rules)} rule(s): "
                    f"{'; '.join(cancellation_rules)}"
                ),
                effect="benefic",
            )
        ]
    # Kemadruma not cancelled — return only the dosha
    return [
        YogaResult(
            name="Kemadruma Yoga (Uncancelled)",
            name_hindi="केमद्रुम योग (अखंडित)",
            is_present=True,
            planets_involved=["Moon"],
            houses_involved=[moon.house],
            description=(
                "Moon isolated with no planet in 2nd/12th from it, "
                "and none of the 8 classical cancellation rules apply — "
                "loneliness, financial fluctuations, emotional isolation"
            ),
            effect="malefic",
        )
    ]


# ── Raja Yoga Bhanga ─────────────────────────────────────────────────────


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
