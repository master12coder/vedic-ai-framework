"""Ashtakoot (36 Guna) matching for marriage compatibility.

Implements all 8 kootas with proper exception handling for doshas:
  - Bhakoot dosha exceptions (nakshatra lord friendship mitigation)
  - Nadi dosha noted (detailed exceptions in compatibility_advanced.py)
  - Vedha dosha awareness (13 nakshatra pairs that obstruct each other)

Source: Muhurta Chintamani, BPHS matching chapter, Phaladeepika.
"""

from __future__ import annotations

from daivai_engine.constants import (
    BHAKOOT_NEGATIVE_COMBOS,
    NAKSHATRA_ANIMALS,
    NAKSHATRA_GANAS,
    NAKSHATRA_LORDS,
    NAKSHATRA_NADIS,
    NAKSHATRAS,
    NATURAL_ENEMIES,
    NATURAL_FRIENDS,
    SIGN_ELEMENTS,
    SIGN_VARNA,
    VARNA_RANK,
    VASYA_TABLE,
    YONI_ENEMIES,
)
from daivai_engine.models.matching import KootaScore, MatchingResult


# Vedha nakshatra pairs — mutual obstruction in marriage context.
# If one partner's Moon nakshatra is in Vedha with the other's, the union
# faces obstacles (timing obstructions, not a permanent bar).
# Source: Muhurta Chintamani; 13 traditional pairs (0-based indices).
_VEDHA_PAIRS: frozenset[frozenset[int]] = frozenset(
    {
        frozenset({0, 23}),  # Ashwini - Shatabhisha
        frozenset({1, 24}),  # Bharani - Purva Bhadrapada
        frozenset({2, 25}),  # Krittika - Uttara Bhadrapada
        frozenset({3, 26}),  # Rohini - Revati
        frozenset({4, 22}),  # Mrigashira - Dhanishtha
        frozenset({5, 21}),  # Ardra - Shravana
        frozenset({6, 20}),  # Punarvasu - Uttara Ashadha
        frozenset({7, 19}),  # Pushya - Purva Ashadha
        frozenset({8, 18}),  # Ashlesha - Moola
        frozenset({9, 17}),  # Magha - Jyeshtha
        frozenset({10, 16}),  # Purva Phalguni - Anuradha
        frozenset({11, 15}),  # Uttara Phalguni - Vishakha
        frozenset({12, 14}),  # Hasta - Swati
    }
)


def _varna_score(sign1: int, sign2: int) -> KootaScore:
    """Varna Koota (1 point) — boy's varna >= girl's varna."""
    element1 = SIGN_ELEMENTS[sign1]
    element2 = SIGN_ELEMENTS[sign2]
    varna1 = SIGN_VARNA[element1]
    varna2 = SIGN_VARNA[element2]
    rank1 = VARNA_RANK[varna1]
    rank2 = VARNA_RANK[varna2]

    score = 1.0 if rank1 >= rank2 else 0.0
    return KootaScore(
        name="Varna",
        name_hindi="वर्ण",
        max_points=1.0,
        obtained=score,
        description=f"Boy: {varna1}, Girl: {varna2}",
    )


def _vasya_score(sign1: int, sign2: int) -> KootaScore:
    """Vasya Koota (2 points) — sign-based compatibility."""
    vasya_list1 = VASYA_TABLE.get(sign1, [])
    vasya_list2 = VASYA_TABLE.get(sign2, [])

    if sign2 in vasya_list1 and sign1 in vasya_list2:
        score = 2.0
        desc = "Mutual Vasya"
    elif sign2 in vasya_list1 or sign1 in vasya_list2:
        score = 1.0
        desc = "One-way Vasya"
    else:
        score = 0.0
        desc = "No Vasya"

    return KootaScore(
        name="Vasya",
        name_hindi="वश्य",
        max_points=2.0,
        obtained=score,
        description=desc,
    )


def _tara_score(nak1: int, nak2: int) -> KootaScore:
    """Tara Koota (3 points) — nakshatra distance modulo 9."""
    dist = (nak2 - nak1) % 27
    tara = (dist % 9) + 1

    # Auspicious taras: 1(Janma), 3(Vipath-avoid), 5(Pratyari-avoid), 7(Vadha-avoid)
    # Favorable: 2,4,6,8,9
    unfavorable = {3, 5, 7}
    if tara not in unfavorable:
        score = 1.5
    else:
        score = 0.0

    # Check reverse too
    dist_rev = (nak1 - nak2) % 27
    tara_rev = (dist_rev % 9) + 1
    if tara_rev not in unfavorable:
        score += 1.5
    else:
        score += 0.0

    return KootaScore(
        name="Tara",
        name_hindi="तारा",
        max_points=3.0,
        obtained=min(score, 3.0),
        description=f"Tara boy→girl: {tara}, girl→boy: {tara_rev}",
    )


