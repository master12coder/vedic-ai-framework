"""Namakarana (Hindu Naming Ceremony) computation.

Implements the traditional Vedic process for selecting an auspicious name
based on the birth nakshatra-pada (108 aksharas), rashi letters, sound
vibration (Nada), numerology compatibility, and Muhurta for the ceremony.

Sources:
    Muhurta Chintamani Ch.8 (naming rules)
    Brihat Samhita Ch.104 (naming syllables)
    Dharmasindhu (Grihya Sutras synthesis)
    Paraskara Grihya Sutra 1.17 (Namakarana rite)
"""

from __future__ import annotations

from datetime import datetime, timedelta

from daivai_engine.compute.panchang import compute_panchang
from daivai_engine.knowledge.loader import load_namakarana_rules
from daivai_engine.models.chart import ChartData
from daivai_engine.models.namakarana import (
    NakshtraAkshar,
    NamakaranaMuhurta,
    NamakaranaResult,
    NameScore,
    NameSuggestion,
    RashiLetters,
)


# Functional benefics by lagna for sound scoring.
# Planets that are generally auspicious rulers (Trikona/Lagna lords).
_LAGNA_BENEFICS: dict[str, list[str]] = {
    "Mesha": ["Sun", "Jupiter", "Mars"],
    "Vrishabha": ["Venus", "Saturn", "Mercury"],
    "Mithuna": ["Mercury", "Venus", "Saturn"],
    "Karka": ["Moon", "Mars", "Jupiter"],
    "Simha": ["Sun", "Mars", "Jupiter"],
    "Kanya": ["Mercury", "Venus", "Saturn"],
    "Tula": ["Venus", "Saturn", "Mercury"],
    "Vrischika": ["Moon", "Jupiter", "Mars"],
    "Dhanu": ["Jupiter", "Sun", "Mars"],
    "Makara": ["Saturn", "Venus", "Mercury"],
    "Kumbha": ["Saturn", "Venus", "Mercury"],
    "Meena": ["Jupiter", "Moon", "Mars"],
}

# Numerology: Chaldean system letter-to-number
_LETTER_VALUES: dict[str, int] = {
    "a": 1,
    "b": 2,
    "c": 3,
    "d": 4,
    "e": 5,
    "f": 8,
    "g": 3,
    "h": 5,
    "i": 1,
    "j": 1,
    "k": 2,
    "l": 3,
    "m": 4,
    "n": 5,
    "o": 7,
    "p": 8,
    "q": 1,
    "r": 2,
    "s": 3,
    "t": 4,
    "u": 6,
    "v": 6,
    "w": 6,
    "x": 5,
    "y": 1,
    "z": 7,
}

# Numerology compatibility: name_number → life_number → score (0-10)
_NUMEROLOGY_COMPAT: dict[int, dict[int, float]] = {
    1: {1: 9, 2: 5, 3: 8, 4: 3, 5: 8, 6: 4, 7: 9, 8: 5, 9: 9},
    2: {1: 5, 2: 9, 3: 8, 4: 8, 5: 3, 6: 9, 7: 5, 8: 3, 9: 8},
    3: {1: 8, 2: 8, 3: 9, 4: 3, 5: 8, 6: 8, 7: 5, 8: 3, 9: 9},
    4: {1: 3, 2: 8, 3: 3, 4: 9, 5: 3, 6: 8, 7: 8, 8: 9, 9: 3},
    5: {1: 8, 2: 3, 3: 8, 4: 3, 5: 9, 6: 5, 7: 8, 8: 5, 9: 8},
    6: {1: 4, 2: 9, 3: 8, 4: 8, 5: 5, 6: 9, 7: 4, 8: 8, 9: 9},
    7: {1: 9, 2: 5, 3: 5, 4: 8, 5: 8, 6: 4, 7: 9, 8: 3, 9: 5},
    8: {1: 5, 2: 3, 3: 3, 4: 9, 5: 5, 6: 8, 7: 3, 8: 9, 9: 3},
    9: {1: 9, 2: 8, 3: 9, 4: 3, 5: 8, 6: 9, 7: 5, 8: 3, 9: 9},
}

