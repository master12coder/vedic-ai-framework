"""Tests for Parivartana Yoga detection, Vargottama utility, and strength post-processor.

Uses a minimal make_chart() factory for controlled unit tests plus the
manish_chart fixture for integration verification.

Manish's chart (Mithuna lagna, sign_index=2):
  No Parivartana yogas -- verified by manual chart analysis.
  Vargottama check:
    Sun in Aquarius (sign 10, Air, d9_start=6). If deg in [13.33-16.67] -> sign 10 Vargottama.
"""

from __future__ import annotations

from daivai_engine.compute.yoga_parivartana import (
    apply_yoga_strength,
    detect_parivartana_yogas,
    is_vargottama,
)
from daivai_engine.models.chart import ChartData, PlanetData
from daivai_engine.models.yoga import YogaResult


# ── Minimal test fixtures ─────────────────────────────────────────────────────

_ALL_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

_PLANET_HI = {
    "Sun": "सूर्य",
    "Moon": "चन्द्र",
    "Mars": "मंगल",
    "Mercury": "बुध",
    "Jupiter": "गुरु",
    "Venus": "शुक्र",
    "Saturn": "शनि",
    "Rahu": "राहु",
    "Ketu": "केतु",
}


def _make_planet(
    name: str,
    sign_index: int,
    house: int,
    *,
    degree: float = 15.0,
    dignity: str = "neutral",
    is_retrograde: bool = False,
    is_combust: bool = False,
) -> PlanetData:
    """Create a minimal PlanetData for testing."""
    return PlanetData(
        name=name,
        name_hi=_PLANET_HI.get(name, name),
        longitude=float(sign_index * 30) + degree,
        sign_index=sign_index,
        sign="Mesha",
        sign_en="Aries",
        sign_hi="मेष",
        degree_in_sign=degree,
        nakshatra_index=0,
        nakshatra="Ashwini",
        nakshatra_lord="Ketu",
        pada=1,
        house=house,
        is_retrograde=is_retrograde,
        speed=1.0 if not is_retrograde else -1.0,
        dignity=dignity,
        avastha="Yuva",
        is_combust=is_combust,
        sign_lord="Mars",
    )


def make_chart(lagna_sign: int, placements: dict[str, tuple[int, int]]) -> ChartData:
    """Create a minimal ChartData for yoga testing.

    Args:
        lagna_sign: Sign index (0-11) for the ascendant.
        placements: planet_name to (sign_index, house_number).
    """
    planets: dict[str, PlanetData] = {}
    for p_name in _ALL_PLANETS:
        s_idx, house = placements.get(p_name, (lagna_sign, 1))
        planets[p_name] = _make_planet(p_name, s_idx, house)

    return ChartData(
        name="Test",
        dob="01/01/2000",
        tob="12:00",
        place="Test",
        gender="Male",
        latitude=0.0,
        longitude=0.0,
        timezone_name="UTC",
        julian_day=0.0,
        ayanamsha=0.0,
        lagna_longitude=float(lagna_sign * 30),
        lagna_sign_index=lagna_sign,
        lagna_sign="Mesha",
        lagna_sign_en="Aries",
        lagna_sign_hi="मेष",
        lagna_degree=0.0,
        planets=planets,
    )


# ── Vargottama tests ──────────────────────────────────────────────────────────


