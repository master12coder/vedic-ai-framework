"""All 16 Tajaka Yogas for Varshphal (Annual Chart) analysis.

Tajaka is the Perso-Arabic annual astrology system integrated into Vedic
jyotish. The 16 yogas describe planetary relationship states in the annual
chart and determine whether significations will be fulfilled, delayed,
blocked, or transferred in the year.

Aspects used in Tajaka (sign-based, bidirectional):
  Conjunction (0°): same sign
  Sextile   (60°): 3 signs apart
  Square    (90°): 4 signs apart
  Trine    (120°): 5 signs apart
  Opposition(180°): 7 signs apart

Orb: 5° from exact aspect degree (standard Tajaka orb).
"Applying" = fast planet approaching aspect with slow planet.
"Separating" = fast planet moving away from aspect with slow planet.

Sources: Tajaka Neelakanthi (Nilakantha), Dr. B.V. Raman's "Varshphal",
         Jahangir's Tajaka Manual, Komilla Sutton commentary.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from daivai_engine.models.chart import ChartData, PlanetData


# Aspect distances in signs for Tajaka (sign-to-sign counting, 1-based)
_TAJAKA_ASPECT_SIGNS: set[int] = {1, 3, 4, 5, 7}  # conj, sextile, sq, trine, opp

# Orb in degrees for Tajaka aspects
_TAJAKA_ORB: float = 5.0

# Planets ordered slowest to fastest (for fast/slow determination)
_SPEED_ORDER = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]

# Malefics for Drippha / adverse condition checks
_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}


class TajakaYoga(BaseModel):
    """A single detected Tajaka yoga between two planets in an annual chart."""

    model_config = ConfigDict(frozen=True)

    name: str  # Yoga name (e.g., "Ithasala")
    name_hi: str  # Hindi/Sanskrit name
    fast_planet: str  # Faster-moving planet
    slow_planet: str  # Slower-moving planet
    aspect_type: str  # conjunction/sextile/square/trine/opposition
    orb: float = Field(ge=0)  # Degrees from exact aspect
    is_applying: bool  # True=applying (fast→slow), False=separating
    is_positive: bool  # Generally favorable yoga or not
    description: str  # Brief interpretation


def detect_all_tajaka_yogas(chart: ChartData) -> list[TajakaYoga]:
    """Detect all 16 Tajaka yogas in the given chart (annual or natal).

    Iterates over all planet pairs and checks each of the 16 yoga conditions.
    Multiple yogas can fire for the same pair. Results are sorted with
    positive yogas first.

    Args:
        chart: Annual chart (Varshphal) or natal chart.

    Returns:
        List of detected TajakaYoga, sorted positive-first.
    """
    planets = {n: p for n, p in chart.planets.items() if n not in ("Rahu", "Ketu")}
    planet_list = list(planets.items())

    yogas: list[TajakaYoga] = []
    for i, (n1, p1) in enumerate(planet_list):
        for j, (n2, p2) in enumerate(planet_list):
            if i >= j:
                continue
            # Determine fast/slow
            fast, slow, fp, sp = _fast_slow(n1, p1, n2, p2)
            if fast is None or slow is None or fp is None or sp is None:
                continue

            pair_yogas = _check_pair(fast, fp, slow, sp, chart)
            yogas.extend(pair_yogas)

    # Also check Moon-specific yogas (Kamboola, Gairi-Kamboola)
    _check_moon_yogas(chart, yogas)

    yogas.sort(key=lambda y: (not y.is_positive, y.orb))
    return yogas


def _check_pair(
    fast_name: str,
    fast: PlanetData,
    slow_name: str,
    slow: PlanetData,
    chart: ChartData,
) -> list[TajakaYoga]:
    """Check all yoga conditions for a single fast-slow planet pair."""
    results: list[TajakaYoga] = []

    aspect = _compute_tajaka_aspect(fast, slow)
    if aspect is None:
        # Planets not in aspect — check for Manaou/Khallasara
        results += _check_no_aspect_yogas(fast_name, fast, slow_name, slow)
        return results

    aspect_type, orb, is_applying = aspect

    # 1. Ithasala — applying aspect (the primary good yoga)
    if is_applying and not fast.is_combust and fast.dignity != "debilitated":
        results.append(
            TajakaYoga(
                name="Ithasala",
                name_hi="इत्थशाल",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=True,
                is_positive=True,
                description=(
                    f"{fast_name} applying {aspect_type} to {slow_name} "
                    f"(orb {orb:.1f}°) — significations will be fulfilled."
                ),
            )
        )

    # 2. Ishrafa — separating aspect (missed opportunity)
    if not is_applying and orb <= _TAJAKA_ORB:
        results.append(
            TajakaYoga(
                name="Ishrafa",
                name_hi="इशराफ",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=False,
                is_positive=False,
                description=(
                    f"{fast_name} separating from {aspect_type} to {slow_name} "
                    f"(orb {orb:.1f}°) — matter was initiated but may not complete."
                ),
            )
        )

    # 3. Ikkabal — fast planet has greater degrees in sign (applying but faster)
    if is_applying and fast.degree_in_sign < slow.degree_in_sign:
        results.append(
            TajakaYoga(
                name="Ikkabal",
                name_hi="इकबाल",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=True,
                is_positive=True,
                description=(
                    f"{fast_name} in Ikkabal with {slow_name} — "
                    "vigorous application, matter comes to fruition quickly."
                ),
            )
        )

    # 4. Induvara — exact or near-exact aspect (both same degree)
    if orb <= 1.0:
        results.append(
            TajakaYoga(
                name="Induvara",
                name_hi="इन्दुवर",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=is_applying,
                is_positive=True,
                description=(
                    f"{fast_name} and {slow_name} at near-exact {aspect_type} "
                    f"(orb {orb:.2f}°) — Induvara: extremely powerful indication."
                ),
            )
        )

    # 5. Nakta — Moon transfers light between fast and slow
    moon = chart.planets.get("Moon")
    if moon and fast_name != "Moon" and slow_name != "Moon":
        nakta = _check_nakta(fast_name, fast, slow_name, slow, moon)
        if nakta:
            results.append(nakta)

    # 6. Yamaya — mutual reception (in each other's sign) with aspect
    if _is_mutual_reception(fast_name, fast, slow_name, slow):
        results.append(
            TajakaYoga(
                name="Yamaya",
                name_hi="यमाय",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=is_applying,
                is_positive=True,
                description=(
                    f"{fast_name} and {slow_name} in mutual reception "
                    f"with {aspect_type} — Yamaya: strong promise of results."
                ),
            )
        )

    # 7. Drippha — fast planet combust, still applying
    if is_applying and fast.is_combust:
        results.append(
            TajakaYoga(
                name="Drippha",
                name_hi="द्रिप्फा",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=True,
                is_positive=False,
                description=(
                    f"{fast_name} combust but applying to {slow_name} — "
                    "Drippha: matter may begin but weakens before completion."
                ),
            )
        )

    # 8. Kuttha — fast planet debilitated, applying
    if is_applying and fast.dignity == "debilitated":
        results.append(
            TajakaYoga(
                name="Kuttha",
                name_hi="कुत्था",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=True,
                is_positive=False,
                description=(
                    f"{fast_name} debilitated, applying to {slow_name} — "
                    "Kuttha: degraded application; results come with humiliation or loss."
                ),
            )
        )

    # 9. Tambira — fast planet in inimical sign, applying
    if is_applying and fast.dignity in ("enemy",) and not fast.is_combust:
        results.append(
            TajakaYoga(
                name="Tambira",
                name_hi="तम्बीर",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=True,
                is_positive=False,
                description=(
                    f"{fast_name} in enemy sign, applying to {slow_name} — "
                    "Tambira: application happens under hostile conditions."
                ),
            )
        )

    # 10. Durupha — both planets in adverse dignity (debilitated or combust)
    slow_adverse = slow.dignity == "debilitated" or (slow.is_combust and slow_name != "Sun")
    fast_adverse = fast.dignity == "debilitated" or fast.is_combust
    if fast_adverse and slow_adverse and is_applying:
        results.append(
            TajakaYoga(
                name="Durupha",
                name_hi="दुरुफा",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type=aspect_type,
                orb=orb,
                is_applying=True,
                is_positive=False,
                description=(
                    f"Both {fast_name} and {slow_name} in adverse condition — "
                    "Durupha: matter will not fructify; double obstruction."
                ),
            )
        )

    # 11. Radda — frustration (another planet blocks between fast and slow)
    if is_applying:
        blocker = _find_blocking_planet(fast_name, fast, slow_name, slow, chart)
        if blocker:
            results.append(
                TajakaYoga(
                    name="Radda",
                    name_hi="रद्दा",
                    fast_planet=fast_name,
                    slow_planet=slow_name,
                    aspect_type=aspect_type,
                    orb=orb,
                    is_applying=True,
                    is_positive=False,
                    description=(
                        f"{fast_name} applying to {slow_name} but blocked by {blocker} — "
                        "Radda: application is frustrated; matter interrupted."
                    ),
                )
            )

    # 16. Musaripha — fast planet separating from slow while applying to another
    if not is_applying:
        musaripha = _check_musaripha(fast_name, fast, slow_name, slow, chart)
        if musaripha:
            results.append(musaripha)

    return results


def _check_no_aspect_yogas(
    fast_name: str,
    fast: PlanetData,
    slow_name: str,
    slow: PlanetData,
) -> list[TajakaYoga]:
    """Check yogas that occur when no aspect exists between the pair."""
    results: list[TajakaYoga] = []

    # 12. Manaou — no aspect connection (matter signified cannot manifest)
    results.append(
        TajakaYoga(
            name="Manaou",
            name_hi="मनाउ",
            fast_planet=fast_name,
            slow_planet=slow_name,
            aspect_type="none",
            orb=0.0,
            is_applying=False,
            is_positive=False,
            description=(
                f"{fast_name} and {slow_name} have no Tajaka aspect — "
                "Manaou: no connection; matters signified will not manifest."
            ),
        )
    )

    # 13. Khallasara — fast planet past slow with no new aspect forming
    if fast.degree_in_sign > slow.degree_in_sign and fast.speed > slow.speed:
        results.append(
            TajakaYoga(
                name="Khallasara",
                name_hi="खल्लासार",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type="none",
                orb=0.0,
                is_applying=False,
                is_positive=False,
                description=(
                    f"{fast_name} has overtaken {slow_name} with no aspect — "
                    "Khallasara: opportunity passed; no new application forming."
                ),
            )
        )

    return results


def _check_moon_yogas(chart: ChartData, yogas: list[TajakaYoga]) -> None:
    """Check Kamboola and Gairi-Kamboola (Moon-specific yogas)."""
    moon = chart.planets.get("Moon")
    if not moon:
        return

    for name, planet in chart.planets.items():
        if name == "Moon":
            continue
        aspect = _compute_tajaka_aspect(moon, planet)
        if aspect is None:
            continue
        aspect_type, orb, is_applying = aspect

        # 14. Kamboola — Moon applying to another planet (Moon = fast planet)
        if is_applying:
            yogas.append(
                TajakaYoga(
                    name="Kamboola",
                    name_hi="कम्बूल",
                    fast_planet="Moon",
                    slow_planet=name,
                    aspect_type=aspect_type,
                    orb=orb,
                    is_applying=True,
                    is_positive=True,
                    description=(
                        f"Moon applying {aspect_type} to {name} "
                        f"(orb {orb:.1f}°) — Kamboola: Moon empowers the application; "
                        "swift results through emotional/mental alignment."
                    ),
                )
            )

        # 15. Gairi-Kamboola — Moon separating from another planet
        if not is_applying and orb <= _TAJAKA_ORB:
            yogas.append(
                TajakaYoga(
                    name="Gairi-Kamboola",
                    name_hi="गैरी-कम्बूल",
                    fast_planet="Moon",
                    slow_planet=name,
                    aspect_type=aspect_type,
                    orb=orb,
                    is_applying=False,
                    is_positive=False,
                    description=(
                        f"Moon separating from {aspect_type} to {name} — "
                        "Gairi-Kamboola: matter initiated through Moon has passed its peak."
                    ),
                )
            )


def _check_musaripha(
    fast_name: str,
    fast: PlanetData,
    slow_name: str,
    slow: PlanetData,
    chart: ChartData,
) -> TajakaYoga | None:
    """16. Musaripha — fast planet separating from one and applying to another."""
    # Check if fast planet has Ishrafa with slow_name AND Ithasala with any other planet
    for other_name, other in chart.planets.items():
        if other_name in (fast_name, slow_name):
            continue
        other_asp = _compute_tajaka_aspect(fast, other)
        if other_asp and other_asp[2]:  # applying to another
            return TajakaYoga(
                name="Musaripha",
                name_hi="मुसारिफा",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type="transfer",
                orb=0.0,
                is_applying=False,
                is_positive=False,
                description=(
                    f"{fast_name} separating from {slow_name} and applying to {other_name} — "
                    "Musaripha: energy transfers from old matter to new."
                ),
            )
    return None


# ── Aspect computation ────────────────────────────────────────────────────


def _compute_tajaka_aspect(
    p1: PlanetData,
    p2: PlanetData,
) -> tuple[str, float, bool] | None:
    """Compute Tajaka aspect between two planets.

    Returns (aspect_type, orb_degrees, is_applying) or None if no aspect.
    is_applying = True if p1 is moving toward exact aspect with p2.
    """
    sign_diff = abs(p1.sign_index - p2.sign_index)
    if sign_diff > 6:
        sign_diff = 12 - sign_diff

    aspect_map = {0: "conjunction", 2: "sextile", 3: "square", 4: "trine", 6: "opposition"}
    if sign_diff not in aspect_map:
        return None

    aspect_type = aspect_map[sign_diff]

    # Compute degree-level orb
    lon_diff = p1.longitude - p2.longitude
    # Normalize to -180..+180
    while lon_diff > 180:
        lon_diff -= 360
    while lon_diff < -180:
        lon_diff += 360

    exact_diffs = {
        "conjunction": 0.0,
        "sextile": 60.0,
        "square": 90.0,
        "trine": 120.0,
        "opposition": 180.0,
    }
    exact = exact_diffs[aspect_type]
    # Check both directions of the aspect
    orb = min(abs(abs(lon_diff) - exact), abs(360 - abs(lon_diff) - exact))

    if orb > _TAJAKA_ORB:
        return None

    # Applying: p1 moving toward exact aspect with p2
    # For conjunction: p1.lon < p2.lon and p1.speed > 0 (moving toward p2)
    is_applying = _is_applying(p1, p2, aspect_type, lon_diff)

    return aspect_type, round(orb, 2), is_applying


def _is_applying(
    p1: PlanetData,
    p2: PlanetData,
    aspect_type: str,
    lon_diff: float,
) -> bool:
    """Determine if p1 is applying to p2 for the given aspect."""
    if aspect_type == "conjunction":
        # Applying if p1 is behind p2 (lon_diff < 0) and p1 faster
        return lon_diff < 0 and p1.speed > p2.speed
    # For other aspects: applying if the orb is decreasing
    # Simplified: if p1.speed > p2.speed and p1 hasn't passed exact aspect yet
    return p1.speed > 0 and abs(lon_diff) < (
        {"sextile": 60.0, "square": 90.0, "trine": 120.0, "opposition": 180.0}.get(aspect_type, 0.0)
    )


def _fast_slow(
    n1: str, p1: PlanetData, n2: str, p2: PlanetData
) -> tuple[str | None, str | None, PlanetData | None, PlanetData | None]:
    """Determine which of two planets is faster and which is slower."""
    try:
        idx1 = _SPEED_ORDER.index(n1)
        idx2 = _SPEED_ORDER.index(n2)
    except ValueError:
        return None, None, None, None

    # Higher index = faster in _SPEED_ORDER
    if idx1 > idx2:
        return n1, n2, p1, p2
    return n2, n1, p2, p1


def _is_mutual_reception(n1: str, p1: PlanetData, n2: str, p2: PlanetData) -> bool:
    """Check if two planets are in mutual reception (each in the other's sign)."""
    return p1.sign_lord == n2 and p2.sign_lord == n1


def _check_nakta(
    fast_name: str,
    fast: PlanetData,
    slow_name: str,
    slow: PlanetData,
    moon: PlanetData,
) -> TajakaYoga | None:
    """Check Nakta — Moon transfers light between fast and slow planets."""
    # Moon must be applying to slow AND fast was applying to Moon
    moon_to_slow = _compute_tajaka_aspect(moon, slow)
    fast_to_moon = _compute_tajaka_aspect(fast, moon)

    if (
        moon_to_slow
        and moon_to_slow[2]  # Moon applying to slow
        and fast_to_moon
        and fast_to_moon[2]  # Fast applying to Moon
    ):
        return TajakaYoga(
            name="Nakta",
            name_hi="नक्त",
            fast_planet=fast_name,
            slow_planet=slow_name,
            aspect_type="transfer_via_moon",
            orb=round((moon_to_slow[1] + fast_to_moon[1]) / 2, 2),
            is_applying=True,
            is_positive=True,
            description=(
                f"Moon transfers light from {fast_name} to {slow_name} — "
                "Nakta: indirect connection through Moon; results come via intermediary."
            ),
        )
    return None


def _find_blocking_planet(
    fast_name: str,
    fast: PlanetData,
    slow_name: str,
    slow: PlanetData,
    chart: ChartData,
) -> str | None:
    """Find a planet that blocks the fast→slow applying aspect (Radda)."""
    for name, planet in chart.planets.items():
        if name in (fast_name, slow_name):
            continue
        # Blocking planet must be between fast and slow in longitude
        f_lon = fast.longitude
        s_lon = slow.longitude
        p_lon = planet.longitude
        # Check if p_lon is between f_lon and s_lon (handling wrap)
        if _is_between_longitudes(f_lon, s_lon, p_lon):
            return name
    return None


def _is_between_longitudes(start: float, end: float, point: float) -> bool:
    """Check if point is between start and end on the zodiac circle."""
    if start <= end:
        return start < point < end
    # Wrap case
    return point > start or point < end
