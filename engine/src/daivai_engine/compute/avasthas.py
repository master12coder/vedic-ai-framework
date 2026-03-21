"""Deeptadi, Lajjitadi, and Shayanadi Avastha computations from BPHS Ch.45.

Deeptadi uses PANCHADA (5-fold combined) friendship, not just Naisargika.
Panchada = Naisargika (natural, BPHS Ch.3 v53-56) + Tatkalika (temporary,
BPHS Ch.3 v57-58) based on actual planetary positions in the chart.

Shayanadi (12-fold) avasthas are positional — based on which 2.5° zone the
planet occupies within its sign. Odd signs run forward (Shayana→Nidra),
even signs run reversed (Nidra→Shayana).

Source: BPHS Chapter 45 v1-35, Chapter 3 v53-58.
"""

from __future__ import annotations

from daivai_engine.constants import (
    NATURAL_ENEMIES,
    NATURAL_FRIENDS,
    SIGN_ELEMENTS,
    SPECIAL_ASPECTS,
)
from daivai_engine.models.avastha import DeeptadiAvastha, LajjitadiAvastha, ShayanadiAvastha
from daivai_engine.models.chart import ChartData, PlanetData


_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
_DEEPTADI_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Temporary friend positions: 2,3,4,10,11,12 from planet (BPHS Ch.3 v57-58)
_TEMP_FRIEND_HOUSES = {2, 3, 4, 10, 11, 12}


# ── Panchada (5-fold) Friendship ─────────────────────────────────────────


def compute_panchada_relation(planet: str, sign_lord: str, chart: ChartData) -> str:
    """Compute 5-fold combined friendship between planet and a sign lord.

    Combines Naisargika (natural/permanent) and Tatkalika (temporary)
    friendship based on actual chart positions.

    Panchada combination (BPHS Ch.3 v57-58):
      Natural Friend  + Temp Friend = adhimitra (best friend)
      Natural Friend  + Temp Enemy  = sama (neutral)
      Natural Neutral + Temp Friend = mitra (friend)
      Natural Neutral + Temp Enemy  = shatru (enemy)
      Natural Enemy   + Temp Friend = sama (neutral)
      Natural Enemy   + Temp Enemy  = adhishatru (worst enemy)

    Returns: adhimitra / mitra / sama / shatru / adhishatru
    """
    # Step 1: Naisargika (natural) relationship
    if sign_lord in NATURAL_FRIENDS.get(planet, []):
        natural = "friend"
    elif sign_lord in NATURAL_ENEMIES.get(planet, []):
        natural = "enemy"
    else:
        natural = "neutral"

    # Step 2: Tatkalika (temporary) relationship
    # Based on distance between planet and sign_lord in the chart
    p = chart.planets.get(planet)
    lord_p = chart.planets.get(sign_lord)
    if p is None or lord_p is None:
        # Can't compute temporary — use natural only
        if natural == "friend":
            return "mitra"
        if natural == "enemy":
            return "shatru"
        return "sama"

    distance = ((lord_p.sign_index - p.sign_index) % 12) + 1
    temp_friend = distance in _TEMP_FRIEND_HOUSES

    # Step 3: Combine (BPHS Ch.3 v57-58)
    if natural == "friend" and temp_friend:
        return "adhimitra"
    if natural == "friend" and not temp_friend:
        return "sama"
    if natural == "neutral" and temp_friend:
        return "mitra"
    if natural == "neutral" and not temp_friend:
        return "shatru"
    if natural == "enemy" and temp_friend:
        return "sama"
    # natural == "enemy" and not temp_friend
    return "adhishatru"


# ── Deeptadi Avasthas ────────────────────────────────────────────────────


