"""Shadbala — six-fold planetary strength computation.

Implements all six components of Shadbala in shashtiyamsas (60ths of a rupa):
Sthana Bala, Dig Bala, Kala Bala, Cheshta Bala, Naisargika Bala, Drik Bala.
Also preserves the backward-compatible ``compute_planet_strengths`` API.
"""

from __future__ import annotations

from jyotish.utils.constants import (
    EXALTATION, DEBILITATION, OWN_SIGNS, MOOLTRIKONA,
    KENDRAS, SIGN_LORDS, PLANETS, SPECIAL_ASPECTS,
)
from jyotish.domain.constants.dignity import EXALTATION_DEGREE
from jyotish.compute.divisional import compute_navamsha_sign
from jyotish.domain.models.chart import ChartData
from jyotish.domain.models.strength import ShadbalaResult, PlanetStrength


# ---------------------------------------------------------------------------
# Fixed constants used across Shadbala components
# ---------------------------------------------------------------------------

# Seven classical planets (Rahu/Ketu excluded from traditional Shadbala)
SHADBALA_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Naisargika Bala (natural strength) — fixed values in shashtiyamsas
NAISARGIKA: dict[str, float] = {
    "Sun": 60.00,
    "Moon": 51.43,
    "Mars": 17.14,
    "Mercury": 25.71,
    "Jupiter": 34.28,
    "Venus": 42.86,
    "Saturn": 8.57,
}

# Minimum required total Shadbala (shashtiyamsas)
REQUIRED_SHADBALA: dict[str, float] = {
    "Sun": 390.0,
    "Moon": 360.0,
    "Mars": 300.0,
    "Mercury": 420.0,
    "Jupiter": 390.0,
    "Venus": 330.0,
    "Saturn": 300.0,
}

# Dig Bala best houses
_DIG_BEST: dict[str, int] = {
    "Sun": 10, "Mars": 10,
    "Jupiter": 1, "Mercury": 1,
    "Saturn": 7,
    "Moon": 4, "Venus": 4,
}

# Natural benefics and malefics
_BENEFICS = {"Jupiter", "Venus", "Moon", "Mercury"}
_MALEFICS = {"Sun", "Mars", "Saturn"}

# Panapara and Apoklima houses for Kendradi Bala
_PANAPARA = {2, 5, 8, 11}
_APOKLIMA = {3, 6, 9, 12}


# ---------------------------------------------------------------------------
# 1. Sthana Bala (positional strength)
# ---------------------------------------------------------------------------

def _uchcha_bala(planet_name: str, longitude: float) -> float:
    """Exaltation strength: max 60 at exact exaltation degree, 0 at debilitation."""
    if planet_name not in EXALTATION or planet_name not in EXALTATION_DEGREE:
        return 30.0  # Neutral for Rahu/Ketu if called

    exalt_sign = EXALTATION[planet_name]
    exalt_deg_in_sign = EXALTATION_DEGREE[planet_name]
    exalt_lon = exalt_sign * 30.0 + exalt_deg_in_sign

    diff = abs(longitude - exalt_lon)
    if diff > 180.0:
        diff = 360.0 - diff

    return (180.0 - diff) / 3.0


def _saptvargaja_bala(planet_name: str, longitude: float, sign_index: int) -> float:
    """Simplified Saptvargaja Bala using D1 and D9 dignity.

    Awards points for dignity in Rashi (D1) and Navamsha (D9).
    Full implementation would include D2, D3, D7, D12, D30 as well.
    """
    _dignity_pts = {"exalted": 30, "mooltrikona": 22.5, "own": 20, "neutral": 7.5, "debilitated": 3}

    # D1 dignity
    d1_dignity = _sign_dignity(planet_name, sign_index, longitude - sign_index * 30.0)
    d1_pts = _dignity_pts.get(d1_dignity, 7.5)

    # D9 dignity
    d9_sign = compute_navamsha_sign(longitude)
    d9_dignity = _sign_dignity(planet_name, d9_sign, 15.0)  # mid-sign approx
    d9_pts = _dignity_pts.get(d9_dignity, 7.5)

    return d1_pts + d9_pts


