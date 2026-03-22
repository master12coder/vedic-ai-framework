"""Extended yoga detection — lunar, solar, and Neech Bhanga yogas.

Covers: Sunapha, Anapha, Durudhura, Shakata, Amala, Adhi (Moon),
Veshi, Voshi, Ubhayachari (Sun), Neech Bhanga Raj Yoga.

Source: BPHS, Phaladeepika Ch.7-8.
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


_BENEFICS = {"Jupiter", "Venus"}
_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}


# ── Lunar Yogas (from Moon) ──────────────────────────────────────────────


def detect_lunar_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect yogas based on Moon's position — Phaladeepika Ch.7."""
    yogas: list[YogaResult] = []
    moon = chart.planets["Moon"]
    moon_sign = moon.sign_index

    # Planets in 2nd and 12th from Moon
    sign_2nd = (moon_sign + 1) % 12
    sign_12th = (moon_sign - 1) % 12
    in_2nd = [
        n
        for n, p in chart.planets.items()
        if p.sign_index == sign_2nd and n not in ("Rahu", "Ketu", "Moon")
    ]
    in_12th = [
        n
        for n, p in chart.planets.items()
        if p.sign_index == sign_12th and n not in ("Rahu", "Ketu", "Moon")
    ]

    # Sunapha: planet in 2nd from Moon (not Sun) — Phaladeepika 7.1
    sunapha_planets = [p for p in in_2nd if p != "Sun"]
    if sunapha_planets:
        yogas.append(
            YogaResult(
                name="Sunapha Yoga",
                name_hindi="सुनफा योग",
                is_present=True,
                planets_involved=sunapha_planets,
                houses_involved=[],
                description=f"{', '.join(sunapha_planets)} in 2nd from Moon — self-made wealth, good reputation",
                effect="benefic",
            )
        )

    # Anapha: planet in 12th from Moon (not Sun) — Phaladeepika 7.2
    anapha_planets = [p for p in in_12th if p != "Sun"]
    if anapha_planets:
        yogas.append(
            YogaResult(
                name="Anapha Yoga",
                name_hindi="अनफा योग",
                is_present=True,
                planets_involved=anapha_planets,
                houses_involved=[],
                description=f"{', '.join(anapha_planets)} in 12th from Moon — generous, expressive personality",
                effect="benefic",
            )
        )

    # Durudhura: planets in BOTH 2nd and 12th from Moon — Phaladeepika 7.3
    if sunapha_planets and anapha_planets:
        yogas.append(
            YogaResult(
                name="Durudhura Yoga",
                name_hindi="दुरुधुरा योग",
                is_present=True,
                planets_involved=sunapha_planets + anapha_planets,
                houses_involved=[],
                description="Planets on both sides of Moon — wealth, vehicles, fame, generous nature",
                effect="benefic",
            )
        )

    # Shakata: Jupiter in 6/8/12 from Moon — Phaladeepika 7.12
    jup = chart.planets["Jupiter"]
    jup_from_moon = ((jup.sign_index - moon_sign) % 12) + 1
    if jup_from_moon in (6, 8, 12):
        yogas.append(
            YogaResult(
                name="Shakata Yoga",
                name_hindi="शकट योग",
                is_present=True,
                planets_involved=["Jupiter", "Moon"],
                houses_involved=[jup_from_moon],
                description=f"Jupiter in {jup_from_moon}th from Moon — ups and downs in fortune, unstable wealth",
                effect="malefic",
            )
        )

    # Amala: natural benefic in 10th from Moon or Lagna — Phaladeepika 7.14
    sign_10_from_moon = (moon_sign + 9) % 12
    sign_10_from_lagna = (chart.lagna_sign_index + 9) % 12

    moon_sun_diff = (chart.planets["Moon"].longitude - chart.planets["Sun"].longitude) % 360
    is_waxing_moon = moon_sun_diff < 180

    amala_candidates: list[tuple[str, bool]] = [
        ("Jupiter", True),
        ("Venus", True),
        ("Mercury", not chart.planets["Mercury"].is_combust),
        ("Moon", is_waxing_moon),
    ]
    for amala_planet, qualifies in amala_candidates:
        if not qualifies:
            continue
        p = chart.planets.get(amala_planet)
        if p and p.sign_index in (sign_10_from_moon, sign_10_from_lagna):
            ref = "10th from Moon" if p.sign_index == sign_10_from_moon else "10th from Lagna"
            yogas.append(
                YogaResult(
                    name="Amala Yoga",
                    name_hindi="अमल योग",
                    is_present=True,
                    planets_involved=[amala_planet],
                    houses_involved=[10],
                    description=(
                        f"{amala_planet} in {ref} — spotless reputation, "
                        "ethical conduct, fame through good deeds"
                    ),
                    effect="benefic",
                )
            )
            break  # One Amala per chart is sufficient

    # Adhi Yoga: Jupiter, Venus, Mercury in 6th/7th/8th from Moon — BPHS
    adhi_signs = frozenset([(moon_sign + i) % 12 for i in (5, 6, 7)])
    adhi_planets = [
        n for n in ("Jupiter", "Venus", "Mercury") if chart.planets[n].sign_index in adhi_signs
    ]
    if adhi_planets:
        count = len(adhi_planets)
        if count >= 3:
            grade = "Purna"
            adhi_desc = (
                "All 3 benefics (Jupiter, Venus, Mercury) in 6/7/8 from Moon — "
                "minister-level authority, great prosperity, enduring leadership"
            )
            adhi_strength = "full"
        elif count == 2:
            grade = "Madhya"
            adhi_desc = (
                f"{' & '.join(adhi_planets)} in 6/7/8 from Moon — "
                "leadership role, wealth, comfortable authority"
            )
            adhi_strength = "full"
        else:
            grade = "Hina"
            adhi_desc = (
                f"{adhi_planets[0]} in 6/7/8 from Moon — "
                "modest authority, minor gains through position"
            )
            adhi_strength = "partial"
        yogas.append(
            YogaResult(
                name="Adhi Yoga",
                name_hindi="अधि योग",
                is_present=True,
                planets_involved=adhi_planets,
                houses_involved=[6, 7, 8],
                description=f"{grade}: {adhi_desc}",
                effect="benefic",
                strength=adhi_strength,
            )
        )

    return yogas


