"""Test additional dasha systems — Yogini, Ashtottari, Chara."""

from daivai_engine.compute.dasha_extra import (
    compute_ashtottari_dasha,
    compute_chara_dasha,
    compute_yogini_dasha,
    is_ashtottari_applicable,
)


class TestYoginiDasha:
    def test_eight_periods(self, manish_chart):
        periods = compute_yogini_dasha(manish_chart)
        assert len(periods) == 8

    def test_contiguous_periods(self, manish_chart):
        periods = compute_yogini_dasha(manish_chart)
        for i in range(1, len(periods)):
            diff = abs((periods[i].start - periods[i - 1].end).total_seconds())
            assert diff < 60

    def test_yogini_names_valid(self, manish_chart):
        periods = compute_yogini_dasha(manish_chart)
        valid_names = {
            "Mangala",
            "Pingala",
            "Dhanya",
            "Bhramari",
            "Bhadrika",
            "Ulka",
            "Siddha",
            "Sankata",
        }
        for p in periods:
            assert p.yogini_name in valid_names

    def test_rohini_starts_with_bhramari(self, manish_chart):
        """Moon in Rohini (nakshatra index 3) → Bhramari starts first Yogini.

        Classical mapping: Ashwini(0)=Mangala, Bharani(1)=Pingala,
        Krittika(2)=Dhanya, Rohini(3)=Bhramari.
        Source: Jataka Parijata, Yogini Dasha chapter.
        """
        moon = manish_chart.planets["Moon"]
        assert moon.nakshatra == "Rohini", f"Expected Rohini, got {moon.nakshatra}"
        periods = compute_yogini_dasha(manish_chart)
        assert periods[0].yogini_name == "Bhramari", (
            f"Rohini should start Bhramari Yogini, got {periods[0].yogini_name}. "
            "Check _yogini_start_index formula — must be nakshatra_index % 8, not +3."
        )

    def test_rohini_first_yogini_planet_is_mars(self, manish_chart):
        """Bhramari Yogini is ruled by Mars — verify planet assignment."""
        periods = compute_yogini_dasha(manish_chart)
        assert periods[0].yogini_name == "Bhramari"
        assert periods[0].planet == "Mars"

    def test_yogini_years_sum_36(self, manish_chart):
        """All 8 Yogini years sum to 36 (fixed cycle, not prorated).

        Sum = 1+2+3+4+5+6+7+8 = 36.
        """
        # YOGINI_SEQUENCE years are fixed; total cycle is 36 years.
        from daivai_engine.compute.dasha_extra import YOGINI_SEQUENCE

        total = sum(years for _, _, years in YOGINI_SEQUENCE)
        assert total == 36

    def test_first_period_is_partial(self, manish_chart):
        """First Yogini Dasha should be prorated (less than full Bhramari 4 years)."""
        periods = compute_yogini_dasha(manish_chart)
        first_years = (periods[0].end - periods[0].start).days / 365.25
        assert first_years < 4.0, "First Yogini period must be a partial balance"
        assert first_years > 0.0


class TestAshtottariDasha:
    def test_eight_periods(self, manish_chart):
        periods = compute_ashtottari_dasha(manish_chart)
        assert len(periods) == 8

    def test_contiguous(self, manish_chart):
        periods = compute_ashtottari_dasha(manish_chart)
        for i in range(1, len(periods)):
            diff = abs((periods[i].start - periods[i - 1].end).total_seconds())
            assert diff < 60

    def test_planets_valid(self, manish_chart):
        periods = compute_ashtottari_dasha(manish_chart)
        valid = {"Sun", "Moon", "Mars", "Mercury", "Saturn", "Jupiter", "Rahu", "Venus"}
        for p in periods:
            assert p.planet in valid

    def test_applicability_check_returns_bool(self, manish_chart):
        """is_ashtottari_applicable must return a bool."""
        result = is_ashtottari_applicable(manish_chart)
        assert isinstance(result, bool)

    def test_total_years_108(self, manish_chart):
        """Ashtottari cycle = 108 years (6+15+8+17+10+19+12+21)."""
        from daivai_engine.compute.dasha_extra import ASHTOTTARI_SEQUENCE

        total = sum(years for _, years in ASHTOTTARI_SEQUENCE)
        assert total == 108


class TestCharaDasha:
    def test_twelve_periods(self, manish_chart):
        periods = compute_chara_dasha(manish_chart)
        assert len(periods) == 12

    def test_all_signs_covered(self, manish_chart):
        periods = compute_chara_dasha(manish_chart)
        signs = {p.sign_index for p in periods}
        assert len(signs) == 12  # All 12 signs

    def test_years_in_range(self, manish_chart):
        periods = compute_chara_dasha(manish_chart)
        for p in periods:
            assert 1 <= p.years <= 12

    def test_contiguous(self, manish_chart):
        periods = compute_chara_dasha(manish_chart)
        for i in range(1, len(periods)):
            diff = abs((periods[i].start - periods[i - 1].end).total_seconds())
            assert diff < 60