class TestIsVargottama:
    """Unit tests for the is_vargottama() utility."""

    def test_aries_first_navamsha_is_vargottama(self):
        """Aries 0-3.33 deg: navamsha starts Aries, D9 sign=0 = D1 sign=0."""
        planet = _make_planet("Mars", sign_index=0, house=1, degree=2.0)
        assert is_vargottama(planet) is True

    def test_aries_second_navamsha_not_vargottama(self):
        """Aries 3.34-6.66 deg: navamsha_idx=1, D9 sign=1 (Taurus) != 0."""
        planet = _make_planet("Mars", sign_index=0, house=1, degree=4.0)
        assert is_vargottama(planet) is False

    def test_taurus_fifth_navamsha_is_vargottama(self):
        """Taurus (Earth, d9_start=9): idx=4 → D9 sign=(9+4)%12=1=Taurus. ✓"""
        planet = _make_planet("Venus", sign_index=1, house=1, degree=15.0)
        # degree=15 → nav_idx = int(15 * 9 / 30) = int(4.5) = 4
        assert is_vargottama(planet) is True

    def test_gemini_ninth_navamsha_is_vargottama(self):
        """Gemini (Air, d9_start=6): idx=8 → D9=(6+8)%12=2=Gemini. ✓"""
        planet = _make_planet("Mercury", sign_index=2, house=1, degree=28.0)
        # degree=28 → nav_idx = int(28 * 9 / 30) = int(8.4) = 8
        assert is_vargottama(planet) is True

    def test_cancer_first_navamsha_is_vargottama(self):
        """Cancer (Water, d9_start=3): idx=0 → D9=(3+0)%12=3=Cancer. ✓"""
        planet = _make_planet("Moon", sign_index=3, house=1, degree=1.0)
        assert is_vargottama(planet) is True

    def test_cancer_second_navamsha_not_vargottama(self):
        """Cancer d9_start=3, idx=1 → D9=4 (Leo) ≠ 3 (Cancer)."""
        planet = _make_planet("Moon", sign_index=3, house=1, degree=5.0)
        assert is_vargottama(planet) is False

    def test_pisces_ninth_navamsha_is_vargottama(self):
        """Pisces (Water, d9_start=3): idx=8 → D9=(3+8)%12=11=Pisces. ✓"""
        planet = _make_planet("Jupiter", sign_index=11, house=1, degree=28.5)
        assert is_vargottama(planet) is True

    def test_aquarius_fifth_navamsha_is_vargottama(self):
        """Aquarius (Air, d9_start=6): idx=4 → D9=(6+4)%12=10=Aquarius. ✓"""
        planet = _make_planet("Saturn", sign_index=10, house=1, degree=14.0)
        # degree=14 → nav_idx = int(14 * 9 / 30) = int(4.2) = 4
        assert is_vargottama(planet) is True


# ── Parivartana Yoga detection tests ─────────────────────────────────────────


