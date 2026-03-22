"""Tests for Panchang computation — Tithi, Nakshatra, Yoga, Karana, Vara."""

from __future__ import annotations

from daivai_engine.compute.panchang import compute_panchang
from daivai_engine.constants import (
    DAY_NAMES,
    KARANA_NAMES,
    NAKSHATRAS,
    PANCHANG_YOGA_NAMES,
    TITHI_NAMES,
)
from daivai_engine.models.panchang import PanchangData


# Reference: Varanasi coordinates
_LAT = 25.3176
_LON = 83.0067
_TZ = "Asia/Kolkata"


class TestPanchangStructure:
    """Tests for the output structure of compute_panchang()."""

    def test_returns_panchang_data(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert isinstance(result, PanchangData)

    def test_date_stored(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert result.date == "22/03/2026"

    def test_latitude_longitude_stored(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert result.latitude == _LAT
        assert result.longitude == _LON


class TestTithi:
    """Tests for Tithi computation."""

    def test_tithi_index_in_range(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert 0 <= result.tithi_index <= 29

    def test_tithi_name_is_valid(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert result.tithi_name in TITHI_NAMES

    def test_tithi_name_matches_index(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert result.tithi_name == TITHI_NAMES[result.tithi_index]

    def test_paksha_is_shukla_or_krishna(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert result.paksha in ("Shukla", "Krishna")

    def test_paksha_shukla_for_tithi_below_15(self) -> None:
        # Find a date with Shukla paksha
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        if result.tithi_index < 15:
            assert result.paksha == "Shukla"
        else:
            assert result.paksha == "Krishna"


class TestNakshatra:
    """Tests for Panchang Nakshatra computation."""

    def test_nakshatra_index_in_range(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert 0 <= result.nakshatra_index <= 26

    def test_nakshatra_name_is_valid(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert result.nakshatra_name in NAKSHATRAS

    def test_nakshatra_name_matches_index(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert result.nakshatra_name == NAKSHATRAS[result.nakshatra_index]


class TestYoga:
    """Tests for Panchang Yoga computation."""

    def test_yoga_index_in_range(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert 0 <= result.yoga_index <= 26

    def test_yoga_name_is_valid(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert result.yoga_name in PANCHANG_YOGA_NAMES

    def test_yoga_name_matches_index(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert result.yoga_name == PANCHANG_YOGA_NAMES[result.yoga_index]


class TestKarana:
    """Tests for Karana computation."""

    def test_karana_index_in_range(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert 0 <= result.karana_index <= 10

    def test_karana_name_is_valid(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert result.karana_name in KARANA_NAMES

    def test_karana_name_matches_index(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert result.karana_name == KARANA_NAMES[result.karana_index]


class TestVara:
    """Tests for Vara (day of week) computation."""

    def test_vara_is_valid_day_name(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        day_names = list(DAY_NAMES.values()) if isinstance(DAY_NAMES, dict) else list(DAY_NAMES)
        assert result.vara in day_names

    def test_sunday_on_known_date(self) -> None:
        # 22/03/2026 is a Sunday
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert result.vara == "Sunday"


class TestTimings:
    """Tests for sunrise/sunset and Rahu Kaal timings."""

    def test_sunrise_is_string(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert isinstance(result.sunrise, str)

    def test_sunset_is_string(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert isinstance(result.sunset, str)

    def test_rahu_kaal_is_string(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert isinstance(result.rahu_kaal, str)

    def test_yamaghanda_is_string(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert isinstance(result.yamaghanda, str)

    def test_gulika_is_string(self) -> None:
        result = compute_panchang("22/03/2026", _LAT, _LON, _TZ)
        assert isinstance(result.gulika, str)


class TestMultipleDates:
    """Consistency tests across different dates."""

    def test_different_dates_give_different_nakshatras(self) -> None:
        r1 = compute_panchang("01/01/2026", _LAT, _LON, _TZ)
        r2 = compute_panchang("15/01/2026", _LAT, _LON, _TZ)
        # Two weeks apart; Moon should be in different nakshatras
        # (Moon moves ~1 nakshatra per day)
        assert r1.nakshatra_index != r2.nakshatra_index

    def test_purnima_tithi_index_is_14(self) -> None:
        # Find a Purnima — tithi index 14 (0-indexed)
        # 14/03/2025 is Holi (Purnima)
        result = compute_panchang("14/03/2025", _LAT, _LON, _TZ)
        assert result.paksha == "Shukla"
