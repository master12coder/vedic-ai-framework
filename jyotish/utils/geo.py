"""Place name -> lat/lon/timezone resolution with caching."""

from __future__ import annotations

import functools
from dataclasses import dataclass

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

import pytz


@dataclass(frozen=True)
class GeoLocation:
    """Resolved geographic coordinates and timezone for a place."""

    latitude: float
    longitude: float
    timezone_name: str
    utc_offset_hours: float


_tf = TimezoneFinder()
_geocoder = Nominatim(user_agent="vedic-ai-framework", timeout=10)


@functools.lru_cache(maxsize=256)
def resolve_place(place_name: str) -> GeoLocation:
    """Resolve a place name to coordinates and timezone."""
    location = _geocoder.geocode(place_name)
    if location is None:
        raise ValueError(f"Could not geocode place: {place_name}")

    lat = location.latitude
    lon = location.longitude
    tz_name = _tf.timezone_at(lat=lat, lng=lon)
    if tz_name is None:
        tz_name = "Asia/Kolkata"

    tz = pytz.timezone(tz_name)
    from datetime import datetime
    utc_offset = tz.utcoffset(datetime(2024, 1, 1)).total_seconds() / 3600  # type: ignore[union-attr]

    return GeoLocation(
        latitude=lat,
        longitude=lon,
        timezone_name=tz_name,
        utc_offset_hours=utc_offset,
    )


def resolve_or_manual(
    place: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    tz_name: str = "Asia/Kolkata",
) -> GeoLocation:
    """Resolve from place name or use manual coordinates."""
    if place:
        return resolve_place(place)
    if lat is not None and lon is not None:
        tz = pytz.timezone(tz_name)
        from datetime import datetime
        utc_offset = tz.utcoffset(datetime(2024, 1, 1)).total_seconds() / 3600  # type: ignore[union-attr]
        return GeoLocation(
            latitude=lat, longitude=lon,
            timezone_name=tz_name, utc_offset_hours=utc_offset,
        )
    raise ValueError("Provide either place name or lat/lon coordinates")
