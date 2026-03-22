"""South Indian 10-Porutham marriage compatibility system.

Implements all 10 poruthams for South Indian (Tamil/Telugu/Kannada) tradition:
  1. Dinam        — Nakshatra distance auspiciousness (mod 9 check)
  2. Ganam        — Temperament: Deva / Manushya / Rakshasa
  3. Yoni         — Animal compatibility (binary: enemy or not)
  4. Rasi         — Moon sign distance compatibility
  5. Rasyadhipati — Moon sign lord friendship
  6. Rajju        — Body cord (ELIMINATORY — same part = dosha)
  7. Vedha        — Nakshatra obstruction pairs (ELIMINATORY)
  8. Vasya        — Sign-based dominance / magnetic control
  9. Mahendra     — Prosperity and longevity of groom
 10. Stree Deergha— Longevity and happiness of bride

Source: Muhurtha Martanda, Tamil Jyotisha tradition, Phaladeepika Ch.19.
"""

from __future__ import annotations

from daivai_engine.constants import (
    NAKSHATRA_ANIMALS,
    NAKSHATRA_GANAS,
    NAKSHATRAS,
    NATURAL_ENEMIES,
    NATURAL_FRIENDS,
    SIGN_LORDS,
    VASYA_TABLE,
    YONI_ENEMIES,
)
from daivai_engine.models.matching_porutham import PouruthamItem, PouruthamResult


# ---------------------------------------------------------------------------
# Rajju — body-cord nakshatra groups. Same group = eliminatory dosha.
# Source: Muhurtha Martanda; traditional South Indian matching texts.
# ---------------------------------------------------------------------------

_RAJJU: dict[str, list[int]] = {
    "Paada": [0, 8, 9, 17, 18, 26],  # Feet
    "Kati": [1, 7, 10, 16, 19, 25],  # Waist
    "Nabhi": [2, 6, 11, 15, 20, 24],  # Navel
    "Kantha": [3, 5, 12, 14, 21, 23],  # Neck
    "Shira": [4, 13, 22],  # Head
}

# Ascending nakshatras (rising through body parts: nak 0-4, 9-13, 18-22)
_RAJJU_ASCENDING: frozenset[int] = frozenset({0, 1, 2, 3, 4, 9, 10, 11, 12, 13, 18, 19, 20, 21, 22})

_NAK_TO_RAJJU: dict[int, str] = {n: part for part, naks in _RAJJU.items() for n in naks}

_RAJJU_SEVERITY: dict[str, str] = {
    "Paada": "mild",
    "Kati": "mild",
    "Nabhi": "moderate",
    "Kantha": "severe",
    "Shira": "severe",
}

_RAJJU_EFFECTS: dict[str, str] = {
    "Paada": "wandering; couple may not settle in one place",
    "Kati": "financial hardships and poverty",
    "Nabhi": "progeny difficulties",
    "Kantha": "danger to wife's longevity",
    "Shira": "danger to husband's longevity (widowhood risk)",
}

# ---------------------------------------------------------------------------
# South Indian Vedha pairs — different from North Indian Vedha.
# 13 pairs covering 26 nakshatras; Dhanishtha (22) has no Vedha partner.
# ---------------------------------------------------------------------------

_SI_VEDHA_PAIRS: frozenset[frozenset[int]] = frozenset(
    {
        frozenset({0, 17}),  # Ashwini   - Jyeshtha
        frozenset({1, 16}),  # Bharani   - Anuradha
        frozenset({2, 15}),  # Krittika  - Vishakha
        frozenset({3, 14}),  # Rohini    - Swati
        frozenset({4, 12}),  # Mrigashira- Hasta
        frozenset({5, 13}),  # Ardra     - Chitra
        frozenset({6, 11}),  # Punarvasu - Uttara Phalguni
        frozenset({7, 10}),  # Pushya    - Purva Phalguni
        frozenset({8, 9}),  # Ashlesha  - Magha
        frozenset({18, 26}),  # Moola     - Revati
        frozenset({19, 25}),  # Purva Ashadha  - Uttara Bhadrapada
        frozenset({20, 24}),  # Uttara Ashadha - Purva Bhadrapada
        frozenset({21, 23}),  # Shravana  - Shatabhisha
    }
)