class TestDetectParivartanaYogas:
    def _names(self, chart: ChartData) -> set[str]:
        return {y.name for y in detect_parivartana_yogas(chart)}

    def test_maha_parivartana_kendra_trikona_exchange(self):
        """Aries lagna: Mars (H1 lord) in H9, Jupiter (H9 lord) in H1 → Maha."""
        # Aries lagna (sign 0). H1=Aries→Mars; H9=Sagittarius(8)→Jupiter
        chart = make_chart(
            0,
            {
                "Mars": (8, 9),  # Mars in Sagittarius = H9
                "Jupiter": (0, 1),  # Jupiter in Aries = H1
            },
        )
        names = self._names(chart)
        assert "Maha Parivartana Yoga" in names

    def test_dainya_parivartana_dusthana_exchange(self):
        """Aries lagna: Mars (H1 lord) in H6, Mercury (H6 lord) in H1 → Dainya."""
        # H6=Virgo(5)→Mercury; Mars in H6; Mercury in H1
        chart = make_chart(
            0,
            {
                "Mars": (5, 6),  # Mars in Virgo = H6
                "Mercury": (0, 1),  # Mercury in Aries = H1
            },
        )
        names = self._names(chart)
        assert "Dainya Parivartana Yoga" in names

    def test_khala_parivartana_upachaya_exchange(self):
        """Aries lagna: Mars (H1 lord) in H3, Sun (H3 lord, Leo=sign 4) in H1 → Khala."""
        # H3=Gemini(2)→Mercury; but H3 lord for Aries = sign(0+3-1)%12=2(Gemini)→Mercury
        # Let's do H3 ↔ H1: H3=Gemini→Mercury, H1=Aries→Mars
        # Mercury(lord H3) in H1(Aries); Mars(lord H1) in H3(Gemini)
        chart = make_chart(
            0,
            {
                "Mercury": (0, 1),  # Mercury in Aries = H1 ✓ (lord H3 in H1)
                "Mars": (2, 3),  # Mars in Gemini = H3 ✓ (lord H1 in H3)
            },
        )
        names = self._names(chart)
        assert "Khala Parivartana Yoga" in names

    def test_same_lord_houses_skipped(self):
        """For Aries lagna, Mercury lords H3 (Gemini) and H6 (Virgo). No self-exchange."""
        # Put Mercury in any house — can't exchange with itself
        chart = make_chart(
            0,
            {
                "Mercury": (2, 3),  # Mercury in H3 (its own sign H3)
            },
        )
        # No planet is lord of H3 and H6 simultaneously, but Mercury lords both.
        # A parivartana between H3 and H6 would require Mercury in H6 AND Mercury in H3
        # — impossible since Mercury is one planet. Should be skipped.
        yogas = detect_parivartana_yogas(chart)
        for y in yogas:
            # All parivartana pairs must involve 2 distinct planets
            assert len(set(y.planets_involved)) == 2

    def test_no_parivartana_when_no_exchange(self):
        """A chart where no lords exchange signs should return empty list."""
        # All planets in H1 — no exchanges possible
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),
                "Moon": (0, 1),
                "Mars": (0, 1),
                "Mercury": (0, 1),
                "Jupiter": (0, 1),
                "Venus": (0, 1),
                "Saturn": (0, 1),
            },
        )
        assert detect_parivartana_yogas(chart) == []

    def test_parivartana_result_structure(self):
        """Detected parivartana has valid YogaResult fields."""
        chart = make_chart(
            0,
            {
                "Mars": (8, 9),  # H1 lord → H9
                "Jupiter": (0, 1),  # H9 lord → H1
            },
        )
        yogas = detect_parivartana_yogas(chart)
        assert yogas
        y = yogas[0]
        assert y.is_present is True
        assert len(y.planets_involved) == 2
        assert len(y.houses_involved) == 2
        assert y.effect in ("benefic", "malefic", "mixed")
        assert y.strength in ("full", "enhanced", "partial", "cancelled")

    def test_vargottama_lord_sets_enhanced_strength(self):
        """If an exchanging planet is Vargottama, strength should be 'enhanced'."""
        # Mars at degree 2 in Aries (sign 0, Fire d9_start=0) → nav_idx=0 → D9 sign=0 = Vargottama
        chart = make_chart(0, {})
        chart.planets["Mars"] = _make_planet("Mars", sign_index=8, house=9, degree=2.0)
        chart.planets["Jupiter"] = _make_planet("Jupiter", sign_index=0, house=1, degree=2.0)
        # Jupiter in Aries (Fire, d9_start=0), degree=2 → nav_idx=0 → D9 sign=0=Aries = Vargottama

        yogas = detect_parivartana_yogas(chart)
        maha = [y for y in yogas if y.name == "Maha Parivartana Yoga"]
        assert maha, "Maha Parivartana should be detected"
        assert maha[0].strength == "enhanced"

    def test_maha_parivartana_1_5_exchange(self):
        """H1 ↔ H5 is both kendra (1) and trikona (5) → Maha."""
        # Taurus lagna (sign 1). H1=Taurus→Venus; H5=Virgo(5)→Mercury
        chart = make_chart(
            1,
            {
                "Venus": (5, 5),  # Venus in Virgo = H5 ✓
                "Mercury": (1, 1),  # Mercury in Taurus = H1 ✓
            },
        )
        assert "Maha Parivartana Yoga" in self._names(chart)

    def test_dainya_parivartana_8_12_exchange(self):
        """H8 ↔ H12: both are dusthana → Dainya."""
        # Aries lagna. H8=Scorpio(7)→Mars; H12=Pisces(11)→Jupiter
        chart = make_chart(
            0,
            {
                "Mars": (11, 12),  # Mars in Pisces = H12 ✓
                "Jupiter": (7, 8),  # Jupiter in Scorpio = H8 ✓
            },
        )
        assert "Dainya Parivartana Yoga" in self._names(chart)


# ── Strength post-processor tests ────────────────────────────────────────────


