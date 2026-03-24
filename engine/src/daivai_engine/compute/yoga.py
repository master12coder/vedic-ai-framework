"""Yoga detection engine — Panch Mahapurush, Raj, Dhan, and all extended yogas."""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData, get_house_lord
from daivai_engine.compute.yoga_other import detect_other_yogas
from daivai_engine.constants import (
    EXALTATION,
    KENDRAS,
    OWN_SIGNS,
    TRIKONAS,
)
from daivai_engine.models.yoga import YogaResult


def _is_in_kendra(house: int) -> bool:
    """Check if house is a kendra."""
    return house in KENDRAS


def _is_in_own_or_exalted(planet_name: str, sign_index: int) -> bool:
    """Check if planet is in own or exalted sign."""
    if planet_name in EXALTATION and EXALTATION[planet_name] == sign_index:
        return True
    return bool(planet_name in OWN_SIGNS and sign_index in OWN_SIGNS[planet_name])


def detect_all_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect all yogas — Panch Mahapurush, Raj, Dhan, Nabhasa, Parivartana, and more.

    Detection order:
      1. Panch Mahapurush (5 great-person yogas)
      2. Raj Yogas (kendra-trikona lord connections)
      3. Dhan Yogas (wealth yogas)
      4. Other Yogas (Gajakesari, Budhaditya, Vipreet Raj, Neech Bhanga, etc.)
      5. Arishta + Kemadruma + Bandhana (affliction, isolation, bondage)
      6. Conjunction Yogas (11 classical pairs + Sunapha/Anapha)
      7. Daridra Yogas (poverty patterns)
      8. Extended Yogas (Nabhasa, lunar, solar, conjunction doshas, Kartari, etc.)
      9. Parivartana Yogas (all 66 house-pair mutual exchanges)
      10. Special Yogas (Chatussagara, Mahabhagya)
      11. Strength post-processing (combustion, Vargottama, retrograde modifiers)

    Source: BPHS, Phaladeepika, Saravali.

    Args:
        chart: Computed birth chart.

    Returns:
        List of all detected YogaResults with strength fields set.
    """
    from daivai_engine.compute.yoga_arishta import detect_arishta_yogas
    from daivai_engine.compute.yoga_conjunctions import (
        detect_conjunction_yogas,
        detect_sunapha_anapha_specific,
    )
    from daivai_engine.compute.yoga_daridra import detect_daridra_extended
    from daivai_engine.compute.yoga_extended import detect_extended_yogas
    from daivai_engine.compute.yoga_parivartana import (
        apply_yoga_strength,
        detect_parivartana_yogas,
    )
    from daivai_engine.compute.yoga_special import detect_special_yogas

    yogas: list[YogaResult] = []
    yogas.extend(_detect_panch_mahapurush(chart))
    yogas.extend(_detect_raj_yogas(chart))
    yogas.extend(_detect_dhan_yogas(chart))
    yogas.extend(detect_other_yogas(chart))
    yogas.extend(detect_arishta_yogas(chart))
    yogas.extend(detect_conjunction_yogas(chart))
    yogas.extend(detect_sunapha_anapha_specific(chart))
    yogas.extend(detect_daridra_extended(chart))
    yogas.extend(detect_extended_yogas(chart))
    yogas.extend(detect_parivartana_yogas(chart))
    yogas.extend(detect_special_yogas(chart))

    # Apply combustion / Vargottama / retrograde strength modifiers
    return apply_yoga_strength(yogas, chart)


def _detect_panch_mahapurush(chart: ChartData) -> list[YogaResult]:
    """Detect the 5 Panch Mahapurush Yogas."""
    yogas = []

    checks = [
        (
            "Jupiter",
            "Hamsa",
            "हंस योग",
            "Jupiter in own/exalted sign in kendra — wisdom, spirituality, fame",
        ),
        (
            "Venus",
            "Malavya",
            "मालव्य योग",
            "Venus in own/exalted sign in kendra — luxury, beauty, artistic talent",
        ),
        (
            "Saturn",
            "Sasa",
            "शश योग",
            "Saturn in own/exalted sign in kendra — authority, discipline, power",
        ),
        (
            "Mars",
            "Ruchaka",
            "रुचक योग",
            "Mars in own/exalted sign in kendra — courage, leadership, military success",
        ),
        (
            "Mercury",
            "Bhadra",
            "भद्र योग",
            "Mercury in own/exalted sign in kendra — intelligence, eloquence, commerce",
        ),
    ]

    for planet, name, name_hi, desc in checks:
        p = chart.planets[planet]
        if _is_in_kendra(p.house) and _is_in_own_or_exalted(planet, p.sign_index):
            yogas.append(
                YogaResult(
                    name=name,
                    name_hindi=name_hi,
                    is_present=True,
                    planets_involved=[planet],
                    houses_involved=[p.house],
                    description=desc,
                    effect="benefic",
                )
            )

    return yogas


def _detect_raj_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect Raj Yogas — kendra lord + trikona lord connections."""
    yogas = []

    # Get lords of kendras and trikonas
    kendra_lords = set()
    trikona_lords = set()
    for h in KENDRAS:
        kendra_lords.add(get_house_lord(chart, h))
    for h in TRIKONAS:
        trikona_lords.add(get_house_lord(chart, h))

    # Planets that own both kendra and trikona (yogakaraka)
    yogakaraka_planets = kendra_lords & trikona_lords
    # Remove Lagna lord from kendra-trikona overlap check as it's always both
    # but we still want to report it
    for yk in yogakaraka_planets:
        p = chart.planets.get(yk)
        if p and (p.dignity in ("exalted", "own", "mooltrikona") or _is_in_kendra(p.house)):
            yogas.append(
                YogaResult(
                    name="Yogakaraka Raj Yoga",
                    name_hindi="योगकारक राज योग",
                    is_present=True,
                    planets_involved=[yk],
                    houses_involved=[p.house],
                    description=f"{yk} owns both kendra and trikona — powerful raj yoga",
                    effect="benefic",
                )
            )

    # Conjunction of kendra lord + trikona lord
    kendra_only = kendra_lords - trikona_lords
    trikona_only = trikona_lords - kendra_lords
    for kl in kendra_only:
        for tl in trikona_only:
            kp = chart.planets.get(kl)
            tp = chart.planets.get(tl)
            if kp and tp and kp.sign_index == tp.sign_index:
                yogas.append(
                    YogaResult(
                        name="Raj Yoga",
                        name_hindi="राज योग",
                        is_present=True,
                        planets_involved=[kl, tl],
                        houses_involved=[kp.house],
                        description=f"Kendra lord {kl} conjunct trikona lord {tl}",
                        effect="benefic",
                    )
                )

    # 9th lord + 10th lord conjunction
    lord_9 = get_house_lord(chart, 9)
    lord_10 = get_house_lord(chart, 10)
    if lord_9 != lord_10:
        p9 = chart.planets.get(lord_9)
        p10 = chart.planets.get(lord_10)
        if p9 and p10 and p9.sign_index == p10.sign_index:
            yogas.append(
                YogaResult(
                    name="Dharma Karmadhipati Yoga",
                    name_hindi="धर्म कर्माधिपति योग",
                    is_present=True,
                    planets_involved=[lord_9, lord_10],
                    houses_involved=[9, 10, p9.house],
                    description=f"9th lord ({lord_9}) conjunct 10th lord ({lord_10}) — fortune meets action",
                    effect="benefic",
                )
            )

    return yogas


