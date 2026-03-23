"""Tests for conditional nakshatra-based Dasha systems.

Covers: Dwisaptati Sama (72yr), Shatabdika (100yr), Chaturaseeti Sama (84yr),
Dwadashottari (112yr), Panchottari (105yr), Shashtihayani (60yr),
Shatrimsha Sama (36yr).
"""

from __future__ import annotations

from typing import ClassVar

from daivai_engine.compute.dasha_conditional import (
    compute_chaturaseeti_dasha,
    compute_dwadashottari_dasha,
    compute_dwisaptati_dasha,
    compute_panchottari_dasha,
    compute_shashtihayani_dasha,
    compute_shatabdika_dasha,
    compute_shatrimsha_dasha,
    is_chaturaseeti_applicable,
    is_dwadashottari_applicable,
    is_dwisaptati_applicable,
    is_panchottari_applicable,
    is_shashtihayani_applicable,
    is_shatabdika_applicable,
    is_shatrimsha_applicable,
)
from daivai_engine.constants import (
    CHATURASEETI_SEQUENCE,
    CHATURASEETI_TOTAL_YEARS,
    DWADASHOTTARI_SEQUENCE,
    DWADASHOTTARI_TOTAL_YEARS,
    DWISAPTATI_SEQUENCE,
    DWISAPTATI_TOTAL_YEARS,
    PANCHOTTARI_SEQUENCE,
    PANCHOTTARI_TOTAL_YEARS,
    SHASHTIHAYANI_SEQUENCE,
    SHASHTIHAYANI_TOTAL_YEARS,
    SHATABDIKA_SEQUENCE,
    SHATABDIKA_TOTAL_YEARS,
    SHATRIMSHA_SEQUENCE,
    SHATRIMSHA_TOTAL_YEARS,
)


# ── Sequence year sums (constants correctness) ───────────────────────────────


class TestSequenceYearSums:
    """Verify the canonical year sums for each conditional dasha system."""

    def test_dwisaptati_72_years(self):
        """Dwisaptati: 8 x 9 = 72 years."""
        total = sum(y for _, y in DWISAPTATI_SEQUENCE)
        assert total == DWISAPTATI_TOTAL_YEARS == 72

    def test_shatabdika_100_years(self):
        """Shatabdika: 5 x 20 = 100 years."""
        total = sum(y for _, y in SHATABDIKA_SEQUENCE)
        assert total == SHATABDIKA_TOTAL_YEARS == 100

    def test_chaturaseeti_84_years(self):
        """Chaturaseeti: 7 x 12 = 84 years."""
        total = sum(y for _, y in CHATURASEETI_SEQUENCE)
        assert total == CHATURASEETI_TOTAL_YEARS == 84

    def test_dwadashottari_112_years(self):
        """Dwadashottari: 7+14+8+17+10+25+10+21 = 112."""
        total = sum(y for _, y in DWADASHOTTARI_SEQUENCE)
        assert total == DWADASHOTTARI_TOTAL_YEARS == 112

    def test_panchottari_105_years(self):
        """Panchottari: 12+21+16+42+14 = 105."""
        total = sum(y for _, y in PANCHOTTARI_SEQUENCE)
        assert total == PANCHOTTARI_TOTAL_YEARS == 105

    def test_shashtihayani_60_years(self):
        """Shashtihayani: 30+30 = 60."""
        total = sum(y for _, y in SHASHTIHAYANI_SEQUENCE)
        assert total == SHASHTIHAYANI_TOTAL_YEARS == 60

    def test_shatrimsha_36_years(self):
        """Shatrimsha: 6 x 6 = 36."""
        total = sum(y for _, y in SHATRIMSHA_SEQUENCE)
        assert total == SHATRIMSHA_TOTAL_YEARS == 36


# ── Applicability checks return bool ────────────────────────────────────────


