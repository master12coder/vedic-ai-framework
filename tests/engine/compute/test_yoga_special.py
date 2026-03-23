"""Tests for special yoga detection — Chatussagara, Mahabhagya.

Also covers Adhi Yoga grading (Purna/Madhya/Hina) and Amala Yoga
Mercury/waxing-Moon improvements from yoga_extended.py.

Manish's chart facts (Mithuna lagna, sign_index=2):
  Kendras: H1=empty, H4=empty, H7=Saturn, H10=empty → Chatussagara absent.
  Mahabhagya (male): Sun is in H9 (day birth) but Moon is in Taurus (even sign) → absent.
  Adhi Yoga: benefics in 6/7/8 from Moon (Taurus, sign 1).
    6th = Libra(6), 7th = Scorpio(7), 8th = Sagittarius(8).
    Jupiter in Taurus(H12), Venus in Aquarius(H9), Mercury in Aquarius(H9) — none in 6/7/8.
    → Adhi Yoga absent for Manish.
  Amala Yoga: 10th from Moon (Taurus sign 1) = Aquarius (sign 10).
    Venus is in Aquarius → Amala fires.
"""

from __future__ import annotations

from daivai_engine.compute.yoga_special import detect_special_yogas
from daivai_engine.models.chart import ChartData, PlanetData


# ── Minimal chart factory ─────────────────────────────────────────────────────

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


def make_chart(
    lagna_sign: int,
    placements: dict[str, tuple[int, int]],
    gender: str = "Male",
) -> ChartData:
    planets: dict[str, PlanetData] = {}
    for p_name in _ALL_PLANETS:
        s_idx, house = placements.get(p_name, (lagna_sign, 1))
        planets[p_name] = _make_planet(p_name, s_idx, house)

    return ChartData(
        name="Test",
        dob="01/01/2000",
        tob="12:00",
        place="Test",
        gender=gender,
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


def _yoga_names(chart: ChartData) -> set[str]:
    return {y.name for y in detect_special_yogas(chart)}


# ── Chatussagara Yoga ─────────────────────────────────────────────────────────


class TestChatussagara:
    def test_all_4_kendras_occupied_detects_yoga(self):
        """One planet in each of H1, H4, H7, H10 → Chatussagara detected."""
        # Aries lagna (0). Kendras: H1=sign0, H4=sign3, H7=sign6, H10=sign9
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),  # H1
                "Moon": (3, 4),  # H4
                "Mars": (6, 7),  # H7
                "Jupiter": (9, 10),  # H10
            },
        )
        assert "Chatussagara Yoga" in _yoga_names(chart)

    def test_3_kendras_occupied_no_yoga(self):
        """Only 3 out of 4 kendras occupied → no Chatussagara."""
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),  # H1
                "Moon": (3, 4),  # H4
                "Mars": (6, 7),  # H7
                # H10 empty — all other planets default to H1
            },
        )
        # With default placements other planets also go to H1, but H10 stays empty
        # Rebuild to ensure H10 stays empty
        chart.planets["Jupiter"] = _make_planet("Jupiter", 0, 1)
        chart.planets["Venus"] = _make_planet("Venus", 0, 1)
        chart.planets["Mercury"] = _make_planet("Mercury", 0, 1)
        chart.planets["Saturn"] = _make_planet("Saturn", 0, 1)
        chart.planets["Rahu"] = _make_planet("Rahu", 0, 1)
        chart.planets["Ketu"] = _make_planet("Ketu", 0, 1)
        assert "Chatussagara Yoga" not in _yoga_names(chart)

    def test_chatussagara_includes_rahu_ketu(self):
        """Rahu or Ketu in kendra counts for Chatussagara."""
        chart = make_chart(
            0,
            {
                "Rahu": (0, 1),  # H1
                "Ketu": (3, 4),  # H4 (Ketu always opposite Rahu but we're using minimal chart)
                "Mars": (6, 7),  # H7
                "Saturn": (9, 10),  # H10
            },
        )
        assert "Chatussagara Yoga" in _yoga_names(chart)

    def test_chatussagara_result_structure(self):
        """Chatussagara result has correct field values."""
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),
                "Moon": (3, 4),
                "Mars": (6, 7),
                "Jupiter": (9, 10),
            },
        )
        yogas = detect_special_yogas(chart)
        chat = [y for y in yogas if y.name == "Chatussagara Yoga"]
        assert chat
        y = chat[0]
        assert y.is_present is True
        assert y.effect == "benefic"
        assert set(y.houses_involved) == {1, 4, 7, 10}
        assert len(y.planets_involved) >= 4

    def test_chatussagara_no_false_positive_all_in_one_house(self):
        """All planets in H1 → only 1 kendra occupied → no Chatussagara."""
        chart = make_chart(0, {})  # all default to H1
        assert "Chatussagara Yoga" not in _yoga_names(chart)