# Mahendra: agreeable count positions (1-27, from girl nakshatra to boy)
_MAHENDRA_POSITIONS: frozenset[int] = frozenset({4, 7, 10, 13, 16, 19, 22, 25})

# Stree Deergha: count from boy to girl must be strictly greater than this
_STREE_DEERGHA_MIN: int = 13

# Rasi Porutham: disagreeing sign distances (1-12, from girl rasi to boy rasi)
_RASI_BAD: frozenset[int] = frozenset({2, 6, 8, 12})


# ---------------------------------------------------------------------------
# Individual porutham functions
# ---------------------------------------------------------------------------


def _dinam(boy_nak: int, girl_nak: int) -> PouruthamItem:
    """Dinam — nakshatra distance mod 9 auspiciousness check."""
    count = (boy_nak - girl_nak) % 27 + 1
    remainder = count % 9
    agrees = remainder in {0, 2, 4, 6, 8}
    return PouruthamItem(
        name="Dinam",
        name_tamil="திணம்",
        agrees=agrees,
        is_eliminatory=False,
        description=f"Count girl→boy: {count} (mod 9 = {remainder}) — {'agrees' if agrees else 'disagrees'}",
    )


def _ganam(boy_nak: int, girl_nak: int) -> PouruthamItem:
    """Ganam — gana temperament compatibility."""
    gana_b = NAKSHATRA_GANAS[boy_nak]
    gana_g = NAKSHATRA_GANAS[girl_nak]

    if gana_b == gana_g:
        agrees, desc = True, f"Same gana: {gana_b}"
    elif {gana_b, gana_g} == {"Deva", "Manushya"}:
        agrees, desc = True, f"Deva-Manushya: {gana_b} (boy) + {gana_g} (girl)"
    else:
        agrees, desc = False, f"Gana mismatch: {gana_b} (boy) + {gana_g} (girl)"

    return PouruthamItem(
        name="Ganam",
        name_tamil="கணம்",
        agrees=agrees,
        is_eliminatory=False,
        description=desc,
    )


def _yoni(boy_nak: int, girl_nak: int) -> PouruthamItem:
    """Yoni — animal compatibility (binary: enemy yoni disagrees)."""
    animal_b = NAKSHATRA_ANIMALS[boy_nak]
    animal_g = NAKSHATRA_ANIMALS[girl_nak]

    if YONI_ENEMIES.get(animal_b) == animal_g:
        agrees, desc = False, f"Enemy yoni: {animal_b} vs {animal_g}"
    elif animal_b == animal_g:
        agrees, desc = True, f"Same yoni: {animal_b}"
    else:
        agrees, desc = True, f"Compatible yoni: {animal_b} + {animal_g}"

    return PouruthamItem(
        name="Yoni",
        name_tamil="யோனி",
        agrees=agrees,
        is_eliminatory=False,
        description=desc,
    )


def _rasi(boy_sign: int, girl_sign: int) -> PouruthamItem:
    """Rasi — moon sign distance compatibility (2/6/8/12 axis disagrees)."""
    dist = (boy_sign - girl_sign) % 12 + 1
    agrees = dist not in _RASI_BAD
    exception = ""

    if not agrees:
        lord_b, lord_g = SIGN_LORDS[boy_sign], SIGN_LORDS[girl_sign]
        if lord_b in NATURAL_FRIENDS.get(lord_g, []) and lord_g in NATURAL_FRIENDS.get(lord_b, []):
            agrees = True
            exception = f"Rasi lords ({lord_g}/{lord_b}) are mutual friends — bad axis mitigated"

    return PouruthamItem(
        name="Rasi",
        name_tamil="ராசி",
        agrees=agrees,
        is_eliminatory=False,
        description=f"Distance girl→boy: {dist}/12 — {'agrees' if agrees else 'disagrees'}",
        exception_note=exception,
    )


def _rasyadhipati(boy_sign: int, girl_sign: int) -> PouruthamItem:
    """Rasyadhipati — moon sign lord friendship compatibility."""
    lord_b, lord_g = SIGN_LORDS[boy_sign], SIGN_LORDS[girl_sign]

    if lord_b == lord_g:
        agrees, desc = True, f"Same lord: {lord_b}"
    elif lord_g in NATURAL_FRIENDS.get(lord_b, []) and lord_b in NATURAL_FRIENDS.get(lord_g, []):
        agrees, desc = True, f"Mutual friends: {lord_b} & {lord_g}"
    elif lord_g in NATURAL_ENEMIES.get(lord_b, []) or lord_b in NATURAL_ENEMIES.get(lord_g, []):
        agrees, desc = False, f"Enmity: {lord_b} & {lord_g}"
    else:
        agrees, desc = False, f"Neutral/one-sided: {lord_b} & {lord_g} — insufficient"

    return PouruthamItem(
        name="Rasyadhipati",
        name_tamil="ராசியதிபதி",
        agrees=agrees,
        is_eliminatory=False,
        description=desc,
    )