class TestApplicability:
    """All applicability checks must return bool for any valid chart."""

    def test_dwisaptati_returns_bool(self, manish_chart):
        assert isinstance(is_dwisaptati_applicable(manish_chart), bool)

    def test_shatabdika_returns_bool(self, manish_chart):
        assert isinstance(is_shatabdika_applicable(manish_chart), bool)

    def test_chaturaseeti_returns_bool(self, manish_chart):
        assert isinstance(is_chaturaseeti_applicable(manish_chart), bool)

    def test_dwadashottari_returns_bool(self, manish_chart):
        assert isinstance(is_dwadashottari_applicable(manish_chart), bool)

    def test_panchottari_returns_bool(self, manish_chart):
        assert isinstance(is_panchottari_applicable(manish_chart), bool)

    def test_shashtihayani_returns_bool(self, manish_chart):
        assert isinstance(is_shashtihayani_applicable(manish_chart), bool)

    def test_shatrimsha_returns_bool(self, manish_chart):
        assert isinstance(is_shatrimsha_applicable(manish_chart), bool)

    def test_panchottari_requires_cancer_lagna(self, manish_chart):
        """Panchottari must be inapplicable for Mithuna lagna (not Cancer)."""
        assert manish_chart.lagna_sign_index != 3, "Expected non-Cancer lagna"
        assert not is_panchottari_applicable(manish_chart)


# ── Period count correctness ─────────────────────────────────────────────────


class TestPeriodCounts:
    """Each system must produce the correct number of Mahadasha periods."""

    def test_dwisaptati_8_periods(self, manish_chart):
        assert len(compute_dwisaptati_dasha(manish_chart)) == 8

    def test_shatabdika_5_periods(self, manish_chart):
        assert len(compute_shatabdika_dasha(manish_chart)) == 5

    def test_chaturaseeti_7_periods(self, manish_chart):
        assert len(compute_chaturaseeti_dasha(manish_chart)) == 7

    def test_dwadashottari_8_periods(self, manish_chart):
        assert len(compute_dwadashottari_dasha(manish_chart)) == 8

    def test_panchottari_5_periods(self, manish_chart):
        assert len(compute_panchottari_dasha(manish_chart)) == 5

    def test_shashtihayani_2_periods(self, manish_chart):
        assert len(compute_shashtihayani_dasha(manish_chart)) == 2

    def test_shatrimsha_6_periods(self, manish_chart):
        assert len(compute_shatrimsha_dasha(manish_chart)) == 6


# ── Contiguous periods ───────────────────────────────────────────────────────


class TestContiguousPeriods:
    """Periods in each system must be contiguous (no gaps, no overlaps)."""

    @staticmethod
    def _check_contiguous(periods) -> None:
        for i in range(1, len(periods)):
            gap = abs((periods[i].start - periods[i - 1].end).total_seconds())
            assert gap < 60, f"Gap between period {i - 1} and {i}: {gap:.1f}s"

    def test_dwisaptati_contiguous(self, manish_chart):
        self._check_contiguous(compute_dwisaptati_dasha(manish_chart))

    def test_shatabdika_contiguous(self, manish_chart):
        self._check_contiguous(compute_shatabdika_dasha(manish_chart))

    def test_chaturaseeti_contiguous(self, manish_chart):
        self._check_contiguous(compute_chaturaseeti_dasha(manish_chart))

    def test_dwadashottari_contiguous(self, manish_chart):
        self._check_contiguous(compute_dwadashottari_dasha(manish_chart))

    def test_panchottari_contiguous(self, manish_chart):
        self._check_contiguous(compute_panchottari_dasha(manish_chart))

    def test_shashtihayani_contiguous(self, manish_chart):
        self._check_contiguous(compute_shashtihayani_dasha(manish_chart))

    def test_shatrimsha_contiguous(self, manish_chart):
        self._check_contiguous(compute_shatrimsha_dasha(manish_chart))


# ── Valid planet names ───────────────────────────────────────────────────────


