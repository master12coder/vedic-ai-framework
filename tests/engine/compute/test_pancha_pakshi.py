"""Comprehensive tests for Pancha Pakshi Shastra computation.

Tests cover:
  - Bird assignment for all 27 nakshatras x 2 pakshas
  - Classical Yama sequences for all 4 paksha/day-night combinations
  - Activity and strength values
  - Period boundary and contiguity
  - Sub-period rotation and coverage
  - Birth bird activity in each Yama (mathematical property)
  - Full compute functions (PanchaPakshiResult, PanchaPakshiDay)
  - Manish Chaurasia fixture (Rohini, Shukla → Vulture birth bird)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from daivai_engine.compute.pancha_pakshi import (
    _birth_bird_activity_in_yama,
    _build_periods,
    _find_sub_period,
    compute_pancha_pakshi,
    compute_pancha_pakshi_day,
    get_birth_bird,
    get_yama_sequence,
)
from daivai_engine.models.pancha_pakshi import (
    ACTIVITY_STRENGTH,
    Activity,
    Bird,
    PanchaPakshiDay,
    PanchaPakshiPeriod,
    PanchaPakshiResult,
)


IST = timezone(timedelta(hours=5, minutes=30))
# Varanasi coordinates (Manish's birthplace)
LAT = 25.3176
LON = 83.0067
# Fixed midday for deterministic tests
NOON_IST = datetime(2024, 3, 20, 12, 0, 0, tzinfo=IST)
MIDNIGHT_IST = datetime(2024, 3, 20, 0, 30, 0, tzinfo=IST)  # pre-dawn night


# ---------------------------------------------------------------------------
# Bird assignment -- all 27 nakshatras x 2 pakshas
# ---------------------------------------------------------------------------
class TestBirdAssignment:
    @pytest.mark.parametrize("nak", range(5))
    def test_nakshatras_0_to_4_shukla_are_vulture(self, nak: int) -> None:
        assert get_birth_bird(nak, "Shukla") == Bird.VULTURE

    @pytest.mark.parametrize("nak", range(5, 11))
    def test_nakshatras_5_to_10_shukla_are_owl(self, nak: int) -> None:
        assert get_birth_bird(nak, "Shukla") == Bird.OWL

    @pytest.mark.parametrize("nak", range(11, 16))
    def test_nakshatras_11_to_15_shukla_are_crow(self, nak: int) -> None:
        assert get_birth_bird(nak, "Shukla") == Bird.CROW

    @pytest.mark.parametrize("nak", range(16, 22))
    def test_nakshatras_16_to_21_shukla_are_cock(self, nak: int) -> None:
        assert get_birth_bird(nak, "Shukla") == Bird.COCK

    @pytest.mark.parametrize("nak", range(22, 27))
    def test_nakshatras_22_to_26_shukla_are_peacock(self, nak: int) -> None:
        assert get_birth_bird(nak, "Shukla") == Bird.PEACOCK

    @pytest.mark.parametrize("nak", range(5))
    def test_nakshatras_0_to_4_krishna_are_peacock(self, nak: int) -> None:
        assert get_birth_bird(nak, "Krishna") == Bird.PEACOCK

    @pytest.mark.parametrize("nak", range(5, 11))
    def test_nakshatras_5_to_10_krishna_are_cock(self, nak: int) -> None:
        assert get_birth_bird(nak, "Krishna") == Bird.COCK

    @pytest.mark.parametrize("nak", range(11, 16))
    def test_nakshatras_11_to_15_krishna_are_crow(self, nak: int) -> None:
        assert get_birth_bird(nak, "Krishna") == Bird.CROW

    @pytest.mark.parametrize("nak", range(16, 22))
    def test_nakshatras_16_to_21_krishna_are_owl(self, nak: int) -> None:
        assert get_birth_bird(nak, "Krishna") == Bird.OWL

    @pytest.mark.parametrize("nak", range(22, 27))
    def test_nakshatras_22_to_26_krishna_are_vulture(self, nak: int) -> None:
        assert get_birth_bird(nak, "Krishna") == Bird.VULTURE

    def test_rohini_shukla_is_vulture(self) -> None:
        """Rohini (index 3) Shukla → Vulture. Manish Chaurasia's birth bird."""
        assert get_birth_bird(3, "Shukla") == Bird.VULTURE

    def test_rohini_krishna_is_peacock(self) -> None:
        """Rohini (index 3) Krishna → Peacock (paksha reversal)."""
        assert get_birth_bird(3, "Krishna") == Bird.PEACOCK

    def test_all_27_nakshatras_mapped_shukla(self) -> None:
        """Every nakshatra (0-26) returns a valid Bird in Shukla."""
        for i in range(27):
            bird = get_birth_bird(i, "Shukla")
            assert isinstance(bird, Bird)

    def test_all_27_nakshatras_mapped_krishna(self) -> None:
        """Every nakshatra (0-26) returns a valid Bird in Krishna."""
        for i in range(27):
            bird = get_birth_bird(i, "Krishna")
            assert isinstance(bird, Bird)

    def test_crow_invariant_across_paksha(self) -> None:
        """Nakshatras 11-15 map to Crow in both Shukla and Krishna."""
        for nak in range(11, 16):
            assert get_birth_bird(nak, "Shukla") == Bird.CROW
            assert get_birth_bird(nak, "Krishna") == Bird.CROW


