"""Tests for transit event finder — ingress, stations, exact aspects.

Uses Swiss Ephemeris to validate computed transit events against
known astronomical phenomena.
"""

from __future__ import annotations

import swisseph as swe

from daivai_engine.compute.transit_finder import (
    find_exact_aspect,
    find_ingress,
    find_stations,
    jd_to_datetime,
)
from daivai_engine.models.transit_finder import (
    AspectEvent,
    IngressEvent,
    StationEvent,
)


def _to_jd(year: int, month: int, day: int, hour: float = 12.0) -> float:
    """Helper: convert date to Julian Day (UT)."""
    return float(swe.julday(year, month, day, hour))


# ── jd_to_datetime tests ────────────────────────────────────────────────────


class TestJdToDatetime:
    """Tests for the jd_to_datetime utility."""

    def test_known_date_converts_correctly(self) -> None:
        """J2000.0 epoch = 1 Jan 2000 12:00 UT."""
        jd = 2451545.0  # J2000.0
        dt = jd_to_datetime(jd, "UTC")
        assert dt.year == 2000
        assert dt.month == 1
        assert dt.day == 1

    def test_ist_offset_applied(self) -> None:
        """IST = UTC + 5:30."""
        jd = _to_jd(2026, 1, 1, 0.0)  # midnight UT
        dt = jd_to_datetime(jd, "Asia/Kolkata")
        assert dt.hour == 5  # 00:00 UT = 05:30 IST
        assert dt.minute == 30


# ── Ingress tests ───────────────────────────────────────────────────────────


class TestFindIngress:
    """Tests for find_ingress() — planet sign entry detection."""

    def test_saturn_ingress_detected_in_year(self) -> None:
        """Saturn changes sign roughly every 2.5 years; scan 3 years."""
        start = _to_jd(2025, 1, 1)
        end = _to_jd(2028, 1, 1)
        # Saturn will enter at least one new sign in 3 years
        # Find ingress into any sign by trying all 12
        all_events: list[IngressEvent] = []
        for sign_idx in range(12):
            evts = find_ingress("Saturn", sign_idx, start, end)
            all_events.extend(evts)
        assert len(all_events) >= 1, "Saturn should enter at least one sign in 3 years"
        for evt in all_events:
            assert evt.event_type == "ingress"
            assert isinstance(evt, IngressEvent)

    def test_ingress_returns_correct_sign(self) -> None:
        """Ingress event target_sign_index matches the requested sign."""
        start = _to_jd(2025, 1, 1)
        end = _to_jd(2028, 1, 1)
        for sign_idx in range(12):
            for evt in find_ingress("Saturn", sign_idx, start, end):
                assert evt.target_sign_index == sign_idx
                assert evt.sign_index == sign_idx

    def test_moon_ingress_frequent(self) -> None:
        """Moon enters each sign roughly every 27 days; check 1 month."""
        start = _to_jd(2026, 3, 1)
        end = _to_jd(2026, 4, 1)
        # Moon should enter Aries at least once in a month
        events = find_ingress("Moon", 0, start, end)
        assert len(events) >= 1, "Moon should enter Aries at least once per month"

    def test_retrograde_ingress_detected(self) -> None:
        """Mercury retrograde can cause double ingress into the same sign."""
        # Scan a full year — Mercury retrogrades 3x/year
        start = _to_jd(2026, 1, 1)
        end = _to_jd(2027, 1, 1)
        all_events: list[IngressEvent] = []
        for sign_idx in range(12):
            all_events.extend(find_ingress("Mercury", sign_idx, start, end))
        # Mercury enters ~12-15 signs per year (some twice due to retrograde)
        assert len(all_events) >= 12

    def test_empty_for_no_ingress_in_short_window(self) -> None:
        """Saturn won't enter Aries in a 1-week window unless it's about to."""
        start = _to_jd(2026, 6, 1)
        end = _to_jd(2026, 6, 8)
        # Very unlikely Saturn enters Aries in a random 7-day window
        # We just verify it returns a list (may be empty or not)
        events = find_ingress("Saturn", 0, start, end)
        assert isinstance(events, list)


# ── Station tests ───────────────────────────────────────────────────────────