_RECOMMENDATION_THRESHOLDS = [
    (8.0, "Highly Recommended"),
    (6.0, "Recommended"),
    (4.0, "Acceptable"),
    (0.0, "Avoid"),
]

_MUHURTA_SCORE_THRESHOLD = 3.5


def get_naming_syllables(nakshatra_index: int, pada: int) -> list[str]:
    """Return all recommended starting syllables for the given nakshatra-pada.

    Args:
        nakshatra_index: 0-based nakshatra index (0=Ashwini … 26=Revati)
        pada: 1-4 (quarter of the nakshatra)

    Returns:
        List of syllables: primary first, then alternates.
    """
    rules = load_namakarana_rules()
    aksharas: list[dict] = rules.get("aksharas", [])
    for entry in aksharas:
        if entry["nakshatra_index"] == nakshatra_index:
            padas: list[dict] = entry["padas"]
            pada_data = padas[pada - 1]
            syllables = [pada_data["syllable"], *pada_data.get("alternates", [])]
            return [s for s in syllables if s]
    return []


def get_nakshtra_akshar(nakshatra_index: int, pada: int) -> NakshtraAkshar:
    """Build a NakshtraAkshar model for the given nakshatra and pada.

    Args:
        nakshatra_index: 0-based index (0=Ashwini … 26=Revati)
        pada: 1-4
    """
    rules = load_namakarana_rules()
    aksharas: list[dict] = rules.get("aksharas", [])
    for entry in aksharas:
        if entry["nakshatra_index"] == nakshatra_index:
            pada_data = entry["padas"][pada - 1]
            return NakshtraAkshar(
                nakshatra=entry["nakshatra"],
                nakshatra_index=nakshatra_index,
                pada=pada,
                syllable=pada_data["syllable"],
                syllable_devanagari=pada_data["devanagari"],
                alternate_syllables=list(pada_data.get("alternates", [])),
                rashi=entry["rashi"],
                nakshatra_lord=entry["lord"],
            )
    msg = f"Nakshatra index {nakshatra_index} not found in knowledge base."
    raise ValueError(msg)


def get_rashi_letters(rashi_index: int) -> RashiLetters:
    """Return all naming letters associated with a rashi.

    Args:
        rashi_index: 0-based rashi index (0=Mesha … 11=Meena)
    """
    rules = load_namakarana_rules()
    rashi_list: list[dict] = rules.get("rashi_letters", [])
    for entry in rashi_list:
        if entry["rashi_index"] == rashi_index:
            return RashiLetters(
                rashi=entry["rashi"],
                rashi_index=rashi_index,
                letters=list(entry["letters"]),
                primary_letters=list(entry["primary_letters"]),
            )
    msg = f"Rashi index {rashi_index} not found in knowledge base."
    raise ValueError(msg)


def compute_name_numerology(name: str) -> int:
    """Compute the Chaldean name number for a name (Roman letters).

    Sums the Chaldean value of each letter and reduces to 1-9.
    Master numbers 11 and 22 are reduced further for naming compatibility.

    Args:
        name: Name in Roman letters (case-insensitive)

    Returns:
        Name number 1-9
    """
    total = sum(_LETTER_VALUES.get(ch.lower(), 0) for ch in name if ch.isalpha())
    if total == 0:
        return 1
    return _reduce_to_single(total)


def compute_life_number(dob: str) -> int:
    """Compute the life path number from date of birth (DD/MM/YYYY).

    Args:
        dob: Date of birth in DD/MM/YYYY format

    Returns:
        Life path number 1-9
    """
    digits = [ch for ch in dob if ch.isdigit()]
    total = sum(int(d) for d in digits)
    return _reduce_to_single(total)


