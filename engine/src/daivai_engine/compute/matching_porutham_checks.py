"""Individual Porutham check functions — South Indian 10-Porutham system."""

from __future__ import annotations

from daivai_engine.compute.matching_porutham_tables import (
    _MAHENDRA_POSITIONS,
    _NAK_TO_RAJJU,
    _RAJJU_ASCENDING,
    _RAJJU_EFFECTS,
    _RAJJU_SEVERITY,
    _RASI_BAD,
    _SI_VEDHA_PAIRS,
    _STREE_DEERGHA_MIN,
)
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
from daivai_engine.models.matching_porutham import PouruthamItem


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