def _sign_dignity(planet_name: str, sign_index: int, deg_in_sign: float) -> str:
    """Determine planet dignity in a sign (replicates chart.py logic)."""
    if planet_name in EXALTATION and EXALTATION[planet_name] == sign_index:
        return "exalted"
    if planet_name in DEBILITATION and DEBILITATION[planet_name] == sign_index:
        return "debilitated"
    if planet_name in MOOLTRIKONA:
        mt_sign, mt_start, mt_end = MOOLTRIKONA[planet_name]
        if sign_index == mt_sign and mt_start <= deg_in_sign <= mt_end:
            return "mooltrikona"
    if planet_name in OWN_SIGNS and sign_index in OWN_SIGNS[planet_name]:
        return "own"
    return "neutral"


def _ojhayugma_bala(planet_name: str, sign_index: int) -> float:
    """Odd/even sign strength.

    Moon and Venus get 15 in even signs, others get 15 in odd signs.
    """
    is_odd_sign = sign_index % 2 == 0  # 0-indexed: Aries=0(odd), Taurus=1(even)
    if planet_name in ("Moon", "Venus"):
        return 15.0 if not is_odd_sign else 0.0
    return 15.0 if is_odd_sign else 0.0


def _kendradi_bala(house: int) -> float:
    """Kendra/Panapara/Apoklima strength."""
    if house in KENDRAS:
        return 60.0
    if house in _PANAPARA:
        return 30.0
    if house in _APOKLIMA:
        return 15.0
    return 15.0


def _drekkana_bala(planet_name: str, longitude: float) -> float:
    """Drekkana Bala based on D3 position.

    Male planets (Sun, Mars, Jupiter) strong in 1st drekkana (0-10 deg),
    neutral planets (Mercury, Saturn) in 2nd drekkana (10-20 deg),
    female planets (Moon, Venus) in 3rd drekkana (20-30 deg).
    """
    sign_index = int(longitude / 30.0)
    deg_in_sign = longitude - sign_index * 30.0

    if deg_in_sign < 10.0:
        drekkana = 1
    elif deg_in_sign < 20.0:
        drekkana = 2
    else:
        drekkana = 3

    male = {"Sun", "Mars", "Jupiter"}
    female = {"Moon", "Venus"}

    if planet_name in male and drekkana == 1:
        return 15.0
    if planet_name in female and drekkana == 3:
        return 15.0
    if planet_name not in male and planet_name not in female and drekkana == 2:
        return 15.0
    return 0.0


def _sthana_bala(chart: ChartData, planet_name: str) -> float:
    """Total Sthana Bala = sum of sub-components."""
    p = chart.planets[planet_name]
    uchcha = _uchcha_bala(planet_name, p.longitude)
    saptvar = _saptvargaja_bala(planet_name, p.longitude, p.sign_index)
    ojha = _ojhayugma_bala(planet_name, p.sign_index)
    kendra = _kendradi_bala(p.house)
    drekk = _drekkana_bala(planet_name, p.longitude)
    return round(uchcha + saptvar + ojha + kendra + drekk, 2)


# ---------------------------------------------------------------------------
# 2. Dig Bala (directional strength)
# ---------------------------------------------------------------------------

def _dig_bala(chart: ChartData, planet_name: str) -> float:
    """Directional strength: 60 at best house, 0 at worst (opposite)."""
    p = chart.planets[planet_name]
    best = _DIG_BEST.get(planet_name, 1)
    # House distance (circular, 1-12)
    dist = abs(p.house - best)
    if dist > 6:
        dist = 12 - dist
    return round(max(0.0, 60.0 * (1.0 - dist / 6.0)), 2)


# ---------------------------------------------------------------------------
# 3. Kala Bala (temporal strength, simplified)
# ---------------------------------------------------------------------------

