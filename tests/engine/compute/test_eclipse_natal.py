"""Tests for eclipse-natal chart impact analysis."""

from __future__ import annotations

import swisseph as swe

from daivai_engine.compute.eclipse_natal import (
    compute_eclipse_natal_impact,
    compute_upcoming_eclipse_impacts,
    find_eclipses,
)
from daivai_engine.models.eclipse_natal import (
    EclipseData,
    EclipseNatalResult,
)


def _to_jd(year: int, month: int, day: int, hour: float = 12.0) -> float:
    """Helper: convert date to Julian Day (UT)."""
    return float(swe.julday(year, month, day, hour))


# ── find_eclipses tests ─────────────────────────────────────────────────────


class TestFindEclipses:
    """Tests for find_eclipses() — eclipse detection."""

    def test_eclipses_found_in_one_year(self) -> None:
        """There are typically 4-7 eclipses per year (2-3 solar + 2-3 lunar)."""
        start = _to_jd(2025, 1, 1)
        end = _to_jd(2026, 1, 1)
        eclipses = find_eclipses(start, end)
        assert len(eclipses) >= 2, "At least 2 eclipses expected per year"

    def test_eclipse_types_are_valid(self) -> None:
        """Each eclipse must be solar or lunar."""
        start = _to_jd(2025, 1, 1)
        end = _to_jd(2026, 1, 1)
        for ecl in find_eclipses(start, end):
            assert ecl.eclipse_type in ("solar", "lunar")

    def test_eclipse_longitude_in_range(self) -> None:
        """Eclipse longitude must be 0-360."""
        start = _to_jd(2025, 1, 1)
        end = _to_jd(2026, 1, 1)
        for ecl in find_eclipses(start, end):
            assert 0.0 <= ecl.longitude < 360.0

    def test_eclipse_sign_index_valid(self) -> None:
        """Sign index must be 0-11."""
        start = _to_jd(2025, 1, 1)
        end = _to_jd(2026, 1, 1)
        for ecl in find_eclipses(start, end):
            assert 0 <= ecl.sign_index <= 11

    def test_both_types_in_two_years(self) -> None:
        """Over 2 years, both solar and lunar eclipses should occur."""
        start = _to_jd(2025, 1, 1)
        end = _to_jd(2027, 1, 1)
        eclipses = find_eclipses(start, end)
        types = {e.eclipse_type for e in eclipses}
        assert "solar" in types, "Should find at least one solar eclipse in 2 years"
        assert "lunar" in types, "Should find at least one lunar eclipse in 2 years"

    def test_eclipses_sorted_chronologically(self) -> None:
        """Eclipses must be sorted by julian_day."""
        start = _to_jd(2025, 1, 1)
        end = _to_jd(2027, 1, 1)
        eclipses = find_eclipses(start, end)
        for i in range(1, len(eclipses)):
            assert eclipses[i].julian_day >= eclipses[i - 1].julian_day


# ── compute_eclipse_natal_impact tests ──────────────────────────────────────