class TestApplyYogaStrength:
    def _simple_yoga(self, planets: list[str], effect: str = "benefic") -> YogaResult:
        return YogaResult(
            name="Test Yoga",
            name_hindi="टेस्ट योग",
            is_present=True,
            planets_involved=planets,
            houses_involved=[1],
            description="test",
            effect=effect,
        )

    def test_combust_planet_downgrades_to_partial(self):
        """A combust yoga planet should downgrade strength to 'partial'."""
        chart = make_chart(0, {"Jupiter": (0, 1)})
        chart.planets["Jupiter"] = _make_planet("Jupiter", 0, 1, is_combust=True)
        yoga = self._simple_yoga(["Jupiter"])
        result = apply_yoga_strength([yoga], chart)
        assert result[0].strength == "partial"

    def test_combust_and_debilitated_gives_cancelled(self):
        """Combust + debilitated planet → 'cancelled'."""
        chart = make_chart(0, {"Saturn": (0, 1)})
        chart.planets["Saturn"] = _make_planet(
            "Saturn", 0, 1, dignity="debilitated", is_combust=True
        )
        yoga = self._simple_yoga(["Saturn"])
        result = apply_yoga_strength([yoga], chart)
        assert result[0].strength == "cancelled"

    def test_vargottama_planet_upgrades_to_enhanced(self):
        """A Vargottama yoga planet should upgrade strength to 'enhanced'."""
        chart = make_chart(0, {})
        # Jupiter at degree 2 in Aries (Fire, d9_start=0) → nav_idx=0 → D9=0=Aries → Vargottama
        chart.planets["Jupiter"] = _make_planet("Jupiter", 0, 1, degree=2.0)
        yoga = self._simple_yoga(["Jupiter"])
        result = apply_yoga_strength([yoga], chart)
        assert result[0].strength == "enhanced"

    def test_retrograde_benefic_upgrades_to_enhanced(self):
        """A retrograde planet in a benefic yoga upgrades to 'enhanced'."""
        chart = make_chart(0, {"Jupiter": (5, 6)})
        chart.planets["Jupiter"] = _make_planet("Jupiter", 5, 6, is_retrograde=True)
        yoga = self._simple_yoga(["Jupiter"])
        result = apply_yoga_strength([yoga], chart)
        assert result[0].strength == "enhanced"

    def test_retrograde_malefic_yoga_not_upgraded(self):
        """Retrograde planet in a malefic yoga should NOT be upgraded."""
        chart = make_chart(0, {"Saturn": (5, 6)})
        chart.planets["Saturn"] = _make_planet("Saturn", 5, 6, is_retrograde=True)
        yoga = self._simple_yoga(["Saturn"], effect="malefic")
        result = apply_yoga_strength([yoga], chart)
        assert result[0].strength == "full"

    def test_no_planets_yoga_unchanged(self):
        """Yoga with no planets_involved passes through unchanged."""
        chart = make_chart(0, {})
        yoga = YogaResult(
            name="Nabhasa Yoga",
            name_hindi="नभस योग",
            is_present=True,
            planets_involved=[],
            houses_involved=[1, 2, 3],
            description="pattern-based",
            effect="benefic",
        )
        result = apply_yoga_strength([yoga], chart)
        assert result[0].strength == "full"

    def test_combust_does_not_upgrade_partial(self):
        """If strength is already 'partial' from grading, combustion doesn't change it."""
        chart = make_chart(0, {"Mercury": (5, 6)})
        chart.planets["Mercury"] = _make_planet("Mercury", 5, 6, is_combust=True)
        yoga = YogaResult(
            name="Adhi Yoga",
            name_hindi="अधि योग",
            is_present=True,
            planets_involved=["Mercury"],
            houses_involved=[6],
            description="Hina",
            effect="benefic",
            strength="partial",  # Already partial from Hina grading
        )
        result = apply_yoga_strength([yoga], chart)
        # Combust on already-partial: stays partial (not worse than partial alone)
        assert result[0].strength == "partial"


# ── Integration: Manish's chart ───────────────────────────────────────────────


class TestManishChartParivartana:
    """Integration tests against the real Manish Chaurasia chart."""

    def test_no_parivartana_for_manish(self, manish_chart: ChartData) -> None:
        """Manish's chart has no mutual sign exchanges (verified manually)."""
        yogas = detect_parivartana_yogas(manish_chart)
        assert yogas == [], (
            f"Expected no Parivartana for Manish, got: "
            f"{[(y.name, y.houses_involved) for y in yogas]}"
        )

    def test_result_types_valid(self, manish_chart: ChartData) -> None:
        """All returned yoga results have valid field types."""
        from daivai_engine.compute.yoga import detect_all_yogas

        for y in detect_all_yogas(manish_chart):
            assert isinstance(y.name, str) and y.name
            assert isinstance(y.strength, str)
            assert y.strength in ("full", "partial", "cancelled", "enhanced")
            assert y.effect in ("benefic", "malefic", "mixed")