# ---------------------------------------------------------------------------
# Yama sequences — classical ordering for all 4 combinations
# ---------------------------------------------------------------------------
class TestYamaSequences:
    def test_shukla_day_sequence(self) -> None:
        seq = get_yama_sequence("Shukla", is_day=True)
        assert seq == [Bird.VULTURE, Bird.OWL, Bird.CROW, Bird.COCK, Bird.PEACOCK]

    def test_shukla_night_sequence(self) -> None:
        seq = get_yama_sequence("Shukla", is_day=False)
        assert seq == [Bird.VULTURE, Bird.PEACOCK, Bird.COCK, Bird.CROW, Bird.OWL]

    def test_krishna_day_sequence(self) -> None:
        seq = get_yama_sequence("Krishna", is_day=True)
        assert seq == [Bird.VULTURE, Bird.CROW, Bird.PEACOCK, Bird.OWL, Bird.COCK]

    def test_krishna_night_sequence(self) -> None:
        seq = get_yama_sequence("Krishna", is_day=False)
        assert seq == [Bird.VULTURE, Bird.COCK, Bird.OWL, Bird.PEACOCK, Bird.CROW]

    def test_all_sequences_have_5_birds(self) -> None:
        for paksha in ("Shukla", "Krishna"):
            for is_day in (True, False):
                seq = get_yama_sequence(paksha, is_day)
                assert len(seq) == 5

    def test_all_sequences_contain_each_bird_once(self) -> None:
        for paksha in ("Shukla", "Krishna"):
            for is_day in (True, False):
                seq = get_yama_sequence(paksha, is_day)
                assert set(seq) == set(Bird)

    def test_vulture_always_yama1(self) -> None:
        """Classical invariant: Vulture governs Yama 1 in all sequences."""
        for paksha in ("Shukla", "Krishna"):
            for is_day in (True, False):
                seq = get_yama_sequence(paksha, is_day)
                assert seq[0] == Bird.VULTURE


# ---------------------------------------------------------------------------
# Activity strengths
# ---------------------------------------------------------------------------
class TestActivityStrengths:
    def test_rule_strength_is_1(self) -> None:
        assert ACTIVITY_STRENGTH[Activity.RULE] == 1.0

    def test_eat_strength_is_075(self) -> None:
        assert ACTIVITY_STRENGTH[Activity.EAT] == 0.75

    def test_walk_strength_is_05(self) -> None:
        assert ACTIVITY_STRENGTH[Activity.WALK] == 0.5

    def test_sleep_strength_is_025(self) -> None:
        assert ACTIVITY_STRENGTH[Activity.SLEEP] == 0.25

    def test_die_strength_is_0(self) -> None:
        assert ACTIVITY_STRENGTH[Activity.DIE] == 0.0

    def test_strengths_are_monotone_decreasing(self) -> None:
        acts = [Activity.RULE, Activity.EAT, Activity.WALK, Activity.SLEEP, Activity.DIE]
        strengths = [ACTIVITY_STRENGTH[a] for a in acts]
        assert strengths == sorted(strengths, reverse=True)


