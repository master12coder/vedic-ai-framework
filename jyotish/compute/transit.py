"""Transit analysis — current/future planet positions overlaid on natal chart."""

from __future__ import annotations

from datetime import datetime

import swisseph as swe

from jyotish.utils.constants import (
    PLANETS, SWE_PLANETS, SIGNS, SIGN_LORDS, NAKSHATRAS, NAKSHATRA_LORDS,
)
from jyotish.utils.datetime_utils import to_jd, now_ist
from jyotish.compute.chart import ChartData, get_nakshatra
from jyotish.domain.models.transit import TransitPlanet, TransitData


def compute_transits(chart: ChartData, target_date: datetime | None = None) -> TransitData:
    """Compute transit positions and overlay on natal chart.

    Args:
        chart: Natal chart
        target_date: Date to compute transits for (default: now)
    """
    if target_date is None:
        target_date = now_ist()

    jd = to_jd(target_date)
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    transit_planets: list[TransitPlanet] = []
    major_transits: list[str] = []

    for planet_name in PLANETS:
        if planet_name == "Ketu":
            # Ketu = Rahu + 180
            rahu_t = next(t for t in transit_planets if t.name == "Rahu")
            lon = (rahu_t.longitude + 180.0) % 360.0
            speed = -1  # retrograde
        else:
            swe_id = SWE_PLANETS[planet_name]
            result = swe.calc_ut(jd, swe_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)
            lon = result[0][0]
            speed = result[0][3]

        sign_index = int(lon / 30.0)
        degree_in_sign = lon - sign_index * 30.0
        nak_index, _ = get_nakshatra(lon)
        is_retro = speed < 0 if planet_name != "Ketu" else True

        # Which natal house does this transit activate?
        natal_house = ((sign_index - chart.lagna_sign_index) % 12) + 1

        tp = TransitPlanet(
            name=planet_name,
            longitude=round(lon, 4),
            sign_index=sign_index,
            sign=SIGNS[sign_index],
            degree_in_sign=round(degree_in_sign, 4),
            nakshatra=NAKSHATRAS[nak_index],
            is_retrograde=is_retro,
            natal_house_activated=natal_house,
        )
        transit_planets.append(tp)

    # Flag major transits
    moon_sign = chart.planets["Moon"].sign_index

    # Saturn transit check (Sadesati)
    saturn_t = next(t for t in transit_planets if t.name == "Saturn")
    saturn_moon_dist = (saturn_t.sign_index - moon_sign) % 12
    if saturn_moon_dist in (11, 0, 1):
        phase_map = {11: "Rising (12th)", 0: "Peak (over Moon)", 1: "Setting (2nd)"}
        major_transits.append(
            f"SADESATI: Saturn in {saturn_t.sign} — {phase_map[saturn_moon_dist]} from natal Moon"
        )

    # Jupiter transits
    jupiter_t = next(t for t in transit_planets if t.name == "Jupiter")
    major_transits.append(
        f"Jupiter transiting {jupiter_t.sign} — activating natal house {jupiter_t.natal_house_activated}"
    )

    # Rahu-Ketu transit axis
    rahu_t = next(t for t in transit_planets if t.name == "Rahu")
    ketu_t = next(t for t in transit_planets if t.name == "Ketu")
    major_transits.append(
        f"Rahu-Ketu axis: {rahu_t.sign} ({rahu_t.natal_house_activated}H) — "
        f"{ketu_t.sign} ({ketu_t.natal_house_activated}H)"
    )

    return TransitData(
        target_date=target_date.strftime("%d/%m/%Y"),
        natal_chart_name=chart.name,
        natal_lagna_sign=chart.lagna_sign,
        transits=transit_planets,
        major_transits=major_transits,
    )