def _kala_bala(chart: ChartData, planet_name: str) -> float:
    """Simplified temporal strength.

    Components (simplified):
    - Nathonnatha Bala: 30 each (would need birth-time day/night split)
    - Paksha Bala: benefics get 60 in Shukla Paksha, malefics in Krishna
      (simplified: use Moon longitude — Shukla if Moon 0-180 from Sun)
    - Ayana Bala: 30 each (simplified)
    """
    nathonnatha = 30.0  # Simplified — no day/night distinction

    # Paksha Bala from Moon-Sun distance
    moon_lon = chart.planets["Moon"].longitude
    sun_lon = chart.planets["Sun"].longitude
    moon_sun_diff = (moon_lon - sun_lon) % 360.0
    is_shukla = moon_sun_diff <= 180.0

    if planet_name in _BENEFICS:
        paksha = 60.0 if is_shukla else 0.0
    elif planet_name in _MALEFICS:
        paksha = 0.0 if is_shukla else 60.0
    else:
        paksha = 30.0

    ayana = 30.0  # Simplified

    return round(nathonnatha + paksha + ayana, 2)


# ---------------------------------------------------------------------------
# 4. Cheshta Bala (motional strength)
# ---------------------------------------------------------------------------

def _cheshta_bala(chart: ChartData, planet_name: str) -> float:
    """Motional strength based on speed and retrogression.

    Sun and Moon always get 30 (they do not retrograde).
    Retrograde: 60, Stationary (|speed| < 0.1): 45,
    Direct & fast (|speed| > avg): 30, Direct & slow: 15.
    """
    if planet_name in ("Sun", "Moon"):
        return 30.0

    p = chart.planets[planet_name]

    if p.is_retrograde:
        return 60.0

    speed = abs(p.speed)
    if speed < 0.1:
        return 45.0  # Stationary

    # Average daily speeds for comparison (approximate)
    avg_speeds: dict[str, float] = {
        "Mars": 0.524, "Mercury": 1.383, "Jupiter": 0.083,
        "Venus": 1.2, "Saturn": 0.034, "Rahu": 0.053, "Ketu": 0.053,
    }
    avg = avg_speeds.get(planet_name, 0.5)
    if speed >= avg:
        return 30.0
    return 15.0


# ---------------------------------------------------------------------------
# 5. Naisargika Bala (natural strength — fixed)
# ---------------------------------------------------------------------------

def _naisargika_bala(planet_name: str) -> float:
    """Fixed natural strength per planet."""
    return NAISARGIKA.get(planet_name, 0.0)


# ---------------------------------------------------------------------------
# 6. Drik Bala (aspectual strength, simplified)
# ---------------------------------------------------------------------------

def _drik_bala(chart: ChartData, planet_name: str) -> float:
    """Simplified aspectual strength from aspects received.

    +15 for each benefic aspect, -15 for each malefic aspect.
    """
    p = chart.planets[planet_name]
    target_house = p.house
    score = 0.0

    for other_name in SHADBALA_PLANETS:
        if other_name == planet_name:
            continue
        other = chart.planets[other_name]
        other_house = other.house

        # Check if other planet aspects this planet's house
        if _aspects_house(other_name, other_house, target_house):
            if other_name in _BENEFICS:
                score += 15.0
            elif other_name in _MALEFICS:
                score -= 15.0

    return round(score, 2)


def _aspects_house(planet_name: str, planet_house: int, target_house: int) -> bool:
    """Check if a planet aspects a target house (7th + special aspects)."""
    # Standard 7th aspect
    seventh = ((planet_house - 1 + 6) % 12) + 1
    if seventh == target_house:
        return True
    # Special aspects
    if planet_name in SPECIAL_ASPECTS:
        for asp_offset in SPECIAL_ASPECTS[planet_name]:
            aspected = ((planet_house - 1 + asp_offset - 1) % 12) + 1
            if aspected == target_house:
                return True
    return False


# ---------------------------------------------------------------------------
# Main Shadbala computation
# ---------------------------------------------------------------------------

