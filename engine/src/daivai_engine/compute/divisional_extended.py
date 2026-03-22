"""Extended Shodashvarga divisional chart computations — D2 through D60."""

from __future__ import annotations


def compute_hora_sign(longitude: float) -> int:
    """Compute D2 (Hora) sign index.

    Each sign divided into 2 parts of 15° each.
    Odd signs: 1st hora = Sun (Leo/4), 2nd hora = Moon (Cancer/3)
    Even signs: 1st hora = Moon (Cancer/3), 2nd hora = Sun (Leo/4)
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    first_half = degree_in_sign < 15.0
    if sign_index % 2 == 0:  # Odd signs
        return 4 if first_half else 3  # Leo then Cancer
    else:  # Even signs
        return 3 if first_half else 4  # Cancer then Leo


def compute_drekkana_sign(longitude: float) -> int:
    """Compute D3 (Drekkana) sign index.

    Each sign divided into 3 parts of 10°.
    1st decanate: same sign
    2nd decanate: 5th from sign
    3rd decanate: 9th from sign
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / 10.0)
    if part > 2:
        part = 2
    offsets = [0, 4, 8]
    return (sign_index + offsets[part]) % 12


def compute_chaturthamsha_sign(longitude: float) -> int:
    """Compute D4 (Chaturthamsha) sign index.

    Each sign divided into 4 parts of 7.5°.
    Counts from same sign, 4th, 7th, 10th.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / 7.5)
    if part > 3:
        part = 3
    offsets = [0, 3, 6, 9]
    return (sign_index + offsets[part]) % 12


def compute_panchamsha_sign(longitude: float) -> int:
    """Compute D5 (Panchamsha) sign index.

    Each sign divided into 5 parts of 6°.
    Odd signs start from same sign, even signs start from opposite.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / 6.0)
    if part > 4:
        part = 4
    if sign_index % 2 == 0:
        start = sign_index
    else:
        start = (sign_index + 6) % 12
    return (start + part) % 12


def compute_shashthamsha_sign(longitude: float) -> int:
    """Compute D6 (Shashthamsha) sign index.

    Each sign divided into 6 parts of 5°.
    Odd signs start from same sign, even signs start from 7th.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / 5.0)
    if part > 5:
        part = 5
    if sign_index % 2 == 0:
        start = sign_index
    else:
        start = (sign_index + 6) % 12
    return (start + part) % 12


def compute_shodashamsha_sign(longitude: float) -> int:
    """Compute D16 (Shodashamsha) sign index.

    Each sign divided into 16 parts of 1.875°.
    Movable signs start from Aries, fixed from Leo, dual from Sagittarius.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / (30.0 / 16.0))
    if part > 15:
        part = 15
    modality = sign_index % 3  # 0=movable, 1=fixed, 2=dual
    start_map = {0: 0, 1: 4, 2: 8}
    return (start_map[modality] + part) % 12


def compute_vimshamsha_sign(longitude: float) -> int:
    """Compute D20 (Vimshamsha) sign index.

    Each sign divided into 20 parts of 1.5°.
    Movable from Aries, fixed from Sagittarius, dual from Leo.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / 1.5)
    if part > 19:
        part = 19
    modality = sign_index % 3
    start_map = {0: 0, 1: 8, 2: 4}
    return (start_map[modality] + part) % 12


def compute_chaturvimshamsha_sign(longitude: float) -> int:
    """Compute D24 (Chaturvimshamsha/Siddhamsha) sign index.

    Each sign divided into 24 parts of 1.25°.
    Odd signs from Leo, even signs from Cancer.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / 1.25)
    if part > 23:
        part = 23
    start = 4 if sign_index % 2 == 0 else 3
    return (start + part) % 12


def compute_saptavimshamsha_sign(longitude: float) -> int:
    """Compute D27 (Saptavimshamsha/Nakshatramsha) sign index.

    Each sign divided into 27 parts of ~1.111°.
    Fire signs from Aries, earth from Cancer, air from Libra, water from Capricorn.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / (30.0 / 27.0))
    if part > 26:
        part = 26
    element = sign_index % 4
    start_map = {0: 0, 1: 3, 2: 6, 3: 9}
    return (start_map[element] + part) % 12


def compute_trimshamsha_sign(longitude: float) -> int:
    """Compute D30 (Trimshamsha) sign index.

    Non-uniform division. For odd signs:
    0-5° Mars, 5-10° Saturn, 10-18° Jupiter, 18-25° Mercury, 25-30° Venus
    Even signs reverse order.
    Returns the sign owned by the ruling planet.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0

    if sign_index % 2 == 0:  # Odd sign
        if degree_in_sign < 5:
            ruler = 0  # Mars -> Aries
        elif degree_in_sign < 10:
            ruler = 10  # Saturn -> Aquarius
        elif degree_in_sign < 18:
            ruler = 8  # Jupiter -> Sagittarius
        elif degree_in_sign < 25:
            ruler = 2  # Mercury -> Gemini
        else:
            ruler = 6  # Venus -> Libra
    else:  # Even sign
        if degree_in_sign < 5:
            ruler = 1  # Venus -> Taurus
        elif degree_in_sign < 12:
            ruler = 5  # Mercury -> Virgo
        elif degree_in_sign < 20:
            ruler = 11  # Jupiter -> Pisces
        elif degree_in_sign < 25:
            ruler = 9  # Saturn -> Capricorn
        else:
            ruler = 7  # Mars -> Scorpio
    return ruler


def compute_khavedamsha_sign(longitude: float) -> int:
    """Compute D40 (Khavedamsha) sign index.

    Each sign divided into 40 parts of 0.75°.
    Odd signs from Aries, even signs from Libra.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / 0.75)
    if part > 39:
        part = 39
    start = 0 if sign_index % 2 == 0 else 6
    return (start + part) % 12


def compute_akshavedamsha_sign(longitude: float) -> int:
    """Compute D45 (Akshavedamsha) sign index.

    Each sign divided into 45 parts of 0.6667°.
    Movable from Aries, fixed from Leo, dual from Sagittarius.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / (30.0 / 45.0))
    if part > 44:
        part = 44
    modality = sign_index % 3
    start_map = {0: 0, 1: 4, 2: 8}
    return (start_map[modality] + part) % 12


def compute_shashtyamsha_sign(longitude: float) -> int:
    """Compute D60 (Shashtyamsha) sign index.

    Each sign divided into 60 parts of 0.5°.
    Always counts from same sign.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    part = int(degree_in_sign / 0.5)
    if part > 59:
        part = 59
    return (sign_index + part) % 12


# VARGA_FUNCTIONS and compute_varga are defined in divisional.py (orchestrator)
# to avoid circular imports — they need D7/D9/D10/D12 from divisional.py.