def compute_deeptadi_avasthas(chart: ChartData) -> list[DeeptadiAvastha]:
    """Compute 9-state Deeptadi Avastha using Panchada friendship.

    States (BPHS Ch.45 v1-10):
    1. Deepta (exalted) = 1.5x
    2. Swastha (own/mooltrikona) = 1.3x
    3. Mudita (adhimitra's sign) = 1.2x
    4. Shanta (mitra's sign) = 1.1x
    5. Deena (sama/neutral sign) = 0.8x
    6. Vikala (combust) = 0.5x
    7. Dukhita (shatru's sign) = 0.4x
    8. Khal (adhishatru's sign) = 0.3x
    9. Kopa (debilitated) = 0.2x

    Combustion and debilitation override sign-based states.

    Source: BPHS Ch.45 v1-10, Ch.3 v53-58 (Panchada Maitri).
    """
    results: list[DeeptadiAvastha] = []
    for name in _DEEPTADI_PLANETS:
        p = chart.planets[name]
        avastha, hi, desc, mult = _classify_deeptadi(name, p, chart)
        results.append(
            DeeptadiAvastha(
                planet=name,
                avastha=avastha,
                avastha_hi=hi,
                description=desc,
                strength_multiplier=mult,
            )
        )
    return results


def _classify_deeptadi(name: str, p: PlanetData, chart: ChartData) -> tuple[str, str, str, float]:
    """Classify using Panchada friendship. Priority: debil > combust > dignity > friendship."""
    # Kopa: debilitated
    if p.dignity == "debilitated":
        return ("kopa", "कोप", f"{name} is debilitated — defeated state", 0.2)

    # Vikala: combust
    if p.is_combust and name != "Sun":
        return ("vikala", "विकल", f"{name} is combust — crippled state", 0.5)

    # Deepta: exalted
    if p.dignity == "exalted":
        return ("deepta", "दीप्त", f"{name} is exalted — brilliant state", 1.5)

    # Swastha: own sign or mooltrikona
    if p.dignity in ("own", "mooltrikona"):
        return ("swastha", "स्वस्थ", f"{name} is in own sign — healthy state", 1.3)

    # Use PANCHADA friendship with sign lord (not just Naisargika)
    relation = compute_panchada_relation(name, p.sign_lord, chart)

    match relation:
        case "adhimitra":
            return ("mudita", "मुदित", f"{name} in best friend's sign — delighted state", 1.2)
        case "mitra":
            return ("shanta", "शान्त", f"{name} in friend's sign — peaceful state", 1.1)
        case "sama":
            return ("deena", "दीन", f"{name} in neutral sign — miserable state", 0.8)
        case "shatru":
            return ("dukhita", "दुखित", f"{name} in enemy's sign — distressed state", 0.4)
        case "adhishatru":
            return ("khal", "खल", f"{name} in worst enemy's sign — wicked state", 0.3)

    return ("deena", "दीन", f"{name} in neutral position", 0.8)


# ── Lajjitadi Avasthas ──────────────────────────────────────────────────


def compute_lajjitadi_avasthas(chart: ChartData) -> list[LajjitadiAvastha]:
    """Compute 6-state Lajjitadi Avastha for each planet.

    States (BPHS Ch.45 v11-20):
    1. Lajjita = in 5th house with Rahu/Ketu/Saturn/Mars
    2. Garvita = in exaltation or mooltrikona
    3. Kshudhita = in enemy sign or conjunct enemy (Panchada)
    4. Trushita = in water sign with enemy influence
    5. Mudita = conjunct friend or in friend's sign (Panchada)
    6. Kshobhita = conjunct Sun and aspected by malefic
    """
    results: list[LajjitadiAvastha] = []
    for name in _DEEPTADI_PLANETS:
        p = chart.planets[name]
        avastha, hi, desc, pos = _classify_lajjitadi(name, p, chart)
        results.append(
            LajjitadiAvastha(
                planet=name,
                avastha=avastha,
                avastha_hi=hi,
                description=desc,
                is_positive=pos,
            )
        )
    return results