def score_name(name: str, birth_chart: ChartData) -> NameScore:
    """Score a name comprehensively against a birth chart.

    Evaluates four dimensions:
    1. Nakshatra syllable match (does name start with prescribed syllable?)
    2. Rashi letter compatibility
    3. Numerology (name number vs life path compatibility)
    4. Sound/planet vibration aligned with lagna

    Args:
        name: Candidate name (Roman transliteration or English)
        birth_chart: Pre-computed ChartData from compute_chart()

    Returns:
        NameScore with component and total scores
    """
    moon = birth_chart.planets.get("Moon")
    if moon is None:
        msg = "Moon not found in chart planets"
        raise ValueError(msg)

    nakshatra_idx = moon.nakshatra_index
    pada = moon.pada
    rashi_idx = moon.sign_index
    # 1. Nakshatra syllable match
    syllables = get_naming_syllables(nakshatra_idx, pada)
    name_upper = name.strip()
    matched_syllable: str | None = None
    for syl in syllables:
        if name_upper.lower().startswith(syl.lower()):
            matched_syllable = syl
            break

    nakshatra_match = matched_syllable is not None
    nakshatra_score = 10.0 if nakshatra_match else 0.0

    # 2. Rashi letter match
    rashi_data = get_rashi_letters(rashi_idx)
    rashi_match = any(
        name_upper.lower().startswith(letter.lower()) for letter in rashi_data.letters
    )
    rashi_score = 8.0 if rashi_match else (3.0 if nakshatra_match else 0.0)

    # 3. Numerology
    name_number = compute_name_numerology(name)
    life_number = compute_life_number(birth_chart.dob)
    num_compat = _NUMEROLOGY_COMPAT.get(name_number, {}).get(life_number, 5.0)
    numerology_score = num_compat

    # 4. Sound / planet vibration
    planet_of_sound = _get_planet_of_sound(name_upper)
    lagna_sign = _get_lagna_sign(birth_chart)
    benefic_planets = _LAGNA_BENEFICS.get(lagna_sign, [])
    planet_is_benefic = planet_of_sound in benefic_planets
    sound_score = 8.0 if planet_is_benefic else 4.0

    # Weighted total: nakshatra 40%, rashi 20%, numerology 20%, sound 20%
    total = (
        nakshatra_score * 0.40 + rashi_score * 0.20 + numerology_score * 0.20 + sound_score * 0.20
    )

    recommendation = _get_recommendation(total)

    return NameScore(
        name=name,
        nakshatra_syllable_match=nakshatra_match,
        matching_syllable=matched_syllable,
        nakshatra_score=round(nakshatra_score, 2),
        rashi_score=round(rashi_score, 2),
        numerology_name_number=name_number,
        numerology_life_number=life_number,
        numerology_score=round(numerology_score, 2),
        planet_of_sound=planet_of_sound,
        planet_is_benefic_for_lagna=planet_is_benefic,
        sound_score=round(sound_score, 2),
        total_score=round(total, 2),
        recommendation=recommendation,
    )


def suggest_names(birth_chart: ChartData, gender: str) -> list[NameSuggestion]:
    """Suggest traditional Sanskrit names matching the birth chart.

    Filters the name database by gender, scores each name, and returns
    results sorted by total score (highest first).

    Args:
        birth_chart: Pre-computed ChartData
        gender: "M" (male), "F" (female), or "N" (neutral/unisex)

    Returns:
        List of NameSuggestion sorted by score descending.
    """
    rules = load_namakarana_rules()
    names_db: list[dict] = rules.get("names", [])

    moon = birth_chart.planets.get("Moon")
    if moon is None:
        return []

    nakshatra_idx = moon.nakshatra_index
    pada = moon.pada
    syllables = get_naming_syllables(nakshatra_idx, pada)

    suggestions: list[NameSuggestion] = []
    gender_upper = gender.upper()

    for entry in names_db:
        entry_gender = str(entry.get("gender", "N")).upper()
        # Include neutral names for all genders; filter by gender otherwise
        if entry_gender not in ("N", gender_upper):
            continue

        name = str(entry["name"])
        syllable = str(entry.get("syllable", ""))

        # Check nakshatra match
        is_nak_match = any(name.lower().startswith(syl.lower()) for syl in syllables)

        scored = score_name(name, birth_chart)
        suggestions.append(
            NameSuggestion(
                name=name,
                gender=entry_gender,
                meaning=str(entry.get("meaning", "")),
                deity=str(entry.get("deity", "")),
                starting_syllable=syllable,
                score=scored,
                is_nakshatra_match=is_nak_match,
            )
        )

    suggestions.sort(key=lambda s: s.score.total_score, reverse=True)
    return suggestions