# ── Solar Yogas ──────────────────────────────────────────────────────────


def detect_solar_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect yogas based on Sun's position — Phaladeepika Ch.8."""
    yogas: list[YogaResult] = []
    sun = chart.planets["Sun"]
    sun_sign = sun.sign_index

    # Veshi: planet (not Moon) in 2nd from Sun — Phaladeepika 8.1
    sign_2nd = (sun_sign + 1) % 12
    veshi = [
        n
        for n, p in chart.planets.items()
        if p.sign_index == sign_2nd and n not in ("Moon", "Rahu", "Ketu", "Sun")
    ]
    if veshi:
        yogas.append(
            YogaResult(
                name="Veshi Yoga",
                name_hindi="वेशी योग",
                is_present=True,
                planets_involved=veshi,
                houses_involved=[],
                description=f"{', '.join(veshi)} in 2nd from Sun — eloquent, learned, wealthy",
                effect="benefic" if any(v in _BENEFICS for v in veshi) else "mixed",
            )
        )

    # Voshi: planet (not Moon) in 12th from Sun — Phaladeepika 8.2
    sign_12th = (sun_sign - 1) % 12
    voshi = [
        n
        for n, p in chart.planets.items()
        if p.sign_index == sign_12th and n not in ("Moon", "Rahu", "Ketu", "Sun")
    ]
    if voshi:
        yogas.append(
            YogaResult(
                name="Voshi Yoga",
                name_hindi="वोशी योग",
                is_present=True,
                planets_involved=voshi,
                houses_involved=[],
                description=f"{', '.join(voshi)} in 12th from Sun — charitable, skilled, influential",
                effect="benefic" if any(v in _BENEFICS for v in voshi) else "mixed",
            )
        )

    # Ubhayachari: planets on BOTH sides of Sun — Phaladeepika 8.3
    if veshi and voshi:
        yogas.append(
            YogaResult(
                name="Ubhayachari Yoga",
                name_hindi="उभयचरी योग",
                is_present=True,
                planets_involved=veshi + voshi,
                houses_involved=[],
                description="Planets flanking Sun — kingly status, balanced personality, eloquent",
                effect="benefic",
            )
        )

    return yogas


# ── Neech Bhanga Raj Yoga ────────────────────────────────────────────────


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