def _classify_lajjitadi(name: str, p: PlanetData, chart: ChartData) -> tuple[str, str, str, bool]:
    """Classify Lajjitadi using Panchada friendship."""
    housemates = {n for n, o in chart.planets.items() if o.house == p.house and n != name}

    if p.house == 5 and housemates & {"Rahu", "Ketu", "Saturn", "Mars"}:
        return ("lajjita", "लज्जित", f"{name} in 5th with malefic — ashamed state", False)

    if p.dignity in ("exalted", "mooltrikona"):
        return ("garvita", "गर्वित", f"{name} exalted/mooltrikona — proud state", True)

    if name != "Sun" and "Sun" in housemates and _has_malefic_influence(name, chart):
        return ("kshobhita", "क्षोभित", f"{name} conjunct Sun with malefic — agitated", False)

    # Use Panchada for enemy/friend checks
    relation = compute_panchada_relation(name, p.sign_lord, chart)
    if relation in ("shatru", "adhishatru"):
        return ("kshudhita", "क्षुधित", f"{name} in enemy sign (Panchada) — hungry state", False)

    # Check conjunction with Panchada enemies
    for hm in housemates:
        hm_relation = compute_panchada_relation(name, hm, chart)
        if hm_relation in ("shatru", "adhishatru"):
            return ("kshudhita", "क्षुधित", f"{name} conjunct enemy — hungry state", False)

    element = SIGN_ELEMENTS[p.sign_index]
    if element == "Water" and relation in ("shatru", "adhishatru"):
        return ("trushita", "तृषित", f"{name} in water sign with enemy — thirsty state", False)

    if relation in ("mitra", "adhimitra"):
        return ("mudita", "मुदित", f"{name} with friend (Panchada) — happy state", True)

    return ("mudita", "मुदित", f"{name} in neutral/friendly position — content", True)


def _has_malefic_influence(planet_name: str, chart: ChartData) -> bool:
    """Check if planet is conjunct or aspected by a malefic."""
    p = chart.planets[planet_name]
    for other_name, other in chart.planets.items():
        if other_name == planet_name or other_name not in _MALEFICS:
            continue
        if other.house == p.house:
            return True
        if ((other.house - 1 + 6) % 12) + 1 == p.house:
            return True
        for asp_dist in SPECIAL_ASPECTS.get(other_name, []):
            target = ((other.house - 1 + asp_dist - 1) % 12) + 1
            if target == p.house:
                return True
    return False


# ── Shayanadi Avasthas (12-fold) ─────────────────────────────────────────────

# 12 avastha names in order for ODD signs — BPHS Ch.45 v21-35
_SHAYANADI_SEQUENCE: list[str] = [
    "shayana",  # 0-2.5°  — sleeping; planet gives very sluggish/delayed results
    "upavesha",  # 2.5-5°  — sitting; moderate and lazy results
    "netrapani",  # 5-7.5°  — tears; gives sorrowful results
    "prakasha",  # 7.5-10° — illumined; bright, good results
    "gamana",  # 10-12.5°— walking forward; progressive, improving results
    "agama",  # 12.5-15°— approaching; improving, somewhat delayed
    "sabha",  # 15-17.5°— assembly; dignified, public recognition
    "aagama",  # 17.5-20°— arrived; fulfilled, full results delivered
    "bhojana",  # 20-22.5°— eating; pleasure and enjoyment to native
    "nrityalipsya",  # 22.5-25°— wishing to dance; desires and artistic pleasures
    "kautuka",  # 25-27.5°— playful; light-hearted, curiosity
    "nidra",  # 27.5-30°— deep sleep; very sluggish, dormant results
]

_SHAYANADI_HI: list[str] = [
    "शयान",
    "उपवेश",
    "नेत्रपाणि",
    "प्रकाश",
    "गमन",
    "आगम",
    "सभा",
    "आगामी",
    "भोजन",
    "नृत्यलिप्सा",
    "कौतुक",
    "निद्रा",
]

