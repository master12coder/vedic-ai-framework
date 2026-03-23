"""Tests for Dasha-Transit integration — dignity, relationship, aspect, favorability.

Covers:
  - Transit dignity computation (exalted / own / debilitated / neutral)
  - MD-AD natural relationship (friends / enemies / neutral)
  - Mutual aspect detection between dasha lords
  - Overall favorability scoring algorithm

Fixture:
  manish_chart: Mithuna lagna, Moon in Rohini Pada 2.
"""

from __future__ import annotations

from datetime import datetime

import pytz

from daivai_engine.compute.dasha_transit import compute_dasha_transit
from daivai_engine.compute.dasha_transit_helpers import (
    _aspects,
    _check_mutual_aspect,
    _get_dignity,
    _get_relationship,
)
from daivai_engine.compute.dasha_transit_scoring import compute_overall_favorability
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dasha_transit import DashaLordTransit


_DATE = datetime(2026, 3, 22, 12, 0, 0, tzinfo=pytz.UTC)


class TestTransitDignity:
    """Tests for transit dignity computation."""

    def test_jupiter_exalted_cancer(self) -> None:
        assert _get_dignity("Jupiter", 3) == "exalted"

    def test_jupiter_debilitated_capricorn(self) -> None:
        assert _get_dignity("Jupiter", 9) == "debilitated"

    def test_jupiter_own_sagittarius(self) -> None:
        assert _get_dignity("Jupiter", 8) == "own"

    def test_jupiter_own_pisces(self) -> None:
        assert _get_dignity("Jupiter", 11) == "own"

    def test_saturn_exalted_libra(self) -> None:
        assert _get_dignity("Saturn", 6) == "exalted"

    def test_saturn_debilitated_aries(self) -> None:
        assert _get_dignity("Saturn", 0) == "debilitated"

    def test_mercury_neutral_aries(self) -> None:
        assert _get_dignity("Mercury", 0) == "neutral"

    def test_sun_exalted_aries(self) -> None:
        assert _get_dignity("Sun", 0) == "exalted"

    def test_venus_own_taurus(self) -> None:
        assert _get_dignity("Venus", 1) == "own"

    def test_mars_own_scorpio(self) -> None:
        assert _get_dignity("Mars", 7) == "own"

    def test_transit_dignity_on_real_chart(self, manish_chart: ChartData) -> None:
        result = compute_dasha_transit(manish_chart, _DATE)
        valid = {"exalted", "own", "debilitated", "neutral"}
        assert result.md_lord.transit_dignity in valid
        assert result.ad_lord.transit_dignity in valid


class TestMdAdRelationship:
    """Tests for MD-AD natural relationship."""

    def test_jupiter_sun_friends(self) -> None:
        assert _get_relationship("Jupiter", "Sun") == "friends"

    def test_jupiter_venus_enemies(self) -> None:
        assert _get_relationship("Jupiter", "Venus") == "enemies"

    def test_jupiter_saturn_neutral(self) -> None:
        assert _get_relationship("Jupiter", "Saturn") == "neutral"

    def test_saturn_mercury_friends(self) -> None:
        assert _get_relationship("Saturn", "Mercury") == "friends"

    def test_saturn_sun_enemies(self) -> None:
        assert _get_relationship("Saturn", "Sun") == "enemies"

    def test_sun_mercury_neutral(self) -> None:
        assert _get_relationship("Sun", "Mercury") == "neutral"

    def test_on_real_chart(self, manish_chart: ChartData) -> None:
        result = compute_dasha_transit(manish_chart, _DATE)
        assert result.md_ad_relationship in ("friends", "neutral", "enemies")


class TestMutualAspect:
    """Tests for mutual aspect detection between dasha lords."""

    def test_opposite_signs(self) -> None:
        assert _check_mutual_aspect(0, 6, "Mercury", "Venus")

    def test_same_sign_no_aspect(self) -> None:
        assert not _check_mutual_aspect(0, 0, "Mercury", "Venus")

    def test_jupiter_5th_aspect(self) -> None:
        assert _aspects(0, 4, "Jupiter")

    def test_jupiter_9th_aspect(self) -> None:
        assert _aspects(0, 8, "Jupiter")

    def test_saturn_3rd_aspect(self) -> None:
        assert _aspects(0, 2, "Saturn")

    def test_saturn_10th_aspect(self) -> None:
        assert _aspects(0, 9, "Saturn")

    def test_mars_4th_aspect(self) -> None:
        assert _aspects(0, 3, "Mars")

    def test_mars_8th_aspect(self) -> None:
        assert _aspects(0, 7, "Mars")

    def test_no_aspect_random_house(self) -> None:
        """Mercury has no special aspect; only 7th should work."""
        assert not _aspects(0, 3, "Mercury")

    def test_7th_aspect_all_planets(self) -> None:
        for planet in ["Sun", "Moon", "Mercury", "Venus"]:
            assert _aspects(0, 6, planet)

    def test_mutual_aspect_is_bool(self, manish_chart: ChartData) -> None:
        result = compute_dasha_transit(manish_chart, _DATE)
        assert isinstance(result.md_ad_mutual_aspect, bool)


class TestOverallFavorability:
    """Tests for compute_overall_favorability."""

    def _make_lord(self, score: int) -> DashaLordTransit:
        return DashaLordTransit(
            lord="Jupiter",
            dasha_level="MD",
            natal_house=7,
            natal_sign_index=1,
            natal_dignity="neutral",
            transit_sign_index=0,
            transit_house_from_lagna=1,
            transit_house_from_moon=1,
            transit_house_from_natal=1,
            transit_dignity="neutral",
            is_retrograde_transit=False,
            bav_bindus=4,
            bav_strength="moderate",
            houses_owned=[7, 10],
            favorability="neutral",
            score=score,
        )

    def test_highly_favorable(self) -> None:
        result = compute_overall_favorability(
            self._make_lord(80),
            self._make_lord(70),
            "friends",
            2,
        )
        assert result == "highly_favorable"

    def test_difficult(self) -> None:
        result = compute_overall_favorability(
            self._make_lord(10),
            self._make_lord(10),
            "enemies",
            0,
        )
        assert result == "difficult"

    def test_friendship_bonus(self) -> None:
        md, ad = self._make_lord(50), self._make_lord(40)
        order = ["difficult", "challenging", "mixed", "favorable", "highly_favorable"]
        neutral = compute_overall_favorability(md, ad, "neutral", 0)
        friend = compute_overall_favorability(md, ad, "friends", 0)
        assert order.index(friend) >= order.index(neutral)

    def test_double_transit_bonus(self) -> None:
        md, ad = self._make_lord(50), self._make_lord(40)
        order = ["difficult", "challenging", "mixed", "favorable", "highly_favorable"]
        no_dt = compute_overall_favorability(md, ad, "neutral", 0)
        with_dt = compute_overall_favorability(md, ad, "neutral", 3)
        assert order.index(with_dt) >= order.index(no_dt)

    def test_enemy_penalty(self) -> None:
        md, ad = self._make_lord(50), self._make_lord(40)
        order = ["difficult", "challenging", "mixed", "favorable", "highly_favorable"]
        neutral = compute_overall_favorability(md, ad, "neutral", 0)
        enemy = compute_overall_favorability(md, ad, "enemies", 0)
        assert order.index(enemy) <= order.index(neutral)