def compute_namakarana_muhurta(
    birth_date: str,
    lat: float,
    lon: float,
    tz_name: str = "Asia/Kolkata",
    days_to_check: int = 40,
    max_results: int = 8,
) -> list[NamakaranaMuhurta]:
    """Find auspicious dates for the Namakarana (naming ceremony).

    Scans dates starting from birth_date + 10 days (traditional sutak period),
    evaluates Panchang quality, and returns the best candidates.

    Args:
        birth_date: Birth date in DD/MM/YYYY format
        lat: Latitude of the ceremony location
        lon: Longitude of the ceremony location
        tz_name: Timezone name (default: Asia/Kolkata)
        days_to_check: Number of days to scan (default: 40)
        max_results: Maximum candidates to return

    Returns:
        List of NamakaranaMuhurta sorted by score descending.
    """
    rules = load_namakarana_rules()
    muhurta_rules: dict = rules.get("muhurta_rules", {})
    scoring: dict = muhurta_rules.get("scoring", {})

    favorable_naks: set[str] = set(muhurta_rules.get("all_favorable_nakshatras", []))
    unfavorable_naks: set[str] = set(muhurta_rules.get("unfavorable_nakshatras", []))
    sthira_naks: set[str] = set(muhurta_rules.get("favorable_nakshatras", {}).get("sthira", []))
    mridu_naks: set[str] = set(muhurta_rules.get("favorable_nakshatras", {}).get("mridu", []))
    favorable_tithis: set[int] = set(muhurta_rules.get("favorable_tithis", {}).get("indices", []))
    unfavorable_tithis: set[int] = set(
        muhurta_rules.get("unfavorable_tithis", {}).get("indices", [])
    )
    favorable_vara: set[str] = set(muhurta_rules.get("favorable_vara", []))
    unfavorable_vara: set[str] = set(muhurta_rules.get("unfavorable_vara", []))

    # Scoring weights from YAML (with defaults)
    s_fav_nak = float(scoring.get("favorable_nakshatra", 3.0))
    s_sthira = float(scoring.get("sthira_nakshatra_bonus", 1.0))
    s_mridu = float(scoring.get("mridu_nakshatra_bonus", 0.5))
    s_fav_tithi = float(scoring.get("favorable_tithi", 1.0))
    s_unfav_tithi = float(scoring.get("unfavorable_tithi_penalty", -2.5))
    s_shukla = float(scoring.get("shukla_paksha_bonus", 1.0))
    s_fav_vara = float(scoring.get("favorable_vara", 1.0))
    s_unfav_vara = float(scoring.get("unfavorable_vara_penalty", -1.5))
    s_unfav_nak = float(scoring.get("unfavorable_nakshatra_penalty", -3.0))

    # Start 10 days after birth (Sutak period ends)
    try:
        day, month, year = birth_date.split("/")
        birth_dt = datetime(int(year), int(month), int(day))
    except (ValueError, AttributeError):
        birth_dt = datetime.now()

    start_dt = birth_dt + timedelta(days=10)
    candidates: list[NamakaranaMuhurta] = []

    for offset in range(days_to_check):
        current_dt = start_dt + timedelta(days=offset)
        date_str = current_dt.strftime("%d/%m/%Y")

        try:
            panchang = compute_panchang(date_str, lat, lon, tz_name)
        except Exception:
            continue

        score = 0.0
        reasons: list[str] = []
        nak_name = panchang.nakshatra_name
        tithi_idx = panchang.tithi_index
        vara = panchang.vara

        # Nakshatra evaluation
        if nak_name in favorable_naks:
            score += s_fav_nak
            reasons.append(f"Favorable nakshatra: {nak_name}")
            if nak_name in sthira_naks:
                score += s_sthira
                reasons.append(f"Sthira (fixed) nakshatra bonus: {nak_name}")
            elif nak_name in mridu_naks:
                score += s_mridu
                reasons.append(f"Mridu (soft) nakshatra bonus: {nak_name}")
        elif nak_name in unfavorable_naks:
            score += s_unfav_nak
            reasons.append(f"Unfavorable nakshatra: {nak_name}")

        # Tithi evaluation
        if tithi_idx in unfavorable_tithis:
            score += s_unfav_tithi
            reasons.append(f"Inauspicious tithi: {panchang.tithi_name}")
        elif tithi_idx in favorable_tithis:
            score += s_fav_tithi
            reasons.append(f"Favorable tithi: {panchang.tithi_name}")

        # Paksha
        if tithi_idx < 15:
            score += s_shukla
            reasons.append("Shukla Paksha (bright fortnight)")
            paksha = "Shukla"
        else:
            paksha = "Krishna"

        # Vara (weekday)
        if vara in favorable_vara:
            score += s_fav_vara
            reasons.append(f"Auspicious day: {vara}")
        elif vara in unfavorable_vara:
            score += s_unfav_vara
            reasons.append(f"Inauspicious day: {vara}")

        candidates.append(
            NamakaranaMuhurta(
                date=date_str,
                day=current_dt.strftime("%A"),
                nakshatra=nak_name,
                tithi=panchang.tithi_name,
                paksha=paksha,
                vara=vara,
                score=round(score, 2),
                reasons=reasons,
                rahu_kaal=panchang.rahu_kaal,
                is_recommended=score >= _MUHURTA_SCORE_THRESHOLD,
            )
        )

    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates[:max_results]