def _yoni_score(nak1: int, nak2: int) -> KootaScore:
    """Yoni Koota (4 points) — animal compatibility."""
    animal1 = NAKSHATRA_ANIMALS[nak1]
    animal2 = NAKSHATRA_ANIMALS[nak2]

    if animal1 == animal2:
        score = 4.0
        desc = f"Same yoni: {animal1}"
    elif YONI_ENEMIES.get(animal1) == animal2:
        score = 0.0
        desc = f"Enemy yoni: {animal1} vs {animal2}"
    else:
        score = 2.0
        desc = f"Neutral yoni: {animal1} vs {animal2}"

    return KootaScore(
        name="Yoni",
        name_hindi="योनि",
        max_points=4.0,
        obtained=score,
        description=desc,
    )


def _graha_maitri_score(nak1: int, nak2: int) -> KootaScore:
    """Graha Maitri Koota (5 points) — planetary friendship of nakshatra lords."""
    lord1 = NAKSHATRA_LORDS[nak1]
    lord2 = NAKSHATRA_LORDS[nak2]

    if lord1 == lord2:
        score = 5.0
        desc = f"Same lord: {lord1}"
    elif lord2 in NATURAL_FRIENDS.get(lord1, []) and lord1 in NATURAL_FRIENDS.get(lord2, []):
        score = 5.0
        desc = f"Mutual friends: {lord1} & {lord2}"
    elif lord2 in NATURAL_FRIENDS.get(lord1, []) or lord1 in NATURAL_FRIENDS.get(lord2, []):
        score = 3.0
        desc = f"One-sided friendship: {lord1} & {lord2}"
    elif lord2 in NATURAL_ENEMIES.get(lord1, []) and lord1 in NATURAL_ENEMIES.get(lord2, []):
        score = 0.0
        desc = f"Mutual enemies: {lord1} & {lord2}"
    elif lord2 in NATURAL_ENEMIES.get(lord1, []) or lord1 in NATURAL_ENEMIES.get(lord2, []):
        score = 1.0
        desc = f"One-sided enmity: {lord1} & {lord2}"
    else:
        score = 2.0
        desc = f"Neutral: {lord1} & {lord2}"

    return KootaScore(
        name="Graha Maitri",
        name_hindi="ग्रह मैत्री",
        max_points=5.0,
        obtained=score,
        description=desc,
    )


def _gana_score(nak1: int, nak2: int) -> KootaScore:
    """Gana Koota (6 points) — Deva/Manushya/Rakshasa compatibility."""
    gana1 = NAKSHATRA_GANAS[nak1]
    gana2 = NAKSHATRA_GANAS[nak2]

    if gana1 == gana2:
        score = 6.0
        desc = f"Same gana: {gana1}"
    elif {gana1, gana2} == {"Deva", "Manushya"}:
        score = 3.0
        desc = "Deva-Manushya"
    elif {gana1, gana2} == {"Manushya", "Rakshasa"}:
        score = 1.0
        desc = "Manushya-Rakshasa"
    else:  # Deva-Rakshasa
        score = 0.0
        desc = "Deva-Rakshasa — most challenging"

    return KootaScore(
        name="Gana",
        name_hindi="गण",
        max_points=6.0,
        obtained=score,
        description=desc,
    )


def _bhakoot_score(sign1: int, sign2: int, nak1: int, nak2: int) -> KootaScore:
    """Bhakoot Koota (7 points) — Moon sign distance compatibility.

    Bhakoot dosha exceptions (Muhurta Chintamani):
      - If nakshatra lords of both partners are the same planet: cancelled.
      - If nakshatra lords are mutual friends: partially mitigated (3.5 pts).
      - 5/9 axis: traditionally less severe than 6/8 or 2/12.
    """
    dist_forward = ((sign2 - sign1) % 12) + 1
    dist_backward = ((sign1 - sign2) % 12) + 1
    combo = (dist_forward, dist_backward)

    if combo not in BHAKOOT_NEGATIVE_COMBOS:
        return KootaScore(
            name="Bhakoot",
            name_hindi="भकूट",
            max_points=7.0,
            obtained=7.0,
            description=f"Favorable distance: {dist_forward}/{dist_backward}",
        )

    # Dosha is present — check exceptions
    lord1 = NAKSHATRA_LORDS[nak1]
    lord2 = NAKSHATRA_LORDS[nak2]

    # Exception 1: Same nakshatra lord → dosha cancelled
    if lord1 == lord2:
        return KootaScore(
            name="Bhakoot",
            name_hindi="भकूट",
            max_points=7.0,
            obtained=7.0,
            description=(
                f"Bhakoot dosha {dist_forward}/{dist_backward} CANCELLED: "
                f"same nakshatra lord ({lord1})"
            ),
        )

    # Exception 2: Mutual friends → dosha mitigated (half points)
    mutual_friends = lord2 in NATURAL_FRIENDS.get(lord1, []) and lord1 in NATURAL_FRIENDS.get(
        lord2, []
    )
    if mutual_friends:
        return KootaScore(
            name="Bhakoot",
            name_hindi="भकूट",
            max_points=7.0,
            obtained=3.5,
            description=(
                f"Bhakoot dosha {dist_forward}/{dist_backward} MITIGATED: "
                f"nakshatra lords {lord1}/{lord2} are mutual friends (3.5/7)"
            ),
        )

    # 5/9 axis is less severe per some traditions
    if combo in {(5, 9), (9, 5)}:
        return KootaScore(
            name="Bhakoot",
            name_hindi="भकूट",
            max_points=7.0,
            obtained=0.0,
            description="Bhakoot dosha: 5/9 axis — present but less severe than 6/8 or 2/12",
        )

    return KootaScore(
        name="Bhakoot",
        name_hindi="भकूट",
        max_points=7.0,
        obtained=0.0,
        description=f"Bhakoot dosha: {dist_forward}/{dist_backward} axis — significant incompatibility",
    )


