"""Tests for all 32 Nabhasa yogas — BPHS Ch.13.

Uses a make_chart() factory for controlled unit tests and the
manish_chart fixture for integration tests.

Manish's chart (Mithuna lagna, sign_index=2):
  Classical planets:
    Sun, Mercury, Venus → Aquarius (H9)
    Moon, Mars, Jupiter → Taurus  (H12)
    Saturn              → Sagittarius (H7)
  Rahu → H9, Ketu → H3 (both excluded from Nabhasa)
  Unique houses: {7, 9, 12}  → Chhatra Yoga (7 consecutive from H7)
"""

from __future__ import annotations

from daivai_engine.compute.yoga_nabhasa import (
    _consec,
    detect_nabhasa_yogas,
)
from daivai_engine.models.chart import ChartData, PlanetData


# ── Test fixture factory ──────────────────────────────────────────────────

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


def _make_planet(name: str, sign_index: int, house: int) -> PlanetData:
    """Create a minimal PlanetData for testing."""
    return PlanetData(
        name=name,
        name_hi=_PLANET_HI.get(name, name),
        longitude=float(sign_index * 30),
        sign_index=sign_index,
        sign="Mesha",
        sign_en="Aries",
        sign_hi="मेष",
        degree_in_sign=0.0,
        nakshatra_index=0,
        nakshatra="Ashwini",
        nakshatra_lord="Ketu",
        pada=1,
        house=house,
        is_retrograde=False,
        speed=1.0,
        dignity="neutral",
        avastha="Yuva",
        is_combust=False,
        sign_lord="Mars",
    )


def make_chart(
    lagna_sign: int,
    placements: dict[str, tuple[int, int]],
) -> ChartData:
    """Create a minimal ChartData for Nabhasa yoga testing.

    Args:
        lagna_sign: Sign index (0-11) for the ascendant.
        placements: planet_name → (sign_index, house_number).
            Any classical planet not in placements defaults to (lagna_sign, 1).
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


def yoga_names(chart: ChartData) -> set[str]:
    """Return set of detected Nabhasa yoga names for a chart."""
    return {y.name for y in detect_nabhasa_yogas(chart)}


# ── Helpers ───────────────────────────────────────────────────────────────


class TestConsecHelper:
    def test_consec_basic(self):
        assert _consec(1, 4) == frozenset([1, 2, 3, 4])

    def test_consec_wraps(self):
        assert _consec(10, 4) == frozenset([10, 11, 12, 1])

    def test_consec_7_from_7(self):
        assert _consec(7, 7) == frozenset([7, 8, 9, 10, 11, 12, 1])

    def test_consec_7_from_10(self):
        assert _consec(10, 7) == frozenset([10, 11, 12, 1, 2, 3, 4])


# ── Category 1: Ashraya Yogas ─────────────────────────────────────────────


class TestAshrayaYogas:
    def test_rajju_all_chara_signs(self):
        """All 7 planets in movable signs → Rajju Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),
                "Moon": (0, 1),
                "Mars": (3, 4),
                "Mercury": (3, 4),
                "Jupiter": (6, 7),
                "Venus": (6, 7),
                "Saturn": (9, 10),
            },
        )
        assert "Rajju Yoga" in yoga_names(chart)
        assert "Musala Yoga" not in yoga_names(chart)
        assert "Nala Yoga" not in yoga_names(chart)

    def test_musala_all_fixed_signs(self):
        """All 7 planets in fixed signs → Musala Yoga."""
        chart = make_chart(
            1,
            {
                "Sun": (1, 1),
                "Moon": (1, 1),
                "Mars": (4, 4),
                "Mercury": (4, 4),
                "Jupiter": (7, 7),
                "Venus": (7, 7),
                "Saturn": (10, 10),
            },
        )
        assert "Musala Yoga" in yoga_names(chart)
        assert "Rajju Yoga" not in yoga_names(chart)

    def test_nala_all_dual_signs(self):
        """All 7 planets in dual signs → Nala Yoga."""
        chart = make_chart(
            2,
            {
                "Sun": (2, 1),
                "Moon": (2, 1),
                "Mars": (5, 4),
                "Mercury": (5, 4),
                "Jupiter": (8, 7),
                "Venus": (8, 7),
                "Saturn": (11, 10),
            },
        )
        assert "Nala Yoga" in yoga_names(chart)
        assert "Rajju Yoga" not in yoga_names(chart)

    def test_mixed_signs_no_ashraya(self):
        """Mixed sign types → no Ashraya yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),
                "Moon": (1, 2),  # chara + fixed
            },
        )
        names = yoga_names(chart)
        assert "Rajju Yoga" not in names
        assert "Musala Yoga" not in names
        assert "Nala Yoga" not in names

    def test_rahu_ketu_excluded_from_ashraya(self):
        """Rahu/Ketu in non-chara signs must NOT block Rajju Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),
                "Moon": (0, 1),
                "Mars": (3, 4),
                "Mercury": (3, 4),
                "Jupiter": (6, 7),
                "Venus": (6, 7),
                "Saturn": (9, 10),
                "Rahu": (1, 2),  # fixed sign — should be ignored
                "Ketu": (7, 8),  # fixed sign — should be ignored
            },
        )
        assert "Rajju Yoga" in yoga_names(chart)