# ---------------------------------------------------------------------------
# Period building (Yama structure)
# ---------------------------------------------------------------------------
class TestBuildPeriods:
    def _make_day_window(self) -> tuple[datetime, datetime, list[Bird]]:
        from datetime import UTC

        sunrise = datetime(2024, 3, 20, 1, 0, tzinfo=UTC)   # 06:30 IST
        sunset = datetime(2024, 3, 20, 13, 0, tzinfo=UTC)   # 18:30 IST (12 hr day)
        seq = get_yama_sequence("Shukla", is_day=True)
        return sunrise, sunset, seq

    def test_exactly_5_periods(self) -> None:
        sunrise, sunset, seq = self._make_day_window()
        periods = _build_periods(sunrise, sunset, seq, is_day=True)
        assert len(periods) == 5

    def test_first_period_starts_at_sunrise(self) -> None:
        sunrise, sunset, seq = self._make_day_window()
        periods = _build_periods(sunrise, sunset, seq, is_day=True)
        assert periods[0].start_time == sunrise

    def test_last_period_ends_at_sunset(self) -> None:
        sunrise, sunset, seq = self._make_day_window()
        periods = _build_periods(sunrise, sunset, seq, is_day=True)
        assert periods[-1].end_time == sunset

    def test_periods_are_contiguous(self) -> None:
        sunrise, sunset, seq = self._make_day_window()
        periods = _build_periods(sunrise, sunset, seq, is_day=True)
        for i in range(4):
            assert periods[i].end_time == periods[i + 1].start_time

    def test_all_periods_equal_duration(self) -> None:
        sunrise, sunset, seq = self._make_day_window()
        periods = _build_periods(sunrise, sunset, seq, is_day=True)
        durations = [(p.end_time - p.start_time).total_seconds() for p in periods]
        assert all(abs(d - durations[0]) < 1e-6 for d in durations)

    def test_yama_indices_1_to_5(self) -> None:
        sunrise, sunset, seq = self._make_day_window()
        periods = _build_periods(sunrise, sunset, seq, is_day=True)
        assert [p.yama_index for p in periods] == [1, 2, 3, 4, 5]

    def test_activity_sequence_rule_eat_walk_sleep_die(self) -> None:
        sunrise, sunset, seq = self._make_day_window()
        periods = _build_periods(sunrise, sunset, seq, is_day=True)
        acts = [p.activity for p in periods]
        assert acts == [Activity.RULE, Activity.EAT, Activity.WALK, Activity.SLEEP, Activity.DIE]

    def test_strength_decreasing_across_yamas(self) -> None:
        sunrise, sunset, seq = self._make_day_window()
        periods = _build_periods(sunrise, sunset, seq, is_day=True)
        strengths = [p.strength for p in periods]
        assert strengths == sorted(strengths, reverse=True)

    def test_bird_sequence_matches_shukla_day(self) -> None:
        sunrise, sunset, seq = self._make_day_window()
        periods = _build_periods(sunrise, sunset, seq, is_day=True)
        birds = [p.bird for p in periods]
        assert birds == [Bird.VULTURE, Bird.OWL, Bird.CROW, Bird.COCK, Bird.PEACOCK]


# ---------------------------------------------------------------------------
# Sub-period rotation
# ---------------------------------------------------------------------------
class TestSubPeriods:
    def _make_period(self) -> tuple[PanchaPakshiPeriod, list[Bird]]:
        from datetime import UTC

        start = datetime(2024, 3, 20, 1, 0, tzinfo=UTC)
        end = datetime(2024, 3, 20, 3, 24, tzinfo=UTC)   # 2h24m = 144min Yama
        seq = get_yama_sequence("Shukla", is_day=True)
        period = PanchaPakshiPeriod(
            yama_index=1, bird=Bird.VULTURE, activity=Activity.RULE,
            strength=1.0, start_time=start, end_time=end, is_daytime=True,
        )
        return period, seq

    def test_sub_period_index_in_1_to_5(self) -> None:
        period, seq = self._make_period()
        # Test at start of Yama → sub-period 1
        _, _, _, _, _, sub_idx = _find_sub_period(period, seq, period.start_time)
        assert sub_idx == 1

    def test_sub_birds_cover_all_5_birds(self) -> None:
        """All 5 birds appear exactly once as sub-birds within a Yama."""
        period, seq = self._make_period()
        total_secs = (period.end_time - period.start_time).total_seconds()
        sub_secs = total_secs / 5.0
        seen_birds: set[Bird] = set()
        for i in range(5):
            t = period.start_time + timedelta(seconds=i * sub_secs + 1)
            bird, _, _, _, _, _ = _find_sub_period(period, seq, t)
            seen_birds.add(bird)
        assert seen_birds == set(Bird)

    def test_first_sub_bird_is_yama_bird(self) -> None:
        """Sub-rotation starts from the Yama's own bird (Vulture in Yama 1)."""
        period, seq = self._make_period()
        bird, _, _, _, _, _ = _find_sub_period(period, seq, period.start_time)
        assert bird == Bird.VULTURE

    def test_first_sub_activity_is_rule(self) -> None:
        period, seq = self._make_period()
        _, act, _, _, _, _ = _find_sub_period(period, seq, period.start_time)
        assert act == Activity.RULE

    def test_sub_period_within_yama_bounds(self) -> None:
        period, seq = self._make_period()
        mid = period.start_time + (period.end_time - period.start_time) / 2
        _, _, _, sub_start, sub_end, _ = _find_sub_period(period, seq, mid)
        assert period.start_time <= sub_start
        assert sub_end <= period.end_time