def compute_shadbala(chart: ChartData) -> list[ShadbalaResult]:
    """Compute full six-fold Shadbala for the seven classical planets.

    Returns a list of ShadbalaResult sorted by total (descending), with
    ranks assigned (1 = strongest).
    """
    results: list[ShadbalaResult] = []

    for planet_name in SHADBALA_PLANETS:
        sb = _sthana_bala(chart, planet_name)
        db = _dig_bala(chart, planet_name)
        kb = _kala_bala(chart, planet_name)
        cb = _cheshta_bala(chart, planet_name)
        nb = _naisargika_bala(planet_name)
        drk = _drik_bala(chart, planet_name)
        total = round(sb + db + kb + cb + nb + drk, 2)
        req = REQUIRED_SHADBALA[planet_name]
        ratio = round(total / req, 3) if req > 0 else 0.0

        results.append(ShadbalaResult(
            planet=planet_name,
            sthana_bala=sb,
            dig_bala=db,
            kala_bala=kb,
            cheshta_bala=cb,
            naisargika_bala=nb,
            drik_bala=drk,
            total=total,
            required=req,
            ratio=ratio,
            is_strong=ratio >= 1.0,
            rank=0,
        ))

    # Assign ranks by total descending
    results.sort(key=lambda r: r.total, reverse=True)
    for i, r in enumerate(results):
        r.rank = i + 1

    return results


# ---------------------------------------------------------------------------
# Backward-compatible API (used by interpreter / formatter)
# ---------------------------------------------------------------------------

def compute_planet_strengths(chart: ChartData) -> list[PlanetStrength]:
    """Compute relative strengths for all planets (backward-compatible).

    Wraps the full Shadbala for the 7 classical planets and adds simplified
    entries for Rahu and Ketu to maintain API compatibility.
    """
    shadbala = compute_shadbala(chart)
    strengths: list[PlanetStrength] = []

    # Build a lookup for ratio-based normalization
    max_total = max(r.total for r in shadbala) if shadbala else 1.0

    for r in shadbala:
        # Normalize to 0-1 range for backward compatibility
        norm_sthana = min(1.0, r.sthana_bala / 180.0)
        norm_dig = min(1.0, r.dig_bala / 60.0)
        norm_kala = min(1.0, r.kala_bala / 120.0)
        total_rel = min(1.0, r.total / max_total) if max_total > 0 else 0.0

        strengths.append(PlanetStrength(
            planet=r.planet,
            sthana_bala=round(norm_sthana, 3),
            dig_bala=round(norm_dig, 3),
            kala_bala=round(norm_kala, 3),
            total_relative=round(total_rel, 3),
            rank=0,
            is_strong=r.is_strong,
        ))

    # Add simplified entries for Rahu and Ketu
    for node_name in ("Rahu", "Ketu"):
        if node_name in chart.planets:
            p = chart.planets[node_name]
            dignity_scores = {
                "exalted": 1.0, "mooltrikona": 0.85,
                "own": 0.75, "neutral": 0.4, "debilitated": 0.1,
            }
            sb = dignity_scores.get(p.dignity, 0.4)
            # Simplified dig/kala for nodes
            db = 0.5
            kb = 0.5
            total_rel = sb * 0.5 + db * 0.25 + kb * 0.25
            strengths.append(PlanetStrength(
                planet=node_name,
                sthana_bala=round(sb, 3),
                dig_bala=round(db, 3),
                kala_bala=round(kb, 3),
                total_relative=round(total_rel, 3),
                rank=0,
                is_strong=total_rel >= 0.55,
            ))

    # Assign ranks by total_relative descending
    strengths.sort(key=lambda s: s.total_relative, reverse=True)
    for i, s in enumerate(strengths):
        s.rank = i + 1

    return strengths


def get_strongest_planet(chart: ChartData) -> str:
    """Return the name of the strongest planet in the chart."""
    strengths = compute_planet_strengths(chart)
    return strengths[0].planet


def get_weakest_planet(chart: ChartData) -> str:
    """Return the name of the weakest planet in the chart."""
    strengths = compute_planet_strengths(chart)
    return strengths[-1].planet