def _rajju(boy_nak: int, girl_nak: int) -> PouruthamItem:
    """Rajju — body cord (ELIMINATORY). Same group = dosha."""
    part_b = _NAK_TO_RAJJU[boy_nak]
    part_g = _NAK_TO_RAJJU[girl_nak]

    if part_b != part_g:
        return PouruthamItem(
            name="Rajju",
            name_tamil="ரஜ்ஜு",
            agrees=True,
            is_eliminatory=True,
            description=f"Different Rajju ({part_b} vs {part_g}) — no dosha",
        )

    severity = _RAJJU_SEVERITY[part_b]
    effect = _RAJJU_EFFECTS[part_b]
    nak_b = NAKSHATRAS[boy_nak]
    nak_g = NAKSHATRAS[girl_nak]

    # Ascending+descending within same group is a partial exception per Tamil texts
    exception = ""
    if (boy_nak in _RAJJU_ASCENDING) != (girl_nak in _RAJJU_ASCENDING) and part_b != "Shira":
        exception = (
            "Opposite directions within same Rajju (ascending+descending) "
            "— dosha partially mitigated per some Tamil texts"
        )

    return PouruthamItem(
        name="Rajju",
        name_tamil="ரஜ்ஜு",
        agrees=False,
        is_eliminatory=True,
        description=(f"Same Rajju: {part_b} ({severity}). {nak_b} + {nak_g}. Effect: {effect}"),
        exception_note=exception,
    )


def _vedha(boy_nak: int, girl_nak: int) -> PouruthamItem:
    """Vedha — nakshatra obstruction pairs (ELIMINATORY, South Indian tradition)."""
    has_vedha = frozenset({boy_nak, girl_nak}) in _SI_VEDHA_PAIRS
    nak_b, nak_g = NAKSHATRAS[boy_nak], NAKSHATRAS[girl_nak]

    if has_vedha:
        return PouruthamItem(
            name="Vedha",
            name_tamil="வேதை",
            agrees=False,
            is_eliminatory=True,
            description=f"Vedha pair: {nak_b} + {nak_g} — obstructing nakshatras",
        )

    return PouruthamItem(
        name="Vedha",
        name_tamil="வேதை",
        agrees=True,
        is_eliminatory=True,
        description=f"No Vedha obstruction between {nak_b} and {nak_g}",
    )


def _vasya(boy_sign: int, girl_sign: int) -> PouruthamItem:
    """Vasya — sign-based dominance and magnetic attraction."""
    vasya_b = VASYA_TABLE.get(boy_sign, [])
    vasya_g = VASYA_TABLE.get(girl_sign, [])
    boy_ctrl = girl_sign in vasya_b
    girl_ctrl = boy_sign in vasya_g

    if boy_ctrl and girl_ctrl:
        agrees, desc = True, "Mutual Vasya — strong magnetic attraction"
    elif boy_ctrl:
        agrees, desc = True, "Boy's sign controls girl's (one-way Vasya)"
    elif girl_ctrl:
        agrees, desc = True, "Girl's sign controls boy's (one-way Vasya)"
    else:
        agrees, desc = False, "No Vasya relationship — no magnetic attraction"

    return PouruthamItem(
        name="Vasya",
        name_tamil="வசியம்",
        agrees=agrees,
        is_eliminatory=False,
        description=desc,
    )


def _mahendra(boy_nak: int, girl_nak: int) -> PouruthamItem:
    """Mahendra — groom welfare. Count from girl to boy must be in {4,7,10,13,16,19,22,25}."""
    count = (boy_nak - girl_nak) % 27 + 1
    agrees = count in _MAHENDRA_POSITIONS
    return PouruthamItem(
        name="Mahendra",
        name_tamil="மஹேந்திர",
        agrees=agrees,
        is_eliminatory=False,
        description=f"Count girl→boy: {count} — {'agrees' if agrees else 'disagrees'} (auspicious: 4,7,10,13,16,19,22,25)",
    )