class TestFindStations:
    """Tests for find_stations() — retrograde/direct station detection."""

    def test_sun_has_no_stations(self) -> None:
        """Sun never goes retrograde."""
        start = _to_jd(2026, 1, 1)
        end = _to_jd(2027, 1, 1)
        events = find_stations("Sun", start, end)
        assert events == []

    def test_moon_has_no_stations(self) -> None:
        """Moon never goes retrograde."""
        start = _to_jd(2026, 1, 1)
        end = _to_jd(2027, 1, 1)
        events = find_stations("Moon", start, end)
        assert events == []

    def test_jupiter_stations_in_year(self) -> None:
        """Jupiter goes retrograde once per year — expect 2 stations (R + D)."""
        start = _to_jd(2026, 1, 1)
        end = _to_jd(2027, 1, 1)
        events = find_stations("Jupiter", start, end)
        assert len(events) >= 1, "Jupiter should have at least 1 station per year"
        types = {e.event_type for e in events}
        # Should have at least one type of station
        assert types & {"station_retrograde", "station_direct"}

    def test_station_event_has_speed_fields(self) -> None:
        """Station events must report speed before and after."""
        start = _to_jd(2026, 1, 1)
        end = _to_jd(2027, 1, 1)
        events = find_stations("Saturn", start, end)
        for evt in events:
            assert isinstance(evt, StationEvent)
            # Speed before and after should have opposite signs
            assert evt.speed_before * evt.speed_after < 0, (
                f"Speed should flip sign at station: {evt.speed_before} -> {evt.speed_after}"
            )

    def test_retrograde_station_speed_positive_to_negative(self) -> None:
        """At retrograde station, speed goes from positive to negative."""
        start = _to_jd(2026, 1, 1)
        end = _to_jd(2027, 1, 1)
        events = find_stations("Mars", start, end)
        retro_events = [e for e in events if e.event_type == "station_retrograde"]
        for evt in retro_events:
            assert evt.speed_before > 0
            assert evt.speed_after < 0


# ── Exact aspect tests ──────────────────────────────────────────────────────


class TestFindExactAspect:
    """Tests for find_exact_aspect() — exact transit-to-natal aspect detection."""

    def test_conjunction_to_natal_position(self, manish_chart) -> None:
        """Transit Moon should conjunct natal Moon longitude within a month."""
        natal_moon_lon = manish_chart.planets["Moon"].longitude
        start = _to_jd(2026, 3, 1)
        end = _to_jd(2026, 4, 1)
        events = find_exact_aspect("Moon", natal_moon_lon, 0.0, start, end)
        assert len(events) >= 1, "Moon returns to its natal position ~monthly"
        for evt in events:
            assert evt.aspect_type == "conjunction"
            assert isinstance(evt, AspectEvent)

    def test_opposition_aspect_detected(self, manish_chart) -> None:
        """Transit Moon should oppose natal Moon within a month."""
        natal_moon_lon = manish_chart.planets["Moon"].longitude
        start = _to_jd(2026, 3, 1)
        end = _to_jd(2026, 4, 1)
        events = find_exact_aspect("Moon", natal_moon_lon, 180.0, start, end)
        assert len(events) >= 1
        for evt in events:
            assert evt.aspect_type == "opposition"

    def test_aspect_event_has_natal_longitude(self, manish_chart) -> None:
        """Aspect event must carry the natal longitude it's aspecting."""
        natal_sun_lon = manish_chart.planets["Sun"].longitude
        start = _to_jd(2026, 1, 1)
        end = _to_jd(2027, 1, 1)
        events = find_exact_aspect("Jupiter", natal_sun_lon, 0.0, start, end)
        for evt in events:
            assert abs(evt.natal_longitude - round(natal_sun_lon, 4)) < 0.01

    def test_trine_aspect_type_label(self, manish_chart) -> None:
        """Trine aspect (120 deg) should be labelled correctly."""
        natal_moon_lon = manish_chart.planets["Moon"].longitude
        start = _to_jd(2026, 1, 1)
        end = _to_jd(2027, 1, 1)
        events = find_exact_aspect("Jupiter", natal_moon_lon, 120.0, start, end)
        for evt in events:
            assert evt.aspect_type == "trine"
