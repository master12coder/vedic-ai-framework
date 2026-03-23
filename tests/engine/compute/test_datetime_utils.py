"""Tests for datetime utility functions — IST, Julian Day, parse, sunrise."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

from daivai_engine.compute.datetime_utils import (
    compute_sunrise,
    compute_sunset,
    from_jd,
    now_ist,
    parse_birth_datetime,
    to_jd,
)


_IST = timezone(timedelta(hours=5, minutes=30))

# Known Julian Day for J2000.0 epoch
_J2000_JD = 2451545.0
_J2000_DT = datetime(2000, 1, 1, 12, 0, 0, tzinfo=UTC)


class TestToJd:
    """Tests for to_jd() — datetime → Julian Day."""

    def test_j2000_epoch_correct(self) -> None:
        jd = to_jd(_J2000_DT)
        assert abs(jd - _J2000_JD) < 0.001

    def test_returns_float(self) -> None:
        jd = to_jd(_J2000_DT)
        assert isinstance(jd, float)

    def test_jd_increases_with_time(self) -> None:
        dt1 = datetime(2020, 1, 1, tzinfo=UTC)
        dt2 = datetime(2020, 1, 2, tzinfo=UTC)
        assert to_jd(dt2) > to_jd(dt1)

    def test_difference_matches_days(self) -> None:
        dt1 = datetime(2020, 6, 1, 12, 0, tzinfo=UTC)
        dt2 = datetime(2020, 6, 11, 12, 0, tzinfo=UTC)
        diff = to_jd(dt2) - to_jd(dt1)
        assert abs(diff - 10.0) < 0.001


class TestFromJd:
    """Tests for from_jd() — Julian Day → datetime."""

    def test_j2000_epoch_roundtrip(self) -> None:
        dt = from_jd(_J2000_JD)
        assert dt.year == 2000
        assert dt.month == 1
        assert dt.day == 1

    def test_returns_utc_aware(self) -> None:
        dt = from_jd(_J2000_JD)
        assert dt.tzinfo == UTC

    def test_roundtrip_with_to_jd(self) -> None:
        original = datetime(2024, 6, 15, 10, 30, 0, tzinfo=UTC)
        jd = to_jd(original)
        recovered = from_jd(jd)
        diff = abs((recovered - original).total_seconds())
        assert diff < 2.0, f"Roundtrip diff: {diff}s"


class TestParseBirthDatetime:
    """Tests for parse_birth_datetime()."""

    def test_parses_manish_dob(self) -> None:
        dt = parse_birth_datetime("13/03/1989", "12:17", "Asia/Kolkata")
        assert dt.year == 1989
        assert dt.month == 3
        assert dt.day == 13
        assert dt.hour == 12
        assert dt.minute == 17

    def test_returns_timezone_aware(self) -> None:
        dt = parse_birth_datetime("01/01/2000", "06:00", "Asia/Kolkata")
        assert dt.tzinfo is not None

    def test_ist_timezone_offset(self) -> None:
        dt = parse_birth_datetime("01/01/2024", "12:00", "Asia/Kolkata")
        utc_dt = dt.astimezone(UTC)
        # IST is UTC+5:30, so 12:00 IST = 06:30 UTC
        assert utc_dt.hour == 6
        assert utc_dt.minute == 30

    def test_us_timezone_works(self) -> None:
        dt = parse_birth_datetime("01/06/2000", "12:00", "America/New_York")
        assert dt.year == 2000
        assert dt.month == 6

    def test_date_format_dd_mm_yyyy(self) -> None:
        dt = parse_birth_datetime("31/12/1999", "23:59", "Asia/Kolkata")
        assert dt.day == 31
        assert dt.month == 12
        assert dt.year == 1999

    def test_hhmmss_format_supported(self) -> None:
        """TOB with seconds (HH:MM:SS) must parse without error."""
        dt = parse_birth_datetime("13/03/1989", "12:17:45", "Asia/Kolkata")
        assert dt.hour == 12
        assert dt.minute == 17
        assert dt.second == 45

    def test_hhmmss_converts_to_utc_correctly(self) -> None:
        """HH:MM:SS birth time must produce the correct UTC value."""
        dt = parse_birth_datetime("01/01/2000", "06:30:30", "Asia/Kolkata")
        utc_dt = dt.astimezone(UTC)
        # 06:30:30 IST = 01:00:30 UTC
        assert utc_dt.hour == 1
        assert utc_dt.minute == 0
        assert utc_dt.second == 30

    def test_dst_ambiguous_time_returns_standard_time(self) -> None:
        """Fall-back DST: 01:30 AM repeated in US Eastern — must not raise, returns std time."""
        # US Eastern fall-back: 2:00 AM → 1:00 AM on first Sunday of November.
        # 2023-11-05 01:30 is ambiguous (exists in both EDT and EST).
        dt = parse_birth_datetime("05/11/2023", "01:30", "America/New_York")
        assert dt is not None
        assert dt.tzinfo is not None
        # Standard time (EST, UTC-5) means 01:30 EST = 06:30 UTC
        utc_dt = dt.astimezone(UTC)
        assert utc_dt.hour == 6
        assert utc_dt.minute == 30

    def test_dst_nonexistent_time_shifts_forward(self) -> None:
        """Spring-forward DST: 02:30 AM does not exist in US Eastern on spring-forward day."""
        # US Eastern spring-forward: 2:00 AM → 3:00 AM on second Sunday of March.
        # 2024-03-10 02:30 does not exist.
        dt = parse_birth_datetime("10/03/2024", "02:30", "America/New_York")
        assert dt is not None
        assert dt.tzinfo is not None
        # Should be shifted to 03:30 EDT (UTC-4) = 07:30 UTC
        utc_dt = dt.astimezone(UTC)
        assert utc_dt.hour == 7
        assert utc_dt.minute == 30


class TestNowIst:
    """Tests for now_ist()."""

    def test_returns_datetime_with_ist_tzinfo(self) -> None:
        dt = now_ist()
        assert dt.tzinfo is not None

    def test_year_is_current_era(self) -> None:
        dt = now_ist()
        assert dt.year >= 2024


class TestSunriseSunset:
    """Tests for compute_sunrise() and compute_sunset()."""

    def test_sunrise_returns_float(self) -> None:
        from daivai_engine.compute.datetime_utils import to_jd

        dt = datetime(2026, 3, 22, 12, 0, tzinfo=UTC)
        jd = to_jd(dt)
        sr = compute_sunrise(jd, 25.3176, 83.0067)
        assert isinstance(sr, float)

    def test_sunset_returns_float(self) -> None:
        from daivai_engine.compute.datetime_utils import to_jd

        dt = datetime(2026, 3, 22, 12, 0, tzinfo=UTC)
        jd = to_jd(dt)
        ss = compute_sunset(jd, 25.3176, 83.0067)
        assert isinstance(ss, float)

    def test_sunrise_before_sunset(self) -> None:
        from daivai_engine.compute.datetime_utils import to_jd

        dt = datetime(2026, 3, 22, 12, 0, tzinfo=UTC)
        jd = to_jd(dt)
        lat, lon = 25.3176, 83.0067
        sr = compute_sunrise(jd, lat, lon)
        ss = compute_sunset(jd, lat, lon)
        assert sr < ss

    def test_daylight_duration_reasonable(self) -> None:
        """Day length at equinox near equator should be ~12 hours."""
        from daivai_engine.compute.datetime_utils import to_jd

        # March equinox date
        dt = datetime(2026, 3, 20, 12, 0, tzinfo=UTC)
        jd = to_jd(dt)
        lat, lon = 25.3176, 83.0067
        sr = compute_sunrise(jd, lat, lon)
        ss = compute_sunset(jd, lat, lon)
        daylight_hours = (ss - sr) * 24
        assert 11.0 <= daylight_hours <= 13.0, f"Daylight: {daylight_hours:.1f}h"
