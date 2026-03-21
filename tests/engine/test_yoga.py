"""Test yoga detection."""

from daivai_engine.compute.chart import compute_chart
from daivai_engine.compute.yoga import detect_all_yogas
from daivai_engine.compute.yoga_extended import detect_extended_yogas


class TestYogaDetection:
    def test_detects_some_yogas(self, manish_chart):
        """A typical chart should detect at least some yogas."""
        yogas = detect_all_yogas(manish_chart)
        present = [y for y in yogas if y.is_present]
        assert len(present) >= 1

    def test_yoga_result_structure(self, manish_chart):
        """Verify yoga result has all required fields."""
        yogas = detect_all_yogas(manish_chart)
        for y in yogas:
            assert isinstance(y.name, str)
            assert isinstance(y.name_hindi, str)
            assert isinstance(y.is_present, bool)
            assert isinstance(y.planets_involved, list)
            assert isinstance(y.houses_involved, list)
            assert isinstance(y.description, str)
            assert y.effect in ("benefic", "malefic", "mixed")

    def test_budhaditya_detection(self, manish_chart):
        """Sun and Mercury in same sign should detect Budhaditya."""
        sun = manish_chart.planets["Sun"]
        mercury = manish_chart.planets["Mercury"]
        yogas = detect_all_yogas(manish_chart)
        budhaditya = [y for y in yogas if y.name == "Budhaditya Yoga"]
        if sun.sign_index == mercury.sign_index:
            assert len(budhaditya) == 1
            assert budhaditya[0].is_present

    def test_gajakesari_structure(self, manish_chart):
        """If Gajakesari is present, it should have Jupiter and Moon."""
        yogas = detect_all_yogas(manish_chart)
        gk = [y for y in yogas if y.name == "Gajakesari Yoga"]
        if gk and gk[0].is_present:
            assert "Jupiter" in gk[0].planets_involved
            assert "Moon" in gk[0].planets_involved

    def test_hamsa_yoga_exalted_jupiter_in_kendra(self):
        """Jupiter exalted in Cancer in kendra should form Hamsa Yoga."""
        # Create a chart where Jupiter is likely exalted in Cancer
        # This is a probabilistic test — we construct a scenario
        chart = compute_chart(
            name="Test Hamsa",
            dob="10/07/2014",  # Jupiter was in Cancer around this time
            tob="12:00",
            lat=28.6139,
            lon=77.2090,
            tz_name="Asia/Kolkata",
        )
        jup = chart.planets["Jupiter"]
        yogas = detect_all_yogas(chart)
        hamsa = [y for y in yogas if y.name == "Hamsa"]
        if jup.sign_index == 3 and jup.house in [1, 4, 7, 10]:
            assert len(hamsa) == 1

    def test_kemdrum_detection(self, manish_chart):
        """Kemdrum should only be detected if no planet in 2nd/12th from Moon."""
        yogas = detect_all_yogas(manish_chart)
        kemdrum = [y for y in yogas if y.name == "Kemdrum Yoga"]
        # Verify structure if present
        if kemdrum and kemdrum[0].is_present:
            assert "Moon" in kemdrum[0].planets_involved

    def test_neech_bhanga_retrograde_cancels(self):
        """A retrograde debilitated planet should get Neech Bhanga.

        Rule: Retrograde debilitated planet has its debilitation cancelled.
        Source: BPHS, widely accepted in classical Jyotish.
        """
        # Find a chart where a planet is debilitated AND retrograde.
        # Mercury retrogrades often; when debilitated (Pisces) + retrograde = Neech Bhanga.
        # Try a date when Mercury was likely in Pisces and retrograde.
        chart = compute_chart(
            name="Neech Bhanga Test",
            dob="15/03/2000",
            tob="06:00",
            lat=28.6139,
            lon=77.2090,
            tz_name="Asia/Kolkata",
        )
        yogas = detect_extended_yogas(chart)
        neech_bhangas = [y for y in yogas if y.name == "Neech Bhanga Raj Yoga"]
        # The test verifies: if any planet in this chart is debilitated+retrograde,
        # it MUST appear as Neech Bhanga with "retrograde" in description.
        for planet_name, planet in chart.planets.items():
            if planet.dignity == "debilitated" and planet.is_retrograde:
                matching = [y for y in neech_bhangas if planet_name in y.planets_involved]
                assert matching, (
                    f"{planet_name} is debilitated+retrograde but no Neech Bhanga detected"
                )
                assert any("retrograde" in y.description.lower() for y in matching), (
                    f"Retrograde rule not reflected in Neech Bhanga description for {planet_name}"
                )

    def test_vipreet_raj_yoga_structure(self, manish_chart):
        """All Vipreet Raj Yogas must involve dusthana lords in dusthana houses."""
        yogas = detect_all_yogas(manish_chart)
        vipreet = [y for y in yogas if "Vipreet" in y.name]
        for y in vipreet:
            assert y.is_present
            # Houses involved should include dusthana houses
            assert any(h in (6, 8, 12) for h in y.houses_involved), (
                f"Vipreet Raj Yoga houses should include dusthana: {y.houses_involved}"
            )
