"""Tajaka yoga pair-level detection logic for the 16 Varshphal yogas.

Contains the _check_pair function which evaluates all aspect-based Tajaka yoga
conditions for a given fast-slow planet pair. Called by detect_all_tajaka_yogas
in tajaka_yogas.py.

Sources: Tajaka Neelakanthi (Nilakantha), Dr. B.V. Raman's "Varshphal".
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from daivai_engine.compute.tajaka_helpers import (
    _TAJAKA_ORB,
    _compute_tajaka_aspect,
    _find_blocking_planet,
    _is_mutual_reception,
)


if TYPE_CHECKING:
    from daivai_engine.models.chart import ChartData, PlanetData


def _check_pair(
    fast_name: str,
    fast: PlanetData,
    slow_name: str,
    slow: PlanetData,
    chart: ChartData,
    yoga_cls: type,
) -> list:
    """Check all yoga conditions for a single fast-slow planet pair."""
    results: list = []

    aspect = _compute_tajaka_aspect(fast, slow)
    if aspect is None:
        from daivai_engine.compute.tajaka_yoga_checks import check_no_aspect_yogas

        results += check_no_aspect_yogas(fast_name, fast, slow_name, slow, yoga_cls)
        return results

    aspect_type, orb, is_applying = aspect

    # 1. Ithasala — applying aspect (the primary good yoga)
    if is_applying and not fast.is_combust and fast.dignity != "debilitated":
        results.append(
            yoga_cls(
                name="Ithasala",
                name_hi="\u0907\u0924\u094d\u0925\u0936\u093e\u0932",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=True,
                is_positive=True,
                description=(
                    f"{fast_name} applying {aspect_type} to {slow_name} "
                    f"(orb {orb:.1f}\u00b0) \u2014 significations will be fulfilled."
                ),
            )
        )

    # 2. Ishrafa — separating aspect (missed opportunity)
    if not is_applying and orb <= _TAJAKA_ORB:
        results.append(
            yoga_cls(
                name="Ishrafa",
                name_hi="\u0907\u0936\u0930\u093e\u092b",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=False,
                is_positive=False,
                description=(
                    f"{fast_name} separating from {aspect_type} to {slow_name} "
                    f"(orb {orb:.1f}\u00b0) \u2014 matter was initiated but may not complete."
                ),
            )
        )

    # 3. Ikkabal — fast planet has greater degrees in sign (applying but vigorous)
    if is_applying and fast.degree_in_sign > slow.degree_in_sign:
        results.append(
            yoga_cls(
                name="Ikkabal",
                name_hi="\u0907\u0915\u092c\u093e\u0932",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=True,
                is_positive=True,
                description=(
                    f"{fast_name} in Ikkabal with {slow_name} \u2014 "
                    "vigorous application, matter comes to fruition quickly."
                ),
            )
        )

    # 4. Induvara — exact or near-exact aspect (both same degree)
    if orb <= 1.0:
        results.append(
            yoga_cls(
                name="Induvara",
                name_hi="\u0907\u0928\u094d\u0926\u0941\u0935\u0930",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=is_applying,
                is_positive=True,
                description=(
                    f"{fast_name} and {slow_name} at near-exact {aspect_type} "
                    f"(orb {orb:.2f}\u00b0) \u2014 Induvara: extremely powerful indication."
                ),
            )
        )

    # 5. Nakta — Moon transfers light between fast and slow
    from daivai_engine.compute.tajaka_helpers import _check_nakta

    moon = chart.planets.get("Moon")
    if moon and fast_name != "Moon" and slow_name != "Moon":
        nakta_data = _check_nakta(fast_name, fast, slow_name, slow, moon)
        if nakta_data:
            results.append(yoga_cls(**nakta_data))

    # 6. Yamaya — mutual reception (in each other's sign) with aspect
    if _is_mutual_reception(fast_name, fast, slow_name, slow):
        results.append(
            yoga_cls(
                name="Yamaya",
                name_hi="\u092f\u092e\u093e\u092f",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=is_applying,
                is_positive=True,
                description=(
                    f"{fast_name} and {slow_name} in mutual reception "
                    f"with {aspect_type} \u2014 Yamaya: strong promise of results."
                ),
            )
        )

    # 7. Drippha — fast planet combust, still applying
    if is_applying and fast.is_combust:
        results.append(
            yoga_cls(
                name="Drippha",
                name_hi="\u0926\u094d\u0930\u093f\u092a\u094d\u092b\u093e",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=True,
                is_positive=False,
                description=(
                    f"{fast_name} combust but applying to {slow_name} \u2014 "
                    "Drippha: matter may begin but weakens before completion."
                ),
            )
        )

    # 8. Kuttha — fast planet debilitated, applying
    if is_applying and fast.dignity == "debilitated":
        results.append(
            yoga_cls(
                name="Kuttha",
                name_hi="\u0915\u0941\u0924\u094d\u0925\u093e",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=True,
                is_positive=False,
                description=(
                    f"{fast_name} debilitated, applying to {slow_name} \u2014 "
                    "Kuttha: degraded application; results come with humiliation or loss."
                ),
            )
        )

    # 9. Tambira — fast planet in inimical sign, applying
    if is_applying and fast.dignity in ("enemy",) and not fast.is_combust:
        results.append(
            yoga_cls(
                name="Tambira",
                name_hi="\u0924\u092e\u094d\u092c\u0940\u0930",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=True,
                is_positive=False,
                description=(
                    f"{fast_name} in enemy sign, applying to {slow_name} \u2014 "
                    "Tambira: application happens under hostile conditions."
                ),
            )
        )

    # 10. Durupha — both planets in adverse dignity (debilitated or combust)
    slow_adverse = slow.dignity == "debilitated" or (slow.is_combust and slow_name != "Sun")
    fast_adverse = fast.dignity == "debilitated" or fast.is_combust
    if fast_adverse and slow_adverse and is_applying:
        results.append(
            yoga_cls(
                name="Durupha",
                name_hi="\u0926\u0941\u0930\u0941\u092b\u093e",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=True,
                is_positive=False,
                description=(
                    f"Both {fast_name} and {slow_name} in adverse condition \u2014 "
                    "Durupha: matter will not fructify; double obstruction."
                ),
            )
        )

    # 11. Radda — frustration (another planet blocks between fast and slow)
    if is_applying:
        blocker = _find_blocking_planet(fast_name, fast, slow_name, slow, chart)
        if blocker:
            results.append(
                yoga_cls(
                    name="Radda",
                    name_hi="\u0930\u0926\u094d\u0926\u093e",
                    fast_planet=fast_name,
                    slow_planet=slow_name,
                    aspect_type=aspect_type,
                    orb=orb,
                    is_applying=True,
                    is_positive=False,
                    description=(
                        f"{fast_name} applying to {slow_name} but blocked by {blocker} \u2014 "
                        "Radda: application is frustrated; matter interrupted."
                    ),
                )
            )

    # 16. Musaripha — fast planet separating from slow while applying to another
    if not is_applying:
        from daivai_engine.compute.tajaka_yoga_checks import check_musaripha

        musaripha = check_musaripha(fast_name, fast, slow_name, slow, chart, yoga_cls)
        if musaripha:
            results.append(musaripha)  # type: ignore[arg-type]

    return results
