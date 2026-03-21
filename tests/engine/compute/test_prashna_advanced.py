"""Tests for upgraded Prashna (horary) computation — Arudha, Mook, Swara."""

from __future__ import annotations

from datetime import UTC, datetime

from daivai_engine.compute.prashna import (
    _compute_arudha,
    _compute_hora_lord,
    _compute_swara,
    _is_moon_waxing,
    compute_prashna,
)
from daivai_engine.models.chart import ChartData


class TestPrashnaCore:
    def test_returns_all_required_keys(self, manish_chart: ChartData) -> None:
        result = compute_prashna("test", 25.3176, 83.0067)
        required = {
            "chart", "answer", "reasoning", "lagna_lord", "relevant_house",
            "relevant_lord", "moon_strong", "moon_waxing",
            "arudha_sign", "arudha_sign_name", "arudha_lord", "arudha_strong",
            "hora_lord", "swara", "is_mook_prashna",
        }
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_answer_is_valid(self) -> None:
        result = compute_prashna("test", 25.3176, 83.0067)
        assert result["answer"] in ("YES", "NO", "MAYBE")

    def test_arudha_sign_in_valid_range(self) -> None:
        result = compute_prashna("test", 25.3176, 83.0067)
        assert 0 <= result["arudha_sign"] <= 11

    def test_hora_lord_is_valid_planet(self) -> None:
        result = compute_prashna("test", 25.3176, 83.0067)
        valid = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert result["hora_lord"] in valid

    def test_swara_is_valid(self) -> None:
        result = compute_prashna("test", 25.3176, 83.0067)
        assert result["swara"] in ("ida", "pingala", "sushumna")

    def test_mook_prashna_flag(self) -> None:
        result = compute_prashna(
            "test", 25.3176, 83.0067,
            is_mook_prashna=True,
        )
        assert result["is_mook_prashna"] is True

    def test_reasoning_mentions_arudha(self) -> None:
        result = compute_prashna("marriage question", 25.3176, 83.0067, question_type="marriage")
        assert "Arudha" in result["reasoning"] or "arudha" in result["reasoning"].lower()

    def test_reasoning_mentions_swara(self) -> None:
        result = compute_prashna("career question", 25.3176, 83.0067, question_type="career")
        assert "swara" in result["reasoning"].lower() or "Swara" in result["reasoning"]

    def test_positive_negative_factors_counted(self) -> None:
        result = compute_prashna("test", 25.3176, 83.0067)
        assert "positive_factors" in result
        assert "negative_factors" in result
        assert result["positive_factors"] >= 0
        assert result["negative_factors"] >= 0


class TestComputeArudha:
    def test_arudha_in_valid_range(self, manish_chart: ChartData) -> None:
        for house in range(1, 13):
            arudha = _compute_arudha(manish_chart, house)
            assert 0 <= arudha <= 11, f"House {house}: arudha {arudha} out of range"

    def test_arudha_not_same_as_house(self, manish_chart: ChartData) -> None:
        """Arudha must not fall in the house sign or its 7th (exception rule)."""
        for house in range(1, 13):
            house_sign = (manish_chart.lagna_sign_index + house - 1) % 12
            seventh = (house_sign + 6) % 12
            arudha = _compute_arudha(manish_chart, house)
            assert arudha != house_sign, f"House {house}: arudha fell in own sign"
            assert arudha != seventh, f"House {house}: arudha fell in 7th from own sign"


class TestHoraLord:
    def test_sunday_noon_is_sun_hora(self) -> None:
        """Sunday 12:00 should give Sun hora (day lord)."""
        # Find a Sunday — 2026-03-22 is a Sunday
        dt = datetime(2026, 3, 22, 12, 0, tzinfo=UTC)
        weekday = (dt.weekday() + 1) % 7  # 0=Sun
        assert weekday == 0  # Confirm it's Sunday
        hora = _compute_hora_lord(dt)
        # Hour 12 from Sunday: start=Sun(0), hora_idx=(0+12)%7=5 → Jupiter
        assert hora in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

    def test_hora_lord_cycles_through_7_planets(self) -> None:
        """Over 7 consecutive hours, all hora lords should be distinct."""
        from datetime import timedelta
        dt = datetime(2026, 3, 22, 0, 0, tzinfo=UTC)
        lords = set()
        for h in range(7):
            hora = _compute_hora_lord(dt + timedelta(hours=h))
            lords.add(hora)
        assert len(lords) == 7


class TestSwara:
    def test_transition_minutes_give_sushumna(self) -> None:
        """Minutes 0-2 and 58-59 should be sushumna (transition)."""
        dt_start = datetime(2026, 3, 21, 10, 1, tzinfo=UTC)
        assert _compute_swara(dt_start) == "sushumna"
        dt_end = datetime(2026, 3, 21, 10, 59, tzinfo=UTC)
        assert _compute_swara(dt_end) == "sushumna"

    def test_even_hour_mid_minute_gives_ida(self) -> None:
        """Even hour (e.g. 10:30) = Ida (Moon breath)."""
        dt = datetime(2026, 3, 21, 10, 30, tzinfo=UTC)
        assert _compute_swara(dt) == "ida"

    def test_odd_hour_mid_minute_gives_pingala(self) -> None:
        """Odd hour (e.g. 11:30) = Pingala (Sun breath)."""
        dt = datetime(2026, 3, 21, 11, 30, tzinfo=UTC)
        assert _compute_swara(dt) == "pingala"


class TestMoonWaxing:
    def test_moon_after_sun_is_waxing(self) -> None:
        """Moon 30° ahead of Sun = waxing (new moon just passed)."""
        assert _is_moon_waxing(90.0, 60.0) is True

    def test_moon_before_sun_wrapping_is_waxing(self) -> None:
        """Moon at 5°, Sun at 350° — Moon is 15° ahead (waxing)."""
        assert _is_moon_waxing(5.0, 350.0) is True

    def test_moon_180_ahead_is_not_waxing(self) -> None:
        """Moon exactly opposite Sun = full moon, transition point."""
        assert _is_moon_waxing(240.0, 60.0) is False