# ── Mahabhagya Yoga ───────────────────────────────────────────────────────────


class TestMahabhagya:
    def test_male_day_birth_odd_signs_detects_yoga(self):
        """Male + day birth + Sun/Moon/Lagna in odd signs → Mahabhagya."""
        # Aries lagna (0 = odd sign). Sun in odd sign above horizon.
        # Odd signs: 0=Aries, 2=Gemini, 4=Leo, 6=Libra, 8=Sagittarius, 10=Aquarius
        # Day birth = Sun in houses 7-12. For Aries lagna, H9=Sagittarius(8).
        chart = make_chart(
            0,
            {
                "Sun": (8, 9),  # H9 = day birth, Sagittarius = odd sign ✓
                "Moon": (0, 1),  # Aries = odd sign ✓
            },
            gender="Male",
        )
        # Lagna = Aries (sign 0) = odd ✓
        assert "Mahabhagya Yoga" in _yoga_names(chart)

    def test_female_night_birth_even_signs_detects_yoga(self):
        """Female + night birth + Sun/Moon/Lagna in even signs → Mahabhagya."""
        # Even signs: 1=Taurus, 3=Cancer, 5=Virgo, 7=Scorpio, 9=Capricorn, 11=Pisces
        # Night birth = Sun in H1-H6. For Taurus lagna, H2=Gemini(2), H3=Cancer(3)
        # Taurus lagna (sign 1) = even sign ✓
        chart = make_chart(
            1,
            {
                "Sun": (3, 3),  # H3 = night birth (H3 < 7), Cancer(3) = even ✓
                "Moon": (1, 1),  # Taurus(1) = even ✓
            },
            gender="Female",
        )
        # Lagna = Taurus (sign 1) = even ✓
        assert "Mahabhagya Yoga" in _yoga_names(chart)

    def test_male_night_birth_no_yoga(self):
        """Male + night birth → Mahabhagya requires day birth for male."""
        chart = make_chart(
            0,
            {
                "Sun": (0, 1),  # H1 = night birth, Aries = odd sign
                "Moon": (0, 1),  # Aries = odd sign
            },
            gender="Male",
        )
        assert "Mahabhagya Yoga" not in _yoga_names(chart)

    def test_female_day_birth_no_yoga(self):
        """Female + day birth → Mahabhagya requires night birth for female."""
        chart = make_chart(
            1,
            {
                "Sun": (7, 7),  # H7 = day birth, Scorpio = even sign
                "Moon": (1, 1),  # Taurus = even sign
            },
            gender="Female",
        )
        assert "Mahabhagya Yoga" not in _yoga_names(chart)

    def test_male_day_birth_mixed_signs_no_yoga(self):
        """Male day birth but Moon in even sign → no Mahabhagya."""
        chart = make_chart(
            0,
            {
                "Sun": (8, 9),  # H9 = day birth, odd sign ✓
                "Moon": (1, 2),  # Taurus (sign 1) = even sign ✗
            },
            gender="Male",
        )
        assert "Mahabhagya Yoga" not in _yoga_names(chart)

    def test_mahabhagya_result_structure(self):
        """Mahabhagya result has correct field values."""
        chart = make_chart(
            0,
            {
                "Sun": (8, 9),
                "Moon": (0, 1),
            },
            gender="Male",
        )
        yogas = detect_special_yogas(chart)
        maha = [y for y in yogas if y.name == "Mahabhagya Yoga"]
        assert maha
        y = maha[0]
        assert y.is_present is True
        assert y.effect == "benefic"
        assert "Sun" in y.planets_involved
        assert "Moon" in y.planets_involved

    def test_mahabhagya_lagna_in_even_sign_blocks_male(self):
        """Male day birth: if Lagna is even sign, Mahabhagya does not form."""
        # Taurus lagna (sign 1 = even) — blocks male Mahabhagya even if Sun/Moon odd
        chart = make_chart(
            1,
            {
                "Sun": (8, 8),  # H8 = day birth, Sagittarius = odd
                "Moon": (0, 12),  # Aries = odd
            },
            gender="Male",
        )
        # Lagna = Taurus (even) → all 3 must be odd → fails
        assert "Mahabhagya Yoga" not in _yoga_names(chart)


