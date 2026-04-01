"""Daily rashifal generator — transit-based predictions for each Moon sign.

Generates deterministic rashifal for all 12 signs using current planetary
transit positions. No birth chart needed, no LLM — pure computation from
the Gochara score table (Phaladeepika Ch.26).

Each sign is treated as a virtual Moon sign: "What would a person with Moon
in this sign experience today?" Transit houses are counted from the sign,
and the compact gochara scores drive the day rating and domain predictions.
"""

from __future__ import annotations

import logging
from datetime import date

from pydantic import BaseModel, ConfigDict

from daivai_engine.constants import (
    NUM_SIGNS,
    SIGNS_EN,
    SIGNS_HI,
)
from daivai_products.plugins.content.rashifal_engine import (
    CAREER_HOUSES,
    FINANCE_HOUSES,
    HEALTH_HOUSES,
    LOVE_HOUSES,
    compute_sign_scores,
    day_rating_from_scores,
    domain_prediction,
    get_current_positions,
    load_gochara,
    load_mantras,
    lucky_color,
    lucky_number,
    pick_remedy,
)


logger = logging.getLogger(__name__)


# ── Models ───────────────────────────────────────────────────────────────────


class SignRashifal(BaseModel):
    """Daily rashifal for one sign."""

    model_config = ConfigDict(frozen=True)

    sign: str
    sign_hindi: str
    date: str
    day_rating: int
    lucky_color: str
    lucky_number: int
    career: str
    finance: str
    health: str
    love: str
    remedy: str
    mantra: str


class DailyRashifal(BaseModel):
    """Complete daily rashifal for all 12 signs."""

    model_config = ConfigDict(frozen=True)

    date: str
    signs: list[SignRashifal]


# ── Public API ───────────────────────────────────────────────────────────────


def generate_rashifal(date_str: str | None = None) -> DailyRashifal:
    """Generate transit-based rashifal for all 12 Moon signs.

    Uses current planetary positions to derive sign-specific forecasts.
    No AI/LLM — pure computation from transits and Gochara score table
    (Phaladeepika Ch.26).

    Args:
        date_str: Date as DD/MM/YYYY. Defaults to today.

    Returns:
        DailyRashifal with predictions for all 12 signs.
    """
    if date_str:
        day, month, year = date_str.split("/")
        target = date(int(year), int(month), int(day))
    else:
        target = date.today()

    formatted_date = target.strftime("%d/%m/%Y")

    # Load YAML data
    gochara_data = load_gochara()
    gochara_scores: dict[str, list[int]] = gochara_data.get("scores", {})
    gochara_results: dict[str, dict[int, str]] = {
        planet: {int(k): v for k, v in houses.items()}
        for planet, houses in gochara_data.get("results", {}).items()
    }
    mantras = load_mantras()

    # Get current planet sign positions
    positions = get_current_positions(target)

    # Derive per-day lucky color (same for all signs)
    day_color = lucky_color(target)

    sign_rashifals: list[SignRashifal] = []

    for sign_index in range(NUM_SIGNS):
        scores = compute_sign_scores(sign_index, positions, gochara_scores)

        rating = day_rating_from_scores(scores)

        career = domain_prediction(
            positions,
            sign_index,
            CAREER_HOUSES,
            gochara_results,
        )
        finance = domain_prediction(
            positions,
            sign_index,
            FINANCE_HOUSES,
            gochara_results,
        )
        health = domain_prediction(
            positions,
            sign_index,
            HEALTH_HOUSES,
            gochara_results,
        )
        love = domain_prediction(
            positions,
            sign_index,
            LOVE_HOUSES,
            gochara_results,
        )

        remedy, mantra = pick_remedy(scores, mantras)

        sign_rashifals.append(
            SignRashifal(
                sign=SIGNS_EN[sign_index],
                sign_hindi=SIGNS_HI[sign_index],
                date=formatted_date,
                day_rating=rating,
                lucky_color=day_color,
                lucky_number=lucky_number(sign_index, target),
                career=career,
                finance=finance,
                health=health,
                love=love,
                remedy=remedy,
                mantra=mantra,
            )
        )

    return DailyRashifal(date=formatted_date, signs=sign_rashifals)
