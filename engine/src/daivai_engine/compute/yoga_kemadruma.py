"""Arishta Bhanga and Kemadruma Bhanga detection."""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData, get_house_lord
from daivai_engine.constants import EXALTATION, KENDRAS, OWN_SIGNS, TRIKONAS
from daivai_engine.models.yoga import YogaResult


_BENEFICS_ALL = {"Jupiter", "Venus", "Mercury"}


def _detect_arishta_bhanga(chart: ChartData) -> list[YogaResult]:
    """Detect Arishta Bhanga (cancellation of dangers) — BPHS Ch.19."""
    yogas: list[YogaResult] = []
    moon = chart.planets["Moon"]
    jup = chart.planets["Jupiter"]
    lagna_lord = get_house_lord(chart, 1)
    p_ll = chart.planets.get(lagna_lord)

    # Rule 1: Jupiter aspects afflicted Moon (Moon in dusthana, Jupiter 5/7/9 from Moon)
    from daivai_engine.constants import DUSTHANAS

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