def _detect_dhan_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect wealth yogas."""
    yogas = []

    # 2nd lord + 11th lord conjunction
    lord_2 = get_house_lord(chart, 2)
    lord_11 = get_house_lord(chart, 11)
    if lord_2 != lord_11:
        p2 = chart.planets.get(lord_2)
        p11 = chart.planets.get(lord_11)
        if p2 and p11 and p2.sign_index == p11.sign_index:
            yogas.append(
                YogaResult(
                    name="Dhan Yoga (2-11)",
                    name_hindi="धन योग",
                    is_present=True,
                    planets_involved=[lord_2, lord_11],
                    houses_involved=[2, 11],
                    description=f"2nd lord ({lord_2}) conjunct 11th lord ({lord_11}) — wealth accumulation",
                    effect="benefic",
                )
            )

    # 5th lord + 9th lord conjunction
    lord_5 = get_house_lord(chart, 5)
    lord_9 = get_house_lord(chart, 9)
    if lord_5 != lord_9:
        p5 = chart.planets.get(lord_5)
        p9 = chart.planets.get(lord_9)
        if p5 and p9 and p5.sign_index == p9.sign_index:
            yogas.append(
                YogaResult(
                    name="Dhan Yoga (5-9)",
                    name_hindi="धन योग (५-९)",
                    is_present=True,
                    planets_involved=[lord_5, lord_9],
                    houses_involved=[5, 9],
                    description=f"5th lord ({lord_5}) conjunct 9th lord ({lord_9}) — purva punya wealth",
                    effect="benefic",
                )
            )

    # Jupiter in 2nd or 11th in good dignity
    jup = chart.planets["Jupiter"]
    if jup.house in (2, 11) and jup.dignity in ("exalted", "own", "mooltrikona"):
        yogas.append(
            YogaResult(
                name="Dhan Yoga (Jupiter)",
                name_hindi="धन योग (बृहस्पति)",
                is_present=True,
                planets_involved=["Jupiter"],
                houses_involved=[jup.house],
                description=f"Jupiter in {jup.house}th house in {jup.dignity} dignity — natural wealth indicator",
                effect="benefic",
            )
        )

    return yogas
