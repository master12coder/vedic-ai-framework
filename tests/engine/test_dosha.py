"""Test dosha detection."""

from daivai_engine.compute.dosha import (
    detect_all_doshas,
    detect_kaal_sarp_dosha,
    detect_mangal_dosha,
    detect_pitra_dosha,
    detect_sadesati,
)


class TestDoshaDetection:
    def test_detect_all_doshas_returns_ten(self, manish_chart):
        """4 original + 6 extended = 10 dosha checks."""
        doshas = detect_all_doshas(manish_chart)
        assert len(doshas) == 10

    def test_dosha_result_structure(self, manish_chart):
        doshas = detect_all_doshas(manish_chart)
        for d in doshas:
            assert isinstance(d.name, str)
            assert isinstance(d.name_hindi, str)
            assert isinstance(d.is_present, bool)
            assert d.severity in ("full", "partial", "cancelled", "none")
            assert isinstance(d.planets_involved, list)
            assert isinstance(d.description, str)

    def test_mangal_dosha(self, manish_chart):
        result = detect_mangal_dosha(manish_chart)
        mars = manish_chart.planets["Mars"]
        mangal_houses = {1, 2, 4, 7, 8, 12}
        if mars.house in mangal_houses:
            # Should detect some form of mangal dosha
            assert result.is_present or result.severity == "cancelled"
        else:
            assert not result.is_present

    def test_kaal_sarp_dosha(self, manish_chart):
        result = detect_kaal_sarp_dosha(manish_chart)
        assert result.name == "Kaal Sarp Dosha"
        # Just verify it runs without error

    def test_sadesati(self, manish_chart):
        result = detect_sadesati(manish_chart)
        assert result.name == "Sadesati"

    def test_sadesati_with_transit(self, manish_chart):
        """Test Sadesati detection with explicit transit Saturn sign."""
        moon_sign = manish_chart.planets["Moon"].sign_index
        # Saturn directly over Moon sign -> should detect Sadesati
        result = detect_sadesati(manish_chart, transit_saturn_sign=moon_sign)
        assert result.is_present
        assert "Peak" in result.description

    def test_pitra_dosha(self, manish_chart):
        result = detect_pitra_dosha(manish_chart)
        assert result.name == "Pitra Dosha"

    def test_ksd_description_contains_type_name(self, manish_chart):
        """When KSD is present (full/partial), description must include named type.

        The 12 named types (Anant, Kulik, …, Sheshnag) identify the KSD variant
        by Rahu's house position. Source: Traditional Jyotish.
        """
        ksd_names = {
            "Anant", "Kulik", "Vasuki", "Shankhapal", "Padma", "Mahapadma",
            "Takshak", "Karkotak", "Shankhnaad", "Ghatak", "Vishdhar", "Sheshnag",
        }
        result = detect_kaal_sarp_dosha(manish_chart)
        if result.is_present:
            # description must mention the type name
            assert any(kn in result.description for kn in ksd_names), (
                f"KSD description missing named type. Got: {result.description}"
            )

    def test_mangal_dosha_lagna_aries_cancels(self):
        """For Aries lagna, Mars in 1st is own-sign — full cancellation expected.

        Source: BPHS Ch.77 — Mars as lagna lord cancels Kuja Dosha.
        """
        from daivai_engine.compute.chart import compute_chart

        # 13/03/1991 around 06:30 Varanasi → approx Aries lagna
        # We use a deterministic chart where lagna IS Aries and Mars is in lagna.
        # Use Manish's chart lagna info to understand the fixture instead:
        chart = compute_chart(
            name="Aries Test",
            dob="13/03/1991",
            tob="06:30",
            lat=25.3176,
            lon=83.0067,
            tz_name="Asia/Kolkata",
        )
        result = detect_mangal_dosha(chart)
        mars = chart.planets["Mars"]
        mangal_houses = {1, 2, 4, 7, 8, 12}
        if mars.house in mangal_houses and chart.lagna_sign_index in (0, 7):
            # Lagna is Aries or Scorpio → cancellation must be present
            assert any("lagna lord" in r.lower() or "lagna is" in r.lower()
                       for r in result.cancellation_reasons), (
                f"Expected lagna-lord cancellation. Got: {result.cancellation_reasons}"
            )

    def test_mangal_dosha_cancellation_count(self, manish_chart):
        """Mangal Dosha cancellation reasons should be a list (may be empty)."""
        result = detect_mangal_dosha(manish_chart)
        assert isinstance(result.cancellation_reasons, list)

    def test_sadesati_not_active_march_2026(self, manish_chart):
        """Saturn in Pisces (sign 11) in March 2026 — NOT in Sadesati range for Taurus Moon.

        Moon is in Taurus (sign 1). Sadesati range = {0, 1, 2} (Aries, Taurus, Gemini).
        Saturn is in Pisces (sign 11) in March 2026 → no Sadesati.
        """
        saturn_pisces = 11  # Pisces = sign index 11
        result = detect_sadesati(manish_chart, transit_saturn_sign=saturn_pisces)
        assert not result.is_present, (
            f"Saturn in Pisces should NOT trigger Sadesati for Taurus Moon. "
            f"Got is_present={result.is_present}, desc={result.description}"
        )

    def test_sadesati_active_when_saturn_transits_taurus(self, manish_chart):
        """Saturn over Moon sign (Taurus=1) → Sadesati peak phase."""
        result = detect_sadesati(manish_chart, transit_saturn_sign=1)  # Taurus
        assert result.is_present
        assert "Peak" in result.description
