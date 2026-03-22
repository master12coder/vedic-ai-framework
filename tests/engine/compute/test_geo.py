"""Tests for geographic utilities — resolve_or_manual, GeoLocation."""

from __future__ import annotations

import pytest

from daivai_engine.compute.geo import GeoLocation, resolve_or_manual


class TestGeoLocation:
    """Tests for the GeoLocation Pydantic model."""

    def test_creation_with_valid_data(self) -> None:
        geo = GeoLocation(
            latitude=25.3176,
            longitude=83.0067,
            timezone_name="Asia/Kolkata",
            utc_offset_hours=5.5,
        )
        assert geo.latitude == 25.3176
        assert geo.longitude == 83.0067

    def test_model_is_frozen(self) -> None:
        geo = GeoLocation(
            latitude=25.3176,
            longitude=83.0067,
            timezone_name="Asia/Kolkata",
            utc_offset_hours=5.5,
        )
        with pytest.raises((TypeError, AttributeError, ValueError)):
            geo.latitude = 0.0  # type: ignore[misc]

    def test_utc_offset_stored(self) -> None:
        geo = GeoLocation(
            latitude=28.6139,
            longitude=77.2090,
            timezone_name="Asia/Kolkata",
            utc_offset_hours=5.5,
        )
        assert geo.utc_offset_hours == 5.5


class TestResolveOrManual:
    """Tests for resolve_or_manual() with manual lat/lon."""

    def test_manual_coordinates_varanasi(self) -> None:
        geo = resolve_or_manual(lat=25.3176, lon=83.0067, tz_name="Asia/Kolkata")
        assert geo.latitude == 25.3176
        assert geo.longitude == 83.0067

    def test_timezone_name_stored(self) -> None:
        geo = resolve_or_manual(lat=25.3176, lon=83.0067, tz_name="Asia/Kolkata")
        assert geo.timezone_name == "Asia/Kolkata"

    def test_utc_offset_for_ist(self) -> None:
        geo = resolve_or_manual(lat=25.3176, lon=83.0067, tz_name="Asia/Kolkata")
        assert abs(geo.utc_offset_hours - 5.5) < 0.01

    def test_utc_offset_for_utc(self) -> None:
        geo = resolve_or_manual(lat=51.5074, lon=-0.1278, tz_name="UTC")
        assert abs(geo.utc_offset_hours) < 0.01

    def test_returns_geo_location_model(self) -> None:
        geo = resolve_or_manual(lat=0.0, lon=0.0, tz_name="UTC")
        assert isinstance(geo, GeoLocation)

    def test_raises_without_place_or_coords(self) -> None:
        with pytest.raises(ValueError, match="Provide either"):
            resolve_or_manual()

    def test_delhi_coordinates(self) -> None:
        geo = resolve_or_manual(lat=28.6139, lon=77.2090, tz_name="Asia/Kolkata")
        assert abs(geo.latitude - 28.6139) < 0.001
        assert abs(geo.longitude - 77.2090) < 0.001

    def test_negative_longitude_western(self) -> None:
        geo = resolve_or_manual(lat=40.7128, lon=-74.0060, tz_name="America/New_York")
        assert geo.longitude < 0
