"""Special yoga detection — Chatussagara and Mahabhagya yogas.

These are standalone yogas that don't fit neatly into the lunar/solar/nabhasa
categories already handled by other modules.

  Chatussagara: All 4 kendra houses occupied by at least one planet.
  Mahabhagya:   Day/night birth criterion + Sun/Moon/Lagna in matching sign parity.

Source: BPHS Ch.36; Phaladeepika Ch.6.
"""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData
from daivai_engine.models.yoga import YogaResult


def detect_special_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect Chatussagara and Mahabhagya Yogas.

    Args:
        chart: Computed birth chart.

    Returns:
        List of detected special YogaResults.
    """
    yogas: list[YogaResult] = []
    yogas.extend(_detect_chatussagara(chart))
    yogas.extend(_detect_mahabhagya(chart))
    return yogas


# ── Chatussagara Yoga ─────────────────────────────────────────────────────────


def _detect_chatussagara(chart: ChartData) -> list[YogaResult]:
    """Detect Chatussagara Yoga — all 4 kendras occupied.

    All four angular houses (1, 4, 7, 10) must each contain at least one
    planet (including Rahu and Ketu). This creates a chart filled with
    strength in all four pillars of life.

    Source: BPHS Ch.36; Phaladeepika Ch.6 v.18.

    Args:
        chart: Computed birth chart.

    Returns:
        List with one YogaResult if Chatussagara is present.
    """
    kendra_houses = (1, 4, 7, 10)
    occupied_kendras: list[int] = []
    planets_in_kendra: list[str] = []

    for house in kendra_houses:
        planets_here = [name for name, p in chart.planets.items() if p.house == house]
        if planets_here:
            occupied_kendras.append(house)
            planets_in_kendra.extend(planets_here)

    if len(occupied_kendras) < 4:
        return []

    return [
        YogaResult(
            name="Chatussagara Yoga",
            name_hindi="चतुस्सागर योग",
            is_present=True,
            planets_involved=planets_in_kendra,
            houses_involved=list(kendra_houses),
            description=(
                "All 4 kendra houses occupied — four oceans of strength, "
                "well-rounded life with power in career, home, relationships, and fame"
            ),
            effect="benefic",
        )
    ]


# ── Mahabhagya Yoga ───────────────────────────────────────────────────────────


def _detect_mahabhagya(chart: ChartData) -> list[YogaResult]:
    """Detect Mahabhagya (Great Fortune) Yoga.

    Conditions (BPHS Ch.36 v.14):
      Male:   Day birth (Sun in H7-H12) + Sun, Moon, and Lagna all in
              ODD signs (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius).
      Female: Night birth (Sun in H1-H6) + Sun, Moon, and Lagna all in
              EVEN signs (Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces).

    Odd sign = sign_index is even (0-indexed from Aries).
    Even sign = sign_index is odd.

    Day birth = Sun is above the horizon = Sun's house is 7-12.

    Args:
        chart: Computed birth chart.

    Returns:
        List with one YogaResult if Mahabhagya is present.
    """
    sun = chart.planets["Sun"]
    moon = chart.planets["Moon"]

    is_day_birth = sun.house in {7, 8, 9, 10, 11, 12}
    gender_lower = chart.gender.lower()

    # Odd sign: sign_index is even (Aries=0, Gemini=2, Leo=4, Libra=6, Sagittarius=8, Aquarius=10)
    def _is_odd_sign(sign_index: int) -> bool:
        return sign_index % 2 == 0

    signs_to_check = [sun.sign_index, moon.sign_index, chart.lagna_sign_index]
    planets_involved = ["Sun", "Moon"]

    if gender_lower == "male" and is_day_birth and all(_is_odd_sign(s) for s in signs_to_check):
        return [
            YogaResult(
                name="Mahabhagya Yoga",
                name_hindi="महाभाग्य योग",
                is_present=True,
                planets_involved=planets_involved,
                houses_involved=[sun.house, moon.house],
                description=(
                    "Day birth (male) with Sun, Moon, and Lagna in odd signs -- "
                    "great fortune, noble character, royal status, long life"
                ),
                effect="benefic",
            )
        ]

    if (
        gender_lower == "female"
        and not is_day_birth
        and all(not _is_odd_sign(s) for s in signs_to_check)
    ):
        return [
            YogaResult(
                name="Mahabhagya Yoga",
                name_hindi="महाभाग्य योग",
                is_present=True,
                planets_involved=planets_involved,
                houses_involved=[sun.house, moon.house],
                description=(
                    "Night birth (female) with Sun, Moon, and Lagna in even signs -- "
                    "great fortune, renowned, virtuous, prosperous life"
                ),
                effect="benefic",
            )
        ]

    return []