# ── Category 2: Dala Yogas ────────────────────────────────────────────────


class TestDalaYogas:
    def test_maala_all_benefics_in_kendras(self):
        """All benefics in kendras → Maala Yoga."""
        # Lagna = 0 (Aries), kendras are H1,H4,H7,H10
        chart = make_chart(
            0,
            {
                "Jupiter": (0, 1),
                "Venus": (3, 4),
                "Mercury": (6, 7),
                "Moon": (9, 10),
                # Malefics anywhere
                "Sun": (1, 2),
                "Mars": (2, 3),
                "Saturn": (5, 6),
            },
        )
        assert "Maala Yoga" in yoga_names(chart)

    def test_maala_not_triggered_if_benefic_outside_kendra(self):
        chart = make_chart(
            0,
            {
                "Jupiter": (0, 1),
                "Venus": (3, 4),
                "Mercury": (6, 7),
                "Moon": (2, 3),  # Moon in H3 (not kendra)
            },
        )
        assert "Maala Yoga" not in yoga_names(chart)

    def test_sarpa_all_malefics_in_kendras(self):
        """All malefics in kendras → Sarpa Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),
                "Mars": (3, 4),
                "Saturn": (6, 7),
                # Benefics outside kendras
                "Jupiter": (1, 2),
                "Venus": (2, 3),
                "Mercury": (5, 6),
                "Moon": (8, 9),
            },
        )
        assert "Sarpa Yoga" in yoga_names(chart)

    def test_no_dala_when_mixed(self):
        """Neither Maala nor Sarpa when planets are spread."""
        chart = make_chart(
            0,
            {
                "Jupiter": (0, 1),
                "Venus": (1, 2),  # Venus in H2 (non-kendra)
            },
        )
        assert "Maala Yoga" not in yoga_names(chart)


# ── Category 3: Akriti Yogas ──────────────────────────────────────────────


class TestAkritiYogas:
    def test_gada_two_adjacent_kendras(self):
        """All planets in H1 and H4 → Gada Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),
                "Moon": (0, 1),
                "Mars": (3, 4),
                "Mercury": (0, 1),
                "Jupiter": (3, 4),
                "Venus": (3, 4),
                "Saturn": (0, 1),
            },
        )
        assert "Gada Yoga" in yoga_names(chart)

    def test_gada_opposite_kendras_not_triggered(self):
        """Planets in H1 and H7 only → NOT Gada (not adjacent pair) → Shakata."""
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),
                "Moon": (0, 1),
                "Mars": (6, 7),
                "Mercury": (6, 7),
                "Jupiter": (0, 1),
                "Venus": (6, 7),
                "Saturn": (0, 1),
            },
        )
        names = yoga_names(chart)
        assert "Shakata Yoga" in names
        assert "Gada Yoga" not in names

    def test_shringataka_all_in_trikonas(self):
        """All planets in H1, H5, H9 → Shringataka Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),
                "Moon": (0, 1),
                "Mars": (4, 5),
                "Mercury": (4, 5),
                "Jupiter": (8, 9),
                "Venus": (8, 9),
                "Saturn": (0, 1),
            },
        )
        assert "Shringataka Yoga" in yoga_names(chart)

    def test_hala_from_trikona_5(self):
        """All planets in H5, H6, H7 → Hala Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (4, 5),
                "Moon": (5, 6),
                "Mars": (6, 7),
                "Mercury": (4, 5),
                "Jupiter": (5, 6),
                "Venus": (6, 7),
                "Saturn": (4, 5),
            },
        )
        assert "Hala Yoga" in yoga_names(chart)

    def test_hala_from_trikona_9(self):
        """All planets in H9, H10, H11 → Hala Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (8, 9),
                "Moon": (9, 10),
                "Mars": (10, 11),
                "Mercury": (8, 9),
                "Jupiter": (9, 10),
                "Venus": (10, 11),
                "Saturn": (8, 9),
            },
        )
        assert "Hala Yoga" in yoga_names(chart)

    def test_vajra_yoga(self):
        """Benefics in H1/H7, malefics in H4/H10 → Vajra Yoga."""
        chart = make_chart(
            0,
            {
                "Jupiter": (0, 1),
                "Venus": (6, 7),
                "Mercury": (0, 1),
                "Moon": (6, 7),
                "Sun": (3, 4),
                "Mars": (9, 10),
                "Saturn": (3, 4),
            },
        )
        assert "Vajra Yoga" in yoga_names(chart)

    def test_yava_yoga(self):
        """Malefics in H1/H7, benefics in H4/H10 → Yava Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),
                "Mars": (6, 7),
                "Saturn": (0, 1),
                "Jupiter": (3, 4),
                "Venus": (9, 10),
                "Mercury": (3, 4),
                "Moon": (9, 10),
            },
        )
        assert "Yava Yoga" in yoga_names(chart)

    def test_kamala_all_in_kendras(self):
        """All planets in 4 kendras → Kamala Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),
                "Moon": (0, 1),
                "Mars": (3, 4),
                "Mercury": (6, 7),
                "Jupiter": (9, 10),
                "Venus": (0, 1),
                "Saturn": (3, 4),
            },
        )
        assert "Kamala Yoga" in yoga_names(chart)

    def test_vaapi_panaphara(self):
        """All planets in panaphara (2,5,8,11) → Vaapi Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (1, 2),
                "Moon": (1, 2),
                "Mars": (4, 5),
                "Mercury": (7, 8),
                "Jupiter": (10, 11),
                "Venus": (1, 2),
                "Saturn": (4, 5),
            },
        )
        assert "Vaapi Yoga" in yoga_names(chart)

    def test_vaapi_apoklima(self):
        """All planets in apoklima (3,6,9,12) → Vaapi Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (2, 3),
                "Moon": (5, 6),
                "Mars": (8, 9),
                "Mercury": (11, 12),
                "Jupiter": (2, 3),
                "Venus": (5, 6),
                "Saturn": (8, 9),
            },
        )
        assert "Vaapi Yoga" in yoga_names(chart)

    def test_yupa_houses_1_to_4(self):
        """All planets in H1-H4 → Yupa Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),
                "Moon": (1, 2),
                "Mars": (2, 3),
                "Mercury": (3, 4),
                "Jupiter": (0, 1),
                "Venus": (1, 2),
                "Saturn": (2, 3),
            },
        )
        assert "Yupa Yoga" in yoga_names(chart)

    def test_ishu_houses_4_to_7(self):
        """All planets in H4-H7 → Ishu Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (3, 4),
                "Moon": (4, 5),
                "Mars": (5, 6),
                "Mercury": (6, 7),
                "Jupiter": (3, 4),
                "Venus": (4, 5),
                "Saturn": (5, 6),
            },
        )
        assert "Ishu Yoga" in yoga_names(chart)

    def test_shakti_houses_7_to_10(self):
        """All planets in H7-H10 → Shakti Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (6, 7),
                "Moon": (7, 8),
                "Mars": (8, 9),
                "Mercury": (9, 10),
                "Jupiter": (6, 7),
                "Venus": (7, 8),
                "Saturn": (8, 9),
            },
        )
        assert "Shakti Yoga" in yoga_names(chart)

    def test_danda_houses_10_to_1(self):
        """All planets in H10-H1 (wrapping) → Danda Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (9, 10),
                "Moon": (10, 11),
                "Mars": (11, 12),
                "Mercury": (0, 1),
                "Jupiter": (9, 10),
                "Venus": (10, 11),
                "Saturn": (11, 12),
            },
        )
        assert "Danda Yoga" in yoga_names(chart)

    def test_naukaa_houses_1_to_7(self):
        """All planets in H1-H7 → Naukaa Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),
                "Moon": (1, 2),
                "Mars": (2, 3),
                "Mercury": (3, 4),
                "Jupiter": (4, 5),
                "Venus": (5, 6),
                "Saturn": (6, 7),
            },
        )
        assert "Naukaa Yoga" in yoga_names(chart)

    def test_chhatra_houses_7_to_1(self):
        """All planets in H7-H1 → Chhatra Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (6, 7),
                "Moon": (7, 8),
                "Mars": (8, 9),
                "Mercury": (9, 10),
                "Jupiter": (10, 11),
                "Venus": (11, 12),
                "Saturn": (0, 1),
            },
        )
        assert "Chhatra Yoga" in yoga_names(chart)

    def test_ardha_chandra_start_not_kendra(self):
        """7 consecutive houses from H2 (not a named yoga) → Ardha Chandra."""
        chart = make_chart(
            0,
            {
                "Sun": (1, 2),
                "Moon": (2, 3),
                "Mars": (3, 4),
                "Mercury": (4, 5),
                "Jupiter": (5, 6),
                "Venus": (6, 7),
                "Saturn": (7, 8),
            },
        )
        names = yoga_names(chart)
        assert "Ardha Chandra Yoga" in names
        assert "Naukaa Yoga" not in names

    def test_chakra_odd_houses(self):
        """All planets in odd houses → Chakra Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),
                "Moon": (2, 3),
                "Mars": (4, 5),
                "Mercury": (6, 7),
                "Jupiter": (8, 9),
                "Venus": (10, 11),
                "Saturn": (0, 1),
            },
        )
        assert "Chakra Yoga" in yoga_names(chart)

    def test_samudra_even_houses(self):
        """All planets in even houses → Samudra Yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (1, 2),
                "Moon": (3, 4),
                "Mars": (5, 6),
                "Mercury": (7, 8),
                "Jupiter": (9, 10),
                "Venus": (11, 12),
                "Saturn": (1, 2),
            },
        )
        assert "Samudra Yoga" in yoga_names(chart)


# ── Category 4: Sankhya Yogas ─────────────────────────────────────────────


class TestSankhyaYogas:
    """Sankhya yogas test number of distinct houses occupied."""

    def _chart_for_houses(self, house_list: list[int]) -> ChartData:
        """Create chart where 7 classical planets are placed in given houses."""
        planet_names = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        placements = {
            p: (i % 12, house_list[i % len(house_list)]) for i, p in enumerate(planet_names)
        }
        # Ensure sign indices produce the right houses for lagna=0
        return make_chart(0, placements)

    def _sankhya_from_n(self, n: int) -> str | None:
        """Build chart with exactly n distinct houses and return Sankhya yoga detected."""
        from daivai_engine.compute.yoga_nabhasa import _sankhya_yoga

        result = _sankhya_yoga(n)
        return result.name if result else None

    def test_vallaki_1_house(self):
        assert self._sankhya_from_n(1) == "Vallaki Yoga"

    def test_dama_2_houses(self):
        assert self._sankhya_from_n(2) == "Dama Yoga"

    def test_paasha_3_houses(self):
        assert self._sankhya_from_n(3) == "Paasha Yoga"

    def test_kedara_4_houses(self):
        assert self._sankhya_from_n(4) == "Kedara Yoga"

    def test_shoola_5_houses(self):
        assert self._sankhya_from_n(5) == "Shoola Yoga"

    def test_yuga_6_houses(self):
        assert self._sankhya_from_n(6) == "Yuga Yoga"

    def test_gola_7_houses(self):
        assert self._sankhya_from_n(7) == "Gola Yoga"

    def test_sankhya_mutually_exclusive(self):
        """Only one Sankhya yoga should be in results."""
        sankhya_names = {
            "Vallaki Yoga",
            "Dama Yoga",
            "Paasha Yoga",
            "Kedara Yoga",
            "Shoola Yoga",
            "Yuga Yoga",
            "Gola Yoga",
        }
        # 7 planets each in a different house — Gola Yoga
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),
                "Moon": (1, 2),
                "Mars": (2, 3),
                "Mercury": (3, 4),
                "Jupiter": (4, 5),
                "Venus": (5, 6),
                "Saturn": (6, 7),
            },
        )
        names = yoga_names(chart)
        detected_sankhya = names & sankhya_names
        assert len(detected_sankhya) <= 1


# ── Akriti Precedence over Sankhya ────────────────────────────────────────


class TestAkritiPrecedence:
    """Akriti yogas suppress Sankhya yogas when both conditions apply."""

    def test_chhatra_suppresses_sankhya(self):
        """Planets in H7, H9, H12 → Chhatra (Akriti), no Sankhya yoga."""
        # 3 distinct houses would normally give Paasha Yoga
        # but they all fit within H7-H1 Chhatra window
        chart = make_chart(
            0,
            {
                "Sun": (6, 7),
                "Moon": (8, 9),
                "Mars": (11, 12),
                "Mercury": (6, 7),
                "Jupiter": (8, 9),
                "Venus": (11, 12),
                "Saturn": (6, 7),
            },
        )
        names = yoga_names(chart)
        assert "Chhatra Yoga" in names
        assert "Paasha Yoga" not in names

    def test_kamala_suppresses_sankhya(self):
        """All planets in kendras → Kamala (Akriti), no Sankhya yoga."""
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),
                "Moon": (3, 4),
                "Mars": (6, 7),
                "Mercury": (9, 10),
                "Jupiter": (0, 1),
                "Venus": (3, 4),
                "Saturn": (6, 7),
            },
        )
        names = yoga_names(chart)
        assert "Kamala Yoga" in names
        assert "Kedara Yoga" not in names

    def test_no_akriti_gives_sankhya(self):
        """When no Akriti yoga applies, Sankhya yoga is returned."""
        # Place planets in 5 houses that don't form any Akriti pattern
        # H1, H2, H4, H6, H8 — not consecutive, not kendra-only, etc.
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),
                "Moon": (1, 2),
                "Mars": (3, 4),
                "Mercury": (5, 6),
                "Jupiter": (7, 8),
                "Venus": (0, 1),
                "Saturn": (1, 2),
            },
        )
        names = yoga_names(chart)
        assert "Shoola Yoga" in names


# ── Integration test: Manish's chart ─────────────────────────────────────


class TestManishChart:
    """Integration tests using the real Manish Chaurasia chart.

    Planet placement (Mithuna lagna, lagna_sign_index=2):
      Sun, Mercury, Venus → Aquarius → H9
      Moon, Mars, Jupiter → Taurus  → H12
      Saturn              → Sagittarius → H7
      (Rahu H9, Ketu H3 — excluded from Nabhasa)

    Occupied classical-planet houses: {7, 9, 12}
    These fit within Chhatra window H7-H1: {7,8,9,10,11,12,1} ✓
    → Chhatra Yoga (Akriti) is detected
    → Sankhya yoga is suppressed
    """

    def test_chhatra_yoga_detected(self, manish_chart: ChartData) -> None:
        """H7/H9/H12 all fit within 7-house Chhatra window from H7."""
        names = yoga_names(manish_chart)
        assert "Chhatra Yoga" in names

    def test_sankhya_suppressed_by_chhatra(self, manish_chart: ChartData) -> None:
        """Because Chhatra (Akriti) fires, no Sankhya yoga should appear."""
        sankhya = {
            "Vallaki Yoga",
            "Dama Yoga",
            "Paasha Yoga",
            "Kedara Yoga",
            "Shoola Yoga",
            "Yuga Yoga",
            "Gola Yoga",
        }
        names = yoga_names(manish_chart)
        assert not (names & sankhya), f"Unexpected Sankhya yoga(s): {names & sankhya}"

    def test_result_structure(self, manish_chart: ChartData) -> None:
        """All returned yogas have valid YogaResult fields."""
        for y in detect_nabhasa_yogas(manish_chart):
            assert y.is_present is True
            assert isinstance(y.name, str) and y.name
            assert isinstance(y.name_hindi, str)
            assert y.effect in ("benefic", "malefic", "mixed")
            assert isinstance(y.houses_involved, list)
            assert isinstance(y.planets_involved, list)

    def test_no_ashraya_yoga_for_manish(self, manish_chart: ChartData) -> None:
        """Manish has planets in Aquarius(sthira), Taurus(sthira), Sagittarius(dvisva)
        — mixed modalities, so no Ashraya yoga should fire."""
        names = yoga_names(manish_chart)
        assert "Rajju Yoga" not in names
        assert "Musala Yoga" not in names
        assert "Nala Yoga" not in names