def _stree_deergha(boy_nak: int, girl_nak: int) -> PouruthamItem:
    """Stree Deergha — bride longevity. Count from boy to girl must be >13."""
    count = (girl_nak - boy_nak) % 27 + 1
    agrees = count > _STREE_DEERGHA_MIN
    return PouruthamItem(
        name="Stree Deergha",
        name_tamil="ஸ்திரீ தீர்க்க",
        agrees=agrees,
        is_eliminatory=False,
        description=f"Count boy→girl: {count} — {'agrees' if agrees else 'disagrees'} (must be >13)",
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def compute_porutham(
    boy_nakshatra_index: int,
    girl_nakshatra_index: int,
    boy_moon_sign: int,
    girl_moon_sign: int,
) -> PouruthamResult:
    """Compute South Indian 10-Porutham marriage compatibility.

    Convention: boy = groom, girl = bride (traditional Tamil ordering).

    Rajju and Vedha are eliminatory — their presence marks the match as not
    recommended regardless of total agreed count. Minimum 6/10 for recommended.

    Args:
        boy_nakshatra_index: 0-based Moon nakshatra index of groom (0=Ashwini…26=Revati).
        girl_nakshatra_index: 0-based Moon nakshatra index of bride.
        boy_moon_sign: 0-based Moon sign index of groom (0=Aries…11=Pisces).
        girl_moon_sign: 0-based Moon sign index of bride.

    Returns:
        PouruthamResult with all 10 porutham results and overall recommendation.
    """
    poruthams = [
        _dinam(boy_nakshatra_index, girl_nakshatra_index),
        _ganam(boy_nakshatra_index, girl_nakshatra_index),
        _yoni(boy_nakshatra_index, girl_nakshatra_index),
        _rasi(boy_moon_sign, girl_moon_sign),
        _rasyadhipati(boy_moon_sign, girl_moon_sign),
        _rajju(boy_nakshatra_index, girl_nakshatra_index),
        _vedha(boy_nakshatra_index, girl_nakshatra_index),
        _vasya(boy_moon_sign, girl_moon_sign),
        _mahendra(boy_nakshatra_index, girl_nakshatra_index),
        _stree_deergha(boy_nakshatra_index, girl_nakshatra_index),
    ]

    agreed = sum(1 for p in poruthams if p.agrees)
    rajju_item = next(p for p in poruthams if p.name == "Rajju")
    vedha_item = next(p for p in poruthams if p.name == "Vedha")
    has_rajju = not rajju_item.agrees
    has_vedha = not vedha_item.agrees

    rajju_part = _NAK_TO_RAJJU[boy_nakshatra_index] if has_rajju else None
    rajju_sev = _RAJJU_SEVERITY[rajju_part] if rajju_part else "none"

    eliminatory = has_rajju or has_vedha
    is_recommended = agreed >= 6 and not eliminatory

    if agreed >= 8 and not eliminatory:
        recommendation = f"Excellent match ({agreed}/10) — highly recommended"
    elif agreed >= 6 and not eliminatory:
        recommendation = f"Good match ({agreed}/10) — recommended"
    elif eliminatory:
        doshas = []
        if has_rajju:
            doshas.append(f"Rajju Dosha ({rajju_part}, {rajju_sev})")
        if has_vedha:
            doshas.append("Vedha Dosha")
        recommendation = (
            f"Eliminatory dosha present: {', '.join(doshas)}. "
            f"Match not recommended despite {agreed}/10 agreement."
        )
    else:
        recommendation = f"Below minimum ({agreed}/10 < 6) — remedies and detailed analysis needed"

    return PouruthamResult(
        boy_nakshatra_index=boy_nakshatra_index,
        girl_nakshatra_index=girl_nakshatra_index,
        boy_moon_sign=boy_moon_sign,
        girl_moon_sign=girl_moon_sign,
        poruthams=poruthams,
        agreed_count=agreed,
        total_count=10,
        has_rajju_dosha=has_rajju,
        has_vedha_dosha=has_vedha,
        rajju_body_part=rajju_part,
        rajju_severity=rajju_sev,
        is_recommended=is_recommended,
        recommendation=recommendation,
    )
