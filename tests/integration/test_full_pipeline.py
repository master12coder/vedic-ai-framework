"""Integration test — full pipeline from birth details to report."""

import pytest
from jyotish.compute.chart import compute_chart
from jyotish.compute.dasha import compute_mahadashas, find_current_dasha
from jyotish.compute.yoga import detect_all_yogas
from jyotish.compute.dosha import detect_all_doshas
from jyotish.compute.divisional import compute_navamsha, compute_varga
from jyotish.compute.matching import compute_ashtakoot
from jyotish.compute.panchang import compute_panchang
from jyotish.compute.transit import compute_transits
from jyotish.compute.strength import compute_planet_strengths
from jyotish.compute.ashtakavarga import compute_ashtakavarga
from jyotish.compute.bhava_chalit import compute_bhava_chalit
from jyotish.compute.kp import compute_kp_positions
from jyotish.compute.upagraha import compute_all_upagrahas
from jyotish.compute.dasha_extra import compute_yogini_dasha, compute_ashtottari_dasha, compute_chara_dasha
from jyotish.interpret.formatter import format_chart_terminal, chart_to_dict
from jyotish.deliver.json_export import export_chart_json


class TestFullPipeline:
    """Test the complete pipeline from birth details to formatted output."""

    def test_manish_full_pipeline(self):
        """Full pipeline for Manish's chart — the primary test fixture."""
        # Step 1: Compute chart
        chart = compute_chart(
            name="Manish Chaurasia", dob="13/03/1989", tob="12:17",
            lat=25.3176, lon=83.0067, tz_name="Asia/Kolkata", gender="Male",
        )
        assert chart.lagna_sign == "Mithuna"

        # Step 2: Dasha
        mds = compute_mahadashas(chart)
        assert len(mds) == 9
        assert mds[0].lord == "Moon"

        md, ad, pd = find_current_dasha(chart)
        assert md.lord == "Jupiter"

        # Step 3: Yogas
        yogas = detect_all_yogas(chart)
        present = [y for y in yogas if y.is_present]
        assert len(present) >= 3

        # Step 4: Doshas
        doshas = detect_all_doshas(chart)
        assert len(doshas) == 4

        # Step 5: Divisional charts
        nav = compute_navamsha(chart)
        assert len(nav) == 9
        for varga in ["D2", "D3", "D9", "D10", "D12"]:
            result = compute_varga(chart, varga)
            assert len(result) == 9

        # Step 6: Ashtakavarga
        ashtaka = compute_ashtakavarga(chart)
        assert ashtaka.total == 337

        # Step 7: Bhava Chalit
        bhava = compute_bhava_chalit(chart)
        assert len(bhava.cusps) == 12
        assert len(bhava.planets) == 9

        # Step 8: KP
        kp = compute_kp_positions(chart)
        assert len(kp) == 9

        # Step 9: Upagraha
        upagrahas = compute_all_upagrahas(chart)
        assert len(upagrahas) >= 5

        # Step 10: Additional dashas
        yogini = compute_yogini_dasha(chart)
        assert len(yogini) == 8
        ashtottari = compute_ashtottari_dasha(chart)
        assert len(ashtottari) == 8
        chara = compute_chara_dasha(chart)
        assert len(chara) == 12

        # Step 11: Strength
        strengths = compute_planet_strengths(chart)
        assert len(strengths) == 9

        # Step 12: Transit
        transits = compute_transits(chart)
        assert len(transits.transits) == 9

        # Step 13: Format output
        terminal = format_chart_terminal(chart)
        assert "Mithuna" in terminal
        assert "Manish" in terminal

        json_str = export_chart_json(chart)
        assert '"lagna"' in json_str

        # Step 14: Dict export
        data = chart_to_dict(chart)
        assert data["lagna"]["sign"] == "Mithuna"
        assert len(data["planets"]) == 9

    def test_matching_pipeline(self):
        """Test Ashtakoot matching between two charts."""
        c1 = compute_chart(name="Person1", dob="15/08/1990", tob="06:30",
                           lat=26.9, lon=75.8, tz_name="Asia/Kolkata")
        c2 = compute_chart(name="Person2", dob="20/03/1992", tob="14:00",
                           lat=28.6, lon=77.2, tz_name="Asia/Kolkata")

        result = compute_ashtakoot(
            c1.planets["Moon"].nakshatra_index, c1.planets["Moon"].sign_index,
            c2.planets["Moon"].nakshatra_index, c2.planets["Moon"].sign_index,
        )
        assert 0 <= result.total_obtained <= 36
        assert len(result.kootas) == 8

    def test_panchang_pipeline(self):
        """Test panchang for today."""
        panchang = compute_panchang("16/03/2026", 25.3176, 83.0067, place="Varanasi")
        assert panchang.vara != ""
        assert panchang.nakshatra_name != ""