# ---------------------------------------------------------------------------
# Birth bird activity in each Yama (mathematical property test)
# ---------------------------------------------------------------------------
class TestBirthBirdActivityInYama:
    def test_vulture_rules_in_yama1_all_sequences(self) -> None:
        """Vulture always Rules in Yama 1 (it IS the Yama 1 bird)."""
        for paksha in ("Shukla", "Krishna"):
            for is_day in (True, False):
                seq = get_yama_sequence(paksha, is_day)
                act, strength = _birth_bird_activity_in_yama(Bird.VULTURE, seq[0], seq)
                assert act == Activity.RULE
                assert strength == 1.0

    def test_birth_bird_dies_in_yama2(self) -> None:
        """Vulture (position 0) is at sub-position 4 in Yama 2 → Dies."""
        seq = get_yama_sequence("Shukla", is_day=True)
        act, strength = _birth_bird_activity_in_yama(Bird.VULTURE, seq[1], seq)
        assert act == Activity.DIE
        assert strength == 0.0

    def test_all_5_activities_covered_across_yamas(self) -> None:
        """Each bird performs all 5 activities exactly once per day/night."""
        for paksha in ("Shukla", "Krishna"):
            for is_day in (True, False):
                seq = get_yama_sequence(paksha, is_day)
                for birth_bird in Bird:
                    activities = {
                        _birth_bird_activity_in_yama(birth_bird, yama_bird, seq)[0]
                        for yama_bird in seq
                    }
                    assert activities == set(Activity), (
                        f"{birth_bird} missing activities in {paksha} {'day' if is_day else 'night'}"
                    )


# ---------------------------------------------------------------------------
# Manish Chaurasia fixture (Rohini, Shukla → Vulture)
# ---------------------------------------------------------------------------
class TestManishChart:
    def test_manish_moon_is_rohini(self, manish_chart) -> None:
        """Verify Manish's Moon nakshatra index is 3 (Rohini)."""
        assert manish_chart.planets["Moon"].nakshatra_index == 3

    def test_manish_birth_bird_is_vulture(self, manish_chart) -> None:
        """Rohini Shukla → Vulture (Manish Chaurasia's birth bird)."""
        moon_nak = manish_chart.planets["Moon"].nakshatra_index
        bird = get_birth_bird(moon_nak, "Shukla")
        assert bird == Bird.VULTURE

    def test_manish_birth_bird_krishna_would_be_peacock(self, manish_chart) -> None:
        """If Manish were Krishna paksha (counter-factual), bird = Peacock."""
        moon_nak = manish_chart.planets["Moon"].nakshatra_index
        bird = get_birth_bird(moon_nak, "Krishna")
        assert bird == Bird.PEACOCK