def _nadi_score(nak1: int, nak2: int) -> KootaScore:
    """Nadi Koota (8 points) — same nadi = 0 points (most critical)."""
    nadi1 = NAKSHATRA_NADIS[nak1]
    nadi2 = NAKSHATRA_NADIS[nak2]

    if nadi1 == nadi2:
        score = 0.0
        desc = f"Same nadi: {nadi1} — Nadi Dosha present"
    else:
        score = 8.0
        desc = f"Different nadi: {nadi1} vs {nadi2} — compatible"

    return KootaScore(
        name="Nadi",
        name_hindi="नाड़ी",
        max_points=8.0,
        obtained=score,
        description=desc,
    )


def compute_ashtakoot(
    person1_nakshatra_index: int,
    person1_moon_sign: int,
    person2_nakshatra_index: int,
    person2_moon_sign: int,
) -> MatchingResult:
    """Compute Ashtakoot (36 guna) matching.

    Convention: person1 = boy, person2 = girl (traditional).

    Includes:
    - All 8 kootas with proper exception handling for doshas
    - Vedha dosha check (13 traditional obstruction pairs)
    - Dosha summary notes for Nadi and Bhakoot
    - 18-point minimum threshold logic per BPHS
    """
    kootas = [
        _varna_score(person1_moon_sign, person2_moon_sign),
        _vasya_score(person1_moon_sign, person2_moon_sign),
        _tara_score(person1_nakshatra_index, person2_nakshatra_index),
        _yoni_score(person1_nakshatra_index, person2_nakshatra_index),
        _graha_maitri_score(person1_nakshatra_index, person2_nakshatra_index),
        _gana_score(person1_nakshatra_index, person2_nakshatra_index),
        _bhakoot_score(
            person1_moon_sign, person2_moon_sign, person1_nakshatra_index, person2_nakshatra_index
        ),
        _nadi_score(person1_nakshatra_index, person2_nakshatra_index),
    ]

    total = sum(k.obtained for k in kootas)
    max_total = 36.0
    percentage = (total / max_total) * 100

    # Vedha dosha check — Muhurta Chintamani
    has_vedha = frozenset({person1_nakshatra_index, person2_nakshatra_index}) in _VEDHA_PAIRS
    nak1_name = NAKSHATRAS[person1_nakshatra_index]
    nak2_name = NAKSHATRAS[person2_nakshatra_index]
    vedha_note = (
        f"Vedha Dosha: {nak1_name} and {nak2_name} are obstructing nakshatras — "
        "timing obstacles in the union. Remedies recommended."
        if has_vedha
        else ""
    )

    # Dosha notes
    dosha_notes: list[str] = []
    nadi_koota = next(k for k in kootas if k.name == "Nadi")
    if nadi_koota.obtained == 0.0:
        dosha_notes.append(
            "Nadi Dosha present (same nadi) — most serious dosha. "
            "Consult compatibility_advanced for exceptions."
        )
    bhakoot_koota = next(k for k in kootas if k.name == "Bhakoot")
    if bhakoot_koota.obtained == 0.0:
        dosha_notes.append(f"Bhakoot Dosha: {bhakoot_koota.description}")
    if has_vedha:
        dosha_notes.append(vedha_note)

    # Recommendation with 18-point threshold — BPHS
    if total >= 25:
        recommendation = "Excellent match (≥25/36) — highly recommended"
    elif total >= 18:
        recommendation = "Good match (≥18/36) — recommended with minor considerations"
    elif total >= 14:
        recommendation = "Average match (14-17/36) — proceed with caution and remedies"
    else:
        recommendation = (
            "Below minimum threshold (<14/36) — detailed chart analysis needed before proceeding"
        )

    return MatchingResult(
        person1_nakshatra_index=person1_nakshatra_index,
        person1_moon_sign=person1_moon_sign,
        person2_nakshatra_index=person2_nakshatra_index,
        person2_moon_sign=person2_moon_sign,
        kootas=kootas,
        total_obtained=total,
        total_max=max_total,
        percentage=round(percentage, 1),
        recommendation=recommendation,
        has_vedha_dosha=has_vedha,
        vedha_note=vedha_note,
        dosha_notes=dosha_notes,
    )
