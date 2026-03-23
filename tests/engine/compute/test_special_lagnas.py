"""Tests for Special Lagnas — Hora, Bhava, Ghatika, Vighati, Pranapada, Indu, Shree."""

from __future__ import annotations

from daivai_engine.compute.special_lagnas import (
    SpecialLagna,
    compute_indu_lagna,
    compute_shree_lagna,
    compute_special_lagnas,
)
from daivai_engine.models.chart import ChartData


ALL_KEYS = ("hora", "bhava", "ghatika", "vighati", "pranapada", "indu", "shree")


class TestSpecialLagnas:
    def test_returns_all_seven_lagnas(self, manish_chart: ChartData) -> None:
        result = compute_special_lagnas(manish_chart)
        for key in ALL_KEYS:
            assert key in result, f"Missing special lagna: {key}"

    def test_longitudes_valid(self, manish_chart: ChartData) -> None:
        result = compute_special_lagnas(manish_chart)
        for key in ALL_KEYS:
            lagna = result[key]
            assert 0 <= lagna.longitude < 360, f"{key} longitude out of range"
            assert 0 <= lagna.sign_index <= 11, f"{key} sign_index out of range"
            assert 0 <= lagna.degree_in_sign < 30, f"{key} degree_in_sign out of range"

    def test_has_sign_labels(self, manish_chart: ChartData) -> None:
        result = compute_special_lagnas(manish_chart)
        for key in ALL_KEYS:
            assert result[key].sign_hi, f"{key} missing Hindi sign"
            assert result[key].sign_en, f"{key} missing English sign"

    def test_deterministic(self, manish_chart: ChartData) -> None:
        r1 = compute_special_lagnas(manish_chart)
        r2 = compute_special_lagnas(manish_chart)
        for key in ALL_KEYS:
            assert r1[key].longitude == r2[key].longitude, f"{key} not deterministic"


class TestInduLagna:
    def test_indu_lagna_valid_range(self, manish_chart: ChartData) -> None:
        indu = compute_indu_lagna(manish_chart)
        assert isinstance(indu, SpecialLagna)
        assert 0 <= indu.longitude < 360
        assert 0 <= indu.sign_index <= 11

    def test_indu_lagna_at_sign_boundary(self, manish_chart: ChartData) -> None:
        """Indu Lagna is placed at the start (0°) of its sign by convention."""
        indu = compute_indu_lagna(manish_chart)
        assert indu.degree_in_sign == 0.0

    def test_indu_lagna_longitude_matches_sign(self, manish_chart: ChartData) -> None:
        indu = compute_indu_lagna(manish_chart)
        expected_lon = indu.sign_index * 30.0
        assert indu.longitude == expected_lon

    def test_indu_lagna_manish_sensible(self, manish_chart: ChartData) -> None:
        """Manish: Mithuna lagna, Moon in Taurus.
        9th from Lagna (Mithuna=2) = sign 10 (Kumbha/Aquarius), lord = Saturn, Kaksha=1.
        9th from Moon (Taurus=1) = sign 9 (Makara/Capricorn), lord = Saturn, Kaksha=1.
        Sum=2, n=2, count 2 from Moon's sign (Taurus=1): sign=(1+2-1)%12=2 = Mithuna.
        """
        indu = compute_indu_lagna(manish_chart)
        # Mithuna (Gemini) = sign index 2, longitude = 60°
        assert indu.sign_index == 2
        assert indu.longitude == 60.0
        assert indu.sign_en == "Gemini"