# ── Adhi Yoga grading (via detect_extended_yogas) ────────────────────────────


class TestAdhiYogaGrading:
    """Test Adhi Yoga Purna/Madhya/Hina grading in yoga_extended.py."""

    def test_purna_adhi_all_three_benefics(self):
        """All 3 of Jupiter, Venus, Mercury in 6/7/8 from Moon → Purna Adhi."""
        from daivai_engine.compute.yoga_extended import detect_extended_yogas

        # Aries lagna. Moon in H1 (sign 0). 6th from Moon = sign 5 (Virgo).
        # 7th = sign 6 (Libra). 8th = sign 7 (Scorpio).
        chart = make_chart(
            0,
            {
                "Moon": (0, 1),  # Moon in Aries = H1 (sign 0)
                "Jupiter": (5, 6),  # Jupiter in Virgo = H6 ✓
                "Venus": (6, 7),  # Venus in Libra = H7 ✓
                "Mercury": (7, 8),  # Mercury in Scorpio = H8 ✓
            },
        )
        yogas = detect_extended_yogas(chart)
        adhi = [y for y in yogas if y.name == "Adhi Yoga"]
        assert adhi, "Adhi Yoga should be detected"
        assert "Purna" in adhi[0].description
        assert adhi[0].strength == "full"

    def test_madhya_adhi_two_benefics(self):
        """2 of 3 benefics in 6/7/8 from Moon → Madhya Adhi."""
        from daivai_engine.compute.yoga_extended import detect_extended_yogas

        chart = make_chart(
            0,
            {
                "Moon": (0, 1),
                "Jupiter": (5, 6),  # H6 ✓
                "Venus": (6, 7),  # H7 ✓
                # Mercury NOT in 6/7/8
                "Mercury": (0, 1),
            },
        )
        yogas = detect_extended_yogas(chart)
        adhi = [y for y in yogas if y.name == "Adhi Yoga"]
        assert adhi
        assert "Madhya" in adhi[0].description
        assert adhi[0].strength == "full"

    def test_hina_adhi_one_benefic(self):
        """1 benefic in 6/7/8 from Moon → Hina Adhi, strength=partial."""
        from daivai_engine.compute.yoga_extended import detect_extended_yogas

        chart = make_chart(
            0,
            {
                "Moon": (0, 1),
                "Jupiter": (5, 6),  # H6 ✓
                # Venus and Mercury NOT in 6/7/8
                "Venus": (0, 1),
                "Mercury": (0, 1),
            },
        )
        yogas = detect_extended_yogas(chart)
        adhi = [y for y in yogas if y.name == "Adhi Yoga"]
        assert adhi
        assert "Hina" in adhi[0].description
        assert adhi[0].strength == "partial"

    def test_no_adhi_when_no_benefics_in_678_from_moon(self):
        """No benefics in 6/7/8 from Moon → no Adhi Yoga."""
        from daivai_engine.compute.yoga_extended import detect_extended_yogas

        chart = make_chart(
            0,
            {
                "Moon": (0, 1),
                "Jupiter": (0, 1),  # Same sign as Moon — not in 6/7/8
                "Venus": (0, 1),
                "Mercury": (0, 1),
            },
        )
        yogas = detect_extended_yogas(chart)
        adhi = [y for y in yogas if y.name == "Adhi Yoga"]
        assert not adhi