def compute_namakarana(
    birth_chart: ChartData,
    gender: str,
    ceremony_lat: float | None = None,
    ceremony_lon: float | None = None,
    tz_name: str = "Asia/Kolkata",
) -> NamakaranaResult:
    """Perform full Namakarana computation for a birth chart.

    Combines syllable lookup, name suggestions, and muhurta in one call.

    Args:
        birth_chart: Pre-computed ChartData
        gender: "M", "F", or "N"
        ceremony_lat: Ceremony location latitude (defaults to birth location)
        ceremony_lon: Ceremony location longitude (defaults to birth location)
        tz_name: Timezone name

    Returns:
        NamakaranaResult with all components
    """
    moon = birth_chart.planets.get("Moon")
    if moon is None:
        msg = "Moon data missing from chart — cannot compute Namakarana."
        raise ValueError(msg)

    nak_idx = moon.nakshatra_index
    pada = moon.pada
    rashi_idx = moon.sign_index

    akshar = get_nakshtra_akshar(nak_idx, pada)
    rashi_ltrs = get_rashi_letters(rashi_idx)
    suggestions = suggest_names(birth_chart, gender)

    lat = ceremony_lat if ceremony_lat is not None else birth_chart.latitude
    lon = ceremony_lon if ceremony_lon is not None else birth_chart.longitude

    muhurtas = compute_namakarana_muhurta(
        birth_date=birth_chart.dob,
        lat=lat,
        lon=lon,
        tz_name=tz_name,
    )

    return NamakaranaResult(
        birth_nakshatra=moon.nakshatra,
        birth_nakshatra_index=nak_idx,
        birth_pada=pada,
        birth_rashi=moon.sign,
        birth_rashi_index=rashi_idx,
        nakshatra_akshar=akshar,
        rashi_letters=rashi_ltrs,
        name_suggestions=suggestions,
        muhurta_candidates=muhurtas,
    )


# ── Private helpers ────────────────────────────────────────────────────────


def _reduce_to_single(n: int) -> int:
    """Reduce an integer to a single digit (1-9) by summing digits."""
    while n > 9:
        n = sum(int(d) for d in str(n))
    return max(1, n)


def _get_planet_of_sound(name: str) -> str:
    """Return the planet associated with the starting sound of the name."""
    rules = load_namakarana_rules()
    planet_akshar: dict = rules.get("planet_akshar", {})
    name_lower = name.lower()
    # Match longest prefix first to handle multi-char syllables (Bha, Gha, etc.)
    best_planet = "Mercury"
    best_len = 0
    for planet, data in planet_akshar.items():
        for sound in data.get("sounds", []):
            if name_lower.startswith(sound.lower()) and len(sound) > best_len:
                best_planet = planet
                best_len = len(sound)
    return best_planet


def _get_lagna_sign(birth_chart: ChartData) -> str:
    """Extract the lagna sign name from the chart."""
    from daivai_engine.constants import SIGNS

    return SIGNS[birth_chart.lagna_sign_index]


def _get_recommendation(score: float) -> str:
    """Map a numeric score to a recommendation label."""
    for threshold, label in _RECOMMENDATION_THRESHOLDS:
        if score >= threshold:
            return label
    return "Avoid"