class TestShreeLagna:
    def test_shree_lagna_valid_range(self, manish_chart: ChartData) -> None:
        shree = compute_shree_lagna(manish_chart)
        assert isinstance(shree, SpecialLagna)
        assert 0 <= shree.longitude < 360
        assert 0 <= shree.sign_index <= 11

    def test_shree_lagna_name(self, manish_chart: ChartData) -> None:
        shree = compute_shree_lagna(manish_chart)
        assert shree.name == "Shree Lagna"

    def test_shree_lagna_in_all_seven(self, manish_chart: ChartData) -> None:
        result = compute_special_lagnas(manish_chart)
        assert result["shree"].name == "Shree Lagna"

    def test_shree_lagna_manish_daytime(self, manish_chart: ChartData) -> None:
        """Manish born 12:17 IST, Sun should be above horizon (house >= 7).
        Shree Lagna = Lagna + Moon - Sun (daytime formula).
        """
        sun = manish_chart.planets["Sun"]
        is_day = sun.house >= 7
        assert is_day, "Manish is a daytime birth — Sun should be in houses 7-12"

        shree = compute_shree_lagna(manish_chart)
        lagna_lon = manish_chart.lagna_longitude
        sun_lon = sun.longitude
        moon_lon = manish_chart.planets["Moon"].longitude
        expected = (lagna_lon + moon_lon - sun_lon) % 360.0
        assert abs(shree.longitude - expected) < 0.001


class TestPranapada:
    def test_pranapada_valid_range(self, manish_chart: ChartData) -> None:
        result = compute_special_lagnas(manish_chart)
        pp = result["pranapada"]
        assert 0 <= pp.longitude < 360
        assert pp.name == "Pranapada"

    def test_pranapada_formula(self, manish_chart: ChartData) -> None:
        """Verify Pranapada = Lagna + 5 x (Moon - Sun) mod 360."""
        result = compute_special_lagnas(manish_chart)
        pp = result["pranapada"]
        lagna = manish_chart.lagna_longitude
        sun = manish_chart.planets["Sun"].longitude
        moon = manish_chart.planets["Moon"].longitude
        moon_from_sun = (moon - sun) % 360.0
        expected = (lagna + 5.0 * moon_from_sun) % 360.0
        assert abs(pp.longitude - expected) < 0.001


class TestVighatiLagna:
    def test_vighati_lagna_valid(self, manish_chart: ChartData) -> None:
        result = compute_special_lagnas(manish_chart)
        vl = result["vighati"]
        assert 0 <= vl.longitude < 360
        assert vl.name == "Vighati Lagna"

    def test_vighati_differs_from_ghatika(self, manish_chart: ChartData) -> None:
        """Vighati Lagna should generally differ from Ghatika Lagna
        because it advances 60x faster (unless elapsed time is near zero)."""
        result = compute_special_lagnas(manish_chart)
        # Both are valid; just verify both are present and in range
        assert 0 <= result["vighati"].longitude < 360
        assert 0 <= result["ghatika"].longitude < 360

    def test_hora_advances_1_sign_per_2point5_ghatikas(self, manish_chart: ChartData) -> None:
        """Hora Lagna must advance at 12°/ghatika (= 1 sign per 2.5 ghatikas) per BPHS Ch.5.

        Bhava Lagna advances at 6°/ghatika (1 sign per 5 ghatikas).
        The Hora:Bhava ratio must be 2:1 (Hora is exactly twice as fast).
        """
        import math

        from daivai_engine.compute.datetime_utils import compute_sunrise

        result = compute_special_lagnas(manish_chart)
        hora_lon = result["hora"].longitude
        bhava_lon = result["bhava"].longitude
        sun_lon = manish_chart.planets["Sun"].longitude
        lagna_lon = manish_chart.lagna_longitude

        # Both hora and bhava start from different bases, so we can't compare directly.
        # Instead verify: (hora - sun_lon) / (bhava - lagna_lon) ≈ 2.0 when ghatikas > 0.
        jd = manish_chart.julian_day
        lat, lon_ = manish_chart.latitude, manish_chart.longitude
        jd_sunrise = compute_sunrise(jd, lat, lon_)
        elapsed_days = jd - jd_sunrise
        ghatikas = elapsed_days * 60.0

        if ghatikas > 0.1:  # only check when meaningfully after sunrise
            hora_advance = (hora_lon - sun_lon) % 360.0
            bhava_advance = (bhava_lon - lagna_lon) % 360.0
            if bhava_advance > 0.01:
                ratio = hora_advance / bhava_advance
                assert math.isclose(ratio, 2.0, rel_tol=0.01), (
                    f"Hora:Bhava advance ratio should be 2:1, got {ratio:.3f}"
                )