# ── Amala Yoga Mercury check (via detect_extended_yogas) ─────────────────────


class TestAmalaYogaMercury:
    def test_mercury_in_10th_from_moon_detects_amala(self):
        """Unafflicted Mercury in 10th sign from Moon triggers Amala."""
        from daivai_engine.compute.yoga_extended import detect_extended_yogas

        # Aries lagna. Moon in sign 0. 10th from Moon = sign 9.
        chart = make_chart(
            0,
            {
                "Moon": (0, 1),
                "Mercury": (9, 10),  # sign 9 = 10th from Moon ✓, not combust by default
                # Jupiter and Venus far away
                "Jupiter": (1, 2),
                "Venus": (1, 2),
            },
        )
        # Override Sun to be far from Mercury (no combustion)
        chart.planets["Sun"] = _make_planet("Sun", 0, 1)
        yogas = detect_extended_yogas(chart)
        amala = [y for y in yogas if y.name == "Amala Yoga"]
        assert amala, "Mercury in 10th from Moon should trigger Amala"
        assert "Mercury" in amala[0].planets_involved

    def test_combust_mercury_does_not_trigger_amala(self):
        """Combust Mercury should NOT trigger Amala Yoga."""
        from daivai_engine.compute.yoga_extended import detect_extended_yogas

        chart = make_chart(
            0,
            {
                "Moon": (0, 1),
                "Sun": (9, 10),  # Sun in sign 9
                "Jupiter": (1, 2),
                "Venus": (1, 2),
            },
        )
        # Mercury combust in sign 9 (10th from Moon)
        chart.planets["Mercury"] = _make_planet("Mercury", 9, 10, is_combust=True)
        yogas = detect_extended_yogas(chart)
        amala = [y for y in yogas if y.name == "Amala Yoga"]
        # Mercury is combust → should not trigger; Jupiter/Venus not in 10th → no Amala
        assert not amala


# ── Integration: Manish's chart ───────────────────────────────────────────────


class TestManishChartSpecial:
    def test_chatussagara_absent_manish(self, manish_chart: ChartData) -> None:
        """Manish's chart has only H7 occupied in kendras → no Chatussagara."""
        yogas = detect_special_yogas(manish_chart)
        names = {y.name for y in yogas}
        assert "Chatussagara Yoga" not in names

    def test_mahabhagya_absent_manish(self, manish_chart: ChartData) -> None:
        """Manish is male, day birth but Moon in Taurus (even) → no Mahabhagya."""
        yogas = detect_special_yogas(manish_chart)
        names = {y.name for y in yogas}
        assert "Mahabhagya Yoga" not in names

    def test_strength_field_present_all_yogas(self, manish_chart: ChartData) -> None:
        """Every yoga in detect_all_yogas has a valid strength field."""
        from daivai_engine.compute.yoga import detect_all_yogas

        for y in detect_all_yogas(manish_chart):
            assert y.strength in ("full", "partial", "cancelled", "enhanced"), (
                f"Invalid strength '{y.strength}' for yoga '{y.name}'"
            )

    def test_adhi_yoga_absent_manish(self, manish_chart: ChartData) -> None:
        """No benefics in 6/7/8 from Moon (Taurus) for Manish → no Adhi Yoga."""
        from daivai_engine.compute.yoga_extended import detect_extended_yogas

        yogas = detect_extended_yogas(manish_chart)
        adhi = [y for y in yogas if y.name == "Adhi Yoga"]
        assert not adhi, f"Expected no Adhi Yoga for Manish, got: {adhi}"