# Positive states give good results; negative states give poor/delayed results
_SHAYANADI_POSITIVE: list[bool] = [
    False,  # shayana — negative
    False,  # upavesha — negative
    False,  # netrapani — negative
    True,  # prakasha — positive
    True,  # gamana — positive (mixed but generally positive)
    False,  # agama — negative (delay)
    True,  # sabha — positive
    True,  # aagama — positive
    True,  # bhojana — positive
    True,  # nrityalipsya — positive (desires fulfilled)
    True,  # kautuka — positive
    False,  # nidra — negative
]

# Classical result summaries from BPHS Ch.45
_SHAYANADI_RESULTS: list[str] = [
    "Planet in Shayana: delayed, sluggish results; native may lack energy from this planet",
    "Planet in Upavesha: moderate results, somewhat lazy or passive in its domain",
    "Planet in Netrapani: sorrowful results; emotional pain from this planet's significations",
    "Planet in Prakasha: bright and active; bestows good results in its domain",
    "Planet in Gamana: results improve over time; forward momentum in significations",
    "Planet in Agama: results approaching; some delay before fruits are enjoyed",
    "Planet in Sabha: dignified and respected; public recognition through this planet",
    "Planet in Aagama: results have arrived; full manifestation of significations",
    "Planet in Bhojana: pleasure and enjoyment; native savors the benefits",
    "Planet in Nrityalipsya: artistic pleasures and desires fulfilled",
    "Planet in Kautuka: light-hearted benefits; curiosity and exploration",
    "Planet in Nidra: dormant planet; results deeply delayed or suppressed",
]

# Strength fractions (for use in composite strength calculations)
_SHAYANADI_STRENGTH: list[float] = [
    0.25,
    0.40,
    0.20,
    0.85,
    0.70,
    0.45,
    0.80,
    0.90,
    0.85,
    0.75,
    0.70,
    0.15,
]

# Odd sign indices (Aries=0, Gemini=2, Leo=4, Libra=6, Sagittarius=8, Aquarius=10)
_ODD_SIGNS: frozenset[int] = frozenset({0, 2, 4, 6, 8, 10})

# Each zone spans 30°/12 = 2.5°
_ZONE_SPAN: float = 30.0 / 12.0


def compute_shayanadi_avasthas(chart: ChartData) -> list[ShayanadiAvastha]:
    """Compute the 12-fold Shayanadi Avastha for each planet.

    Each sign is divided into 12 equal zones of 2.5°. For odd signs the
    sequence runs Shayana→Nidra (ascending degrees). For even signs the
    sequence is reversed (Nidra at 0°, Shayana at 27.5°).

    Source: BPHS Chapter 45 v21-35.
    """
    results: list[ShayanadiAvastha] = []
    for name in _DEEPTADI_PLANETS:
        p = chart.planets[name]
        zone_idx = _shayanadi_zone(p.sign_index, p.degree_in_sign)
        results.append(
            ShayanadiAvastha(
                planet=name,
                avastha=_SHAYANADI_SEQUENCE[zone_idx],
                avastha_hi=_SHAYANADI_HI[zone_idx],
                zone=zone_idx + 1,  # 1-based for readability
                is_positive=_SHAYANADI_POSITIVE[zone_idx],
                result_summary=_SHAYANADI_RESULTS[zone_idx],
                strength_fraction=_SHAYANADI_STRENGTH[zone_idx],
            )
        )
    return results


def _shayanadi_zone(sign_index: int, degree_in_sign: float) -> int:
    """Return 0-indexed zone (0-11) for a planet's position.

    Odd signs: zone increases with degree (0° → zone 0, 27.5° → zone 11).
    Even signs: zone decreases with degree (0° → zone 11, 27.5° → zone 0).
    """
    raw_zone = int(degree_in_sign / _ZONE_SPAN)
    raw_zone = min(raw_zone, 11)  # Clamp to 0-11 (handles exact 30°)
    if sign_index in _ODD_SIGNS:
        return raw_zone
    else:
        return 11 - raw_zone  # Reverse for even signs
