"""Place name -> lat/lon/timezone resolution with caching."""

from __future__ import annotations

import functools
from datetime import datetime

import pytz
from geopy.geocoders import Nominatim
from pydantic import BaseModel, ConfigDict
from timezonefinder import TimezoneFinder


class GeoLocation(BaseModel):
    """Resolved geographic coordinates and timezone for a place."""

    model_config = ConfigDict(frozen=True)

    latitude: float
    longitude: float
    timezone_name: str
    utc_offset_hours: float


_tf = TimezoneFinder()
_geocoder = Nominatim(user_agent="DaivAI", timeout=10)


@functools.lru_cache(maxsize=256)
def _resolve_place_coords(place_name: str) -> tuple[float, float, str]:
    """Geocode a place name and return (lat, lon, tz_name) — cached."""
    location = _geocoder.geocode(place_name)
    if location is None:
        raise ValueError(f"Could not geocode place: {place_name}")

    lat = location.latitude
    lon = location.longitude
    tz_name = _tf.timezone_at(lat=lat, lng=lon) or "Asia/Kolkata"
    return lat, lon, tz_name


def _utc_offset(tz_name: str, ref_date: datetime) -> float:
    """Return UTC offset in decimal hours for *tz_name* on *ref_date*.

    Using the actual reference date is critical for DST-affected timezones:
    a timezone like America/New_York is UTC-5 in winter but UTC-4 in summer.
    Passing the birth date avoids a systematic 1-hour error for summer births.

    Args:
        tz_name: IANA timezone identifier.
        ref_date: The date for which the offset is needed (usually birth date).

    Returns:
        Signed offset in decimal hours (e.g. 5.5 for IST, -4.0 for EDT).
    """
    tz = pytz.timezone(tz_name)
    offset = tz.utcoffset(ref_date)
    return offset.total_seconds() / 3600 if offset is not None else 0.0


def resolve_place(
    place_name: str,
    ref_date: datetime | None = None,
) -> GeoLocation:
    """Resolve a place name to coordinates, timezone, and UTC offset.

    Args:
        place_name: Human-readable place name (geocoded via Nominatim).
        ref_date: Reference date for DST-accurate UTC offset computation.
            Defaults to 2024-01-01 (standard time) if not provided.

    Returns:
        GeoLocation with coordinates, timezone name, and UTC offset.
    """
    lat, lon, tz_name = _resolve_place_coords(place_name)
    ref = ref_date if ref_date is not None else datetime(2024, 1, 1)
    utc_offset = _utc_offset(tz_name, ref)
    return GeoLocation(
        latitude=lat, longitude=lon, timezone_name=tz_name, utc_offset_hours=utc_offset
    )


def resolve_or_manual(
    place: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    tz_name: str = "Asia/Kolkata",
    ref_date: datetime | None = None,
) -> GeoLocation:
    """Resolve location from place name or manual lat/lon + timezone.

    Args:
        place: Human-readable place name. Takes priority over lat/lon.
        lat: Manual latitude (decimal degrees, -90 to 90).
        lon: Manual longitude (decimal degrees, -180 to 180).
        tz_name: IANA timezone name used when lat/lon given manually.
        ref_date: Reference date for DST-accurate UTC offset. Pass the birth
            date for correctness. Defaults to 2024-01-01 if omitted.

    Returns:
        GeoLocation with resolved coordinates and UTC offset.

    Raises:
        ValueError: If neither place name nor lat/lon are provided, or if
            the place name cannot be geocoded.
    """
    if place:
        return resolve_place(place, ref_date=ref_date)
    if lat is not None and lon is not None:
        ref = ref_date if ref_date is not None else datetime(2024, 1, 1)
        utc_offset = _utc_offset(tz_name, ref)
        return GeoLocation(
            latitude=lat, longitude=lon, timezone_name=tz_name, utc_offset_hours=utc_offset
        )
    raise ValueError("Provide either place name or lat/lon coordinates")