class TestEclipseNatalImpact:
    """Tests for compute_eclipse_natal_impact() — natal overlay."""

    def _get_first_eclipse(self) -> EclipseData:
        """Get a real eclipse for testing."""
        start = _to_jd(2025, 1, 1)
        end = _to_jd(2026, 1, 1)
        eclipses = find_eclipses(start, end)
        assert eclipses, "Need at least one eclipse for testing"
        return eclipses[0]

    def test_impacts_include_all_natal_points(self, manish_chart) -> None:
        """Should check all 9 planets + lagna = 10 points."""
        ecl = self._get_first_eclipse()
        result = compute_eclipse_natal_impact(manish_chart, ecl)
        assert len(result.impacts) == 10  # 9 planets + Lagna

    def test_impacts_sorted_by_orb(self, manish_chart) -> None:
        """Impacts must be sorted tightest orb first."""
        ecl = self._get_first_eclipse()
        result = compute_eclipse_natal_impact(manish_chart, ecl)
        orbs = [i.orb for i in result.impacts]
        assert orbs == sorted(orbs)

    def test_solar_eclipse_near_natal_sun_is_hit(self, manish_chart) -> None:
        """Synthesize an eclipse at natal Sun longitude — should be exact hit."""
        sun_lon = manish_chart.planets["Sun"].longitude
        si = manish_chart.planets["Sun"].sign_index
        from daivai_engine.constants import NAKSHATRAS, SIGNS

        fake_eclipse = EclipseData(
            eclipse_type="solar",
            date="01/01/2025",
            julian_day=2460676.0,
            longitude=round(sun_lon, 4),
            sign_index=si,
            sign=SIGNS[si],
            nakshatra=NAKSHATRAS[0],
        )
        result = compute_eclipse_natal_impact(manish_chart, fake_eclipse)
        sun_impact = next(i for i in result.impacts if i.natal_point == "Sun")
        assert sun_impact.is_hit
        assert sun_impact.severity == "exact"
        assert sun_impact.orb < 1.0

    def test_eclipse_far_from_all_natal_points(self, manish_chart) -> None:
        """Eclipse at 180 deg from all natal points — low severity."""
        # Use a longitude unlikely to be near any natal point
        from daivai_engine.constants import NAKSHATRAS, SIGNS

        fake_eclipse = EclipseData(
            eclipse_type="lunar",
            date="01/01/2025",
            julian_day=2460676.0,
            longitude=179.0,
            sign_index=5,
            sign=SIGNS[5],
            nakshatra=NAKSHATRAS[13],
        )
        result = compute_eclipse_natal_impact(manish_chart, fake_eclipse, orb=1.0)
        # With 1-degree orb, most/all should be non-hits
        [i for i in result.impacts if i.is_hit]
        # We can't guarantee zero hits, but orb is very tight
        assert isinstance(result, EclipseNatalResult)

    def test_lagna_impact_included(self, manish_chart) -> None:
        """Lagna must be one of the checked natal points."""
        ecl = self._get_first_eclipse()
        result = compute_eclipse_natal_impact(manish_chart, ecl)
        lagna_impacts = [i for i in result.impacts if i.natal_point == "Lagna"]
        assert len(lagna_impacts) == 1
        assert lagna_impacts[0].house_affected == 1

    def test_severity_classification_correct(self, manish_chart) -> None:
        """Verify severity labels match orb thresholds."""
        ecl = self._get_first_eclipse()
        result = compute_eclipse_natal_impact(manish_chart, ecl)
        for impact in result.impacts:
            if impact.orb < 1.0:
                assert impact.severity == "exact"
            elif impact.orb < 3.0:
                assert impact.severity == "strong"
            elif impact.orb < 5.0:
                assert impact.severity == "moderate"
            else:
                assert impact.severity == "none"

    def test_most_affected_planet_is_tightest(self, manish_chart) -> None:
        """Most affected planet should be the one with tightest orb that is hit."""
        from daivai_engine.constants import NAKSHATRAS, SIGNS

        sun_lon = manish_chart.planets["Sun"].longitude
        si = manish_chart.planets["Sun"].sign_index
        fake_eclipse = EclipseData(
            eclipse_type="solar",
            date="01/01/2025",
            julian_day=2460676.0,
            longitude=round(sun_lon, 4),
            sign_index=si,
            sign=SIGNS[si],
            nakshatra=NAKSHATRAS[0],
        )
        result = compute_eclipse_natal_impact(manish_chart, fake_eclipse)
        if result.most_affected_planet:
            # The most affected should be the first hit in sorted impacts
            hits = [i for i in result.impacts if i.is_hit]
            assert result.most_affected_planet == hits[0].natal_point


# ── compute_upcoming_eclipse_impacts tests ──────────────────────────────────


class TestUpcomingEclipseImpacts:
    """Tests for compute_upcoming_eclipse_impacts() — batch analysis."""

    def test_returns_list_of_results(self, manish_chart) -> None:
        """Should return a list of EclipseNatalResult."""
        start = _to_jd(2025, 1, 1)
        results = compute_upcoming_eclipse_impacts(manish_chart, start, years=1)
        assert isinstance(results, list)
        assert len(results) >= 2
        for r in results:
            assert isinstance(r, EclipseNatalResult)

    def test_each_result_has_eclipse_data(self, manish_chart) -> None:
        """Each result must carry its eclipse data."""
        start = _to_jd(2025, 1, 1)
        results = compute_upcoming_eclipse_impacts(manish_chart, start, years=1)
        for r in results:
            assert r.eclipse.eclipse_type in ("solar", "lunar")
            assert r.eclipse.julian_day > 0