# ---------------------------------------------------------------------------
# Full compute_pancha_pakshi function
# ---------------------------------------------------------------------------
class TestComputePanchaPakshi:
    def test_returns_pancha_pakshi_result(self, manish_chart) -> None:
        result = compute_pancha_pakshi(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            NOON_IST,
            "Shukla",
            LAT,
            LON,
        )
        assert isinstance(result, PanchaPakshiResult)

    def test_birth_bird_is_vulture(self, manish_chart) -> None:
        result = compute_pancha_pakshi(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            NOON_IST,
            "Shukla",
            LAT,
            LON,
        )
        assert result.birth_bird == Bird.VULTURE

    def test_birth_nakshatra_is_rohini(self, manish_chart) -> None:
        result = compute_pancha_pakshi(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            NOON_IST,
            "Shukla",
            LAT,
            LON,
        )
        assert result.birth_nakshatra == "Rohini"

    def test_noon_is_daytime(self, manish_chart) -> None:
        result = compute_pancha_pakshi(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            NOON_IST,
            "Shukla",
            LAT,
            LON,
        )
        assert result.is_daytime is True

    def test_midnight_is_nighttime(self, manish_chart) -> None:
        result = compute_pancha_pakshi(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            MIDNIGHT_IST,
            "Shukla",
            LAT,
            LON,
        )
        assert result.is_daytime is False

    def test_period_times_ordered(self, manish_chart) -> None:
        result = compute_pancha_pakshi(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            NOON_IST,
            "Shukla",
            LAT,
            LON,
        )
        assert result.period_start < result.period_end

    def test_sub_period_within_main_period(self, manish_chart) -> None:
        result = compute_pancha_pakshi(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            NOON_IST,
            "Shukla",
            LAT,
            LON,
        )
        assert result.period_start <= result.sub_period_start
        assert result.sub_period_end <= result.period_end

    def test_birth_bird_strength_is_valid(self, manish_chart) -> None:
        result = compute_pancha_pakshi(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            NOON_IST,
            "Shukla",
            LAT,
            LON,
        )
        assert result.birth_bird_strength in {0.0, 0.25, 0.5, 0.75, 1.0}

    def test_yama_index_in_1_to_5(self, manish_chart) -> None:
        result = compute_pancha_pakshi(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            NOON_IST,
            "Shukla",
            LAT,
            LON,
        )
        assert 1 <= result.yama_index <= 5

    def test_sub_index_in_1_to_5(self, manish_chart) -> None:
        result = compute_pancha_pakshi(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            NOON_IST,
            "Shukla",
            LAT,
            LON,
        )
        assert 1 <= result.sub_index <= 5

    def test_query_dt_preserved(self, manish_chart) -> None:
        result = compute_pancha_pakshi(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            NOON_IST,
            "Shukla",
            LAT,
            LON,
        )
        assert result.query_dt == NOON_IST


# ---------------------------------------------------------------------------
# Full day breakdown
# ---------------------------------------------------------------------------
class TestComputePanchaPakshiDay:
    def test_returns_pancha_pakshi_day(self, manish_chart) -> None:
        result = compute_pancha_pakshi_day(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            "20/03/2024",
            "Shukla",
            LAT,
            LON,
        )
        assert isinstance(result, PanchaPakshiDay)

    def test_exactly_5_day_periods(self, manish_chart) -> None:
        result = compute_pancha_pakshi_day(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            "20/03/2024",
            "Shukla",
            LAT,
            LON,
        )
        assert len(result.day_periods) == 5

    def test_exactly_5_night_periods(self, manish_chart) -> None:
        result = compute_pancha_pakshi_day(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            "20/03/2024",
            "Shukla",
            LAT,
            LON,
        )
        assert len(result.night_periods) == 5

    def test_day_begins_at_sunrise(self, manish_chart) -> None:
        result = compute_pancha_pakshi_day(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            "20/03/2024",
            "Shukla",
            LAT,
            LON,
        )
        assert result.day_periods[0].start_time == result.sunrise

    def test_night_begins_at_sunset(self, manish_chart) -> None:
        result = compute_pancha_pakshi_day(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            "20/03/2024",
            "Shukla",
            LAT,
            LON,
        )
        assert result.night_periods[0].start_time == result.sunset

    def test_day_periods_contiguous(self, manish_chart) -> None:
        result = compute_pancha_pakshi_day(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            "20/03/2024",
            "Shukla",
            LAT,
            LON,
        )
        for i in range(4):
            assert result.day_periods[i].end_time == result.day_periods[i + 1].start_time

    def test_birth_bird_is_vulture(self, manish_chart) -> None:
        result = compute_pancha_pakshi_day(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            "20/03/2024",
            "Shukla",
            LAT,
            LON,
        )
        assert result.birth_bird == Bird.VULTURE

    def test_date_formatted_correctly(self, manish_chart) -> None:
        result = compute_pancha_pakshi_day(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            "20/03/2024",
            "Shukla",
            LAT,
            LON,
        )
        assert result.date == "2024-03-20"

    def test_sunrise_before_sunset(self, manish_chart) -> None:
        result = compute_pancha_pakshi_day(
            manish_chart.planets["Moon"].nakshatra_index,
            "Shukla",
            "20/03/2024",
            "Shukla",
            LAT,
            LON,
        )
        assert result.sunrise < result.sunset