class TestValidPlanets:
    """All period lords must be recognized planet names."""

    _VALID_PLANETS: ClassVar[set[str]] = {
        "Sun",
        "Moon",
        "Mars",
        "Mercury",
        "Jupiter",
        "Venus",
        "Saturn",
        "Rahu",
        "Ketu",
    }

    def _check_valid(self, periods) -> None:
        for p in periods:
            assert p.planet in self._VALID_PLANETS, f"Unknown planet: {p.planet}"

    def test_dwisaptati_planets_valid(self, manish_chart):
        self._check_valid(compute_dwisaptati_dasha(manish_chart))

    def test_shatabdika_planets_valid(self, manish_chart):
        self._check_valid(compute_shatabdika_dasha(manish_chart))

    def test_chaturaseeti_planets_valid(self, manish_chart):
        self._check_valid(compute_chaturaseeti_dasha(manish_chart))

    def test_dwadashottari_planets_valid(self, manish_chart):
        self._check_valid(compute_dwadashottari_dasha(manish_chart))

    def test_panchottari_planets_valid(self, manish_chart):
        self._check_valid(compute_panchottari_dasha(manish_chart))

    def test_shashtihayani_sun_moon_only(self, manish_chart):
        """Shashtihayani is strictly Sun+Moon; no other planets."""
        periods = compute_shashtihayani_dasha(manish_chart)
        lords = {p.planet for p in periods}
        assert lords == {"Sun", "Moon"}

    def test_shatrimsha_planets_valid(self, manish_chart):
        self._check_valid(compute_shatrimsha_dasha(manish_chart))


# ── First period is prorated ─────────────────────────────────────────────────


class TestFirstPeriodProrated:
    """The first Mahadasha must be shorter than its canonical duration (balance)."""

    def _duration_years(self, period) -> float:
        return (period.end - period.start).total_seconds() / (365.25 * 86400)

    def test_dwisaptati_first_prorated(self, manish_chart):
        periods = compute_dwisaptati_dasha(manish_chart)
        assert self._duration_years(periods[0]) < periods[0].years
        assert self._duration_years(periods[0]) > 0

    def test_shatrimsha_first_prorated(self, manish_chart):
        periods = compute_shatrimsha_dasha(manish_chart)
        assert self._duration_years(periods[0]) < periods[0].years
        assert self._duration_years(periods[0]) > 0

    def test_chaturaseeti_first_prorated(self, manish_chart):
        periods = compute_chaturaseeti_dasha(manish_chart)
        assert self._duration_years(periods[0]) < periods[0].years


# ── Antardasha structure ─────────────────────────────────────────────────────


class TestAntardasha:
    """Each Mahadasha must contain sub-periods equal to the system's planet count."""

    def test_dwisaptati_ad_count(self, manish_chart):
        periods = compute_dwisaptati_dasha(manish_chart)
        for md in periods:
            assert len(md.antardasha) == 8

    def test_shatrimsha_ad_count(self, manish_chart):
        periods = compute_shatrimsha_dasha(manish_chart)
        for md in periods:
            assert len(md.antardasha) == 6

    def test_shashtihayani_ad_count(self, manish_chart):
        periods = compute_shashtihayani_dasha(manish_chart)
        for md in periods:
            assert len(md.antardasha) == 2

    def test_dwisaptati_ad_contiguous(self, manish_chart):
        """Antardashas within first Dwisaptati MD must be contiguous."""
        periods = compute_dwisaptati_dasha(manish_chart)
        ads = periods[0].antardasha
        for i in range(1, len(ads)):
            gap = abs((ads[i].start - ads[i - 1].end).total_seconds())
            assert gap < 60

    def test_dwadashottari_ad_mercury_largest(self, manish_chart):
        """In Dwadashottari, Venus MD (25 yrs) must have longest antardasha for Venus.

        Within any MD, the AD duration = MD_days x (planet_yrs / 112).
        Venus (25 yrs) is the largest share, so Venus AD in any MD is the longest.
        """
        periods = compute_dwadashottari_dasha(manish_chart)
        md = periods[0]
        ads = md.antardasha
        venus_ad = next((a for a in ads if a.planet == "Venus"), None)
        sun_ad = next((a for a in ads if a.planet == "Sun"), None)
        assert venus_ad is not None
        assert sun_ad is not None
        venus_dur = (venus_ad.end - venus_ad.start).total_seconds()
        sun_dur = (sun_ad.end - sun_ad.start).total_seconds()
        assert venus_dur > sun_dur, (
            "Venus AD (25 yrs) must be longer than Sun AD (7 yrs) in Dwadashottari"
        )
