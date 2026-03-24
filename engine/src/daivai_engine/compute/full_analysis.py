"""Full chart analysis — compute ALL engine calculations in one call.

Orchestrator that calls every engine module and returns a single typed
FullChartAnalysis v5.0. Each module wrapped in safe_compute().

NOTE: lordship_context must be passed in from the products layer.
"""

from __future__ import annotations

from typing import Any

from daivai_engine.compute.argala import compute_argala
from daivai_engine.compute.ashtakavarga import compute_ashtakavarga
from daivai_engine.compute.avasthas import (
    compute_deeptadi_avasthas,
    compute_lajjitadi_avasthas,
)
from daivai_engine.compute.badhaka import compute_badhaka
from daivai_engine.compute.bhava_bala import compute_bhava_bala
from daivai_engine.compute.bhava_chalit import compute_bhava_chalit
from daivai_engine.compute.bhavat_bhavam import compute_all_bhavat_bhavam
from daivai_engine.compute.compatibility_advanced import compute_mangal_dosha_detailed
from daivai_engine.compute.dasha import compute_mahadashas, find_current_dasha
from daivai_engine.compute.dasha_advanced import compute_dasha_sandhi
from daivai_engine.compute.dasha_extra import (
    compute_ashtottari_dasha,
    compute_chara_dasha,
    compute_yogini_dasha,
)
from daivai_engine.compute.dasha_transit import compute_dasha_transit
from daivai_engine.compute.datetime_utils import now_ist, to_jd
from daivai_engine.compute.dispositor import compute_dispositor_tree
from daivai_engine.compute.divisional import compute_navamsha, get_vargottam_planets
from daivai_engine.compute.dosha import detect_all_doshas
from daivai_engine.compute.double_transit import (
    check_double_transit,
    check_double_transit_from_moon,
)
from daivai_engine.compute.eclipse_natal import compute_upcoming_eclipse_impacts
from daivai_engine.compute.full_analysis_utils import compute_phase2_modules, safe_compute
from daivai_engine.compute.gandanta import check_gandanta
from daivai_engine.compute.graha_yuddha import detect_planetary_war
from daivai_engine.compute.house_comparison import compare_whole_sign_vs_chalit
from daivai_engine.compute.ishta_kashta import compute_ishta_kashta
from daivai_engine.compute.jaimini import compute_jaimini
from daivai_engine.compute.kalachakra_dasha import compute_kalachakra_dasha
from daivai_engine.compute.kota_chakra import compute_kota_chakra
from daivai_engine.compute.kp import compute_kp_positions
from daivai_engine.compute.lal_kitab import compute_lal_kitab
from daivai_engine.compute.longevity import compute_longevity
from daivai_engine.compute.namakarana import check_gand_mool
from daivai_engine.compute.narayana_dasha import compute_narayana_dasha
from daivai_engine.compute.nisheka import compute_nisheka
from daivai_engine.compute.panchang import compute_panchang
from daivai_engine.compute.reference_chart import (
    compute_chandra_kundali,
    compute_surya_kundali,
)
from daivai_engine.compute.saham import compute_sahams
from daivai_engine.compute.special_lagnas import compute_special_lagnas
from daivai_engine.compute.strength import compute_shadbala
from daivai_engine.compute.sudarshan import compute_sudarshan
from daivai_engine.compute.transit_advanced import (
    compute_jupiter_transit,
    compute_rahu_ketu_transit,
    compute_sadesati_detailed,
)
from daivai_engine.compute.upagraha import compute_all_upagrahas
from daivai_engine.compute.upapada import compute_upapada_lagna
from daivai_engine.compute.varga_analysis import (
    analyze_d4_property,
    analyze_d7_children,
    analyze_d10_career,
    analyze_d24_education,
)
from daivai_engine.compute.verify import verify_chart_accuracy
from daivai_engine.compute.vimshopaka import compute_vimshopaka_bala
from daivai_engine.compute.yoga import detect_all_yogas
from daivai_engine.compute.yoga_timing import compute_all_yoga_timings
from daivai_engine.constants import SIGN_LORDS
from daivai_engine.models.analysis import FullChartAnalysis
from daivai_engine.models.chart import ChartData


def compute_full_analysis(
    chart: ChartData,
    lordship_context: dict[str, Any] | None = None,
) -> FullChartAnalysis:
    """Run ALL engine computations — 60+ modules, one typed result.

    Args:
        chart: Computed birth chart.
        lordship_context: From products layer (engine can't import products).

    Returns:
        FullChartAnalysis v5.0 — the complete data contract.
    """
    if lordship_context is None:
        lordship_context = {}

    # Lagna lord (every pandit's first check)
    lagna_lord_name = SIGN_LORDS[chart.lagna_sign_index]

    # Core
    mahadashas = compute_mahadashas(chart)
    md, ad, _pd = find_current_dasha(chart)
    yogas = detect_all_yogas(chart)
    doshas = detect_all_doshas(chart)
    shadbala = compute_shadbala(chart)
    avk = compute_ashtakavarga(chart)

    # Strength
    bb = safe_compute(compute_bhava_bala, chart)
    vimshopaka = safe_compute(compute_vimshopaka_bala, chart)
    ishta_kashta = safe_compute(compute_ishta_kashta, chart, shadbala)

    # Avasthas
    deeptadi = safe_compute(compute_deeptadi_avasthas, chart)
    lajjitadi = safe_compute(compute_lajjitadi_avasthas, chart)

    # Special checks
    gandanta = safe_compute(check_gandanta, chart)
    yuddha = safe_compute(detect_planetary_war, chart)
    gand_mool = safe_compute(check_gand_mool, chart)

    # Divisional
    navamsha = safe_compute(compute_navamsha, chart)
    vargottam = safe_compute(get_vargottam_planets, chart)

    # Transit
    dt_lagna = safe_compute(check_double_transit, chart)
    dt_moon = safe_compute(check_double_transit_from_moon, chart)
    sadesati = safe_compute(compute_sadesati_detailed, chart)
    jup_transit = safe_compute(compute_jupiter_transit, chart)
    rk_transit = safe_compute(compute_rahu_ketu_transit, chart)

    # Jaimini
    jaimini = safe_compute(compute_jaimini, chart)
    upapada = compute_upapada_lagna(chart)
    argala = safe_compute(compute_argala, chart)

    # KP + Bhava Chalit
    kp_pos = safe_compute(compute_kp_positions, chart)
    bhava_chalit = safe_compute(compute_bhava_chalit, chart)
    house_shifts = safe_compute(compare_whole_sign_vs_chalit, chart)
    upagrahas = safe_compute(compute_all_upagrahas, chart)

    # Dashas (all systems)
    narayana = safe_compute(compute_narayana_dasha, chart)
    yogini = safe_compute(compute_yogini_dasha, chart)
    ashtottari = safe_compute(compute_ashtottari_dasha, chart)
    chara = safe_compute(compute_chara_dasha, chart)
    kalachakra = safe_compute(compute_kalachakra_dasha, chart)
    sandhi = safe_compute(compute_dasha_sandhi, mahadashas)

    # Special lagnas
    sp_lagnas = safe_compute(compute_special_lagnas, chart)
    if not isinstance(sp_lagnas, dict):
        sp_lagnas = {}

    # Birth panchang
    panchang = safe_compute(
        compute_panchang,
        chart.dob,
        chart.latitude,
        chart.longitude,
        chart.timezone_name,
        chart.place,
    )

    # Misc modules
    sudarshan = safe_compute(compute_sudarshan, chart)
    sahams = safe_compute(compute_sahams, chart)
    longevity = safe_compute(compute_longevity, chart)
    mangal = safe_compute(compute_mangal_dosha_detailed, chart)

    # Varga analysis
    varga: dict[str, Any] = {}
    for key, fn in [
        ("D7", analyze_d7_children),
        ("D4", analyze_d4_property),
        ("D24", analyze_d24_education),
        ("D10", analyze_d10_career),
    ]:
        result = safe_compute(fn, chart)
        if result:
            varga[key] = result

    # Phase 1 advanced modules
    dispositor = safe_compute(compute_dispositor_tree, chart)
    badhaka = safe_compute(compute_badhaka, chart)
    bhavat_bhavam = safe_compute(compute_all_bhavat_bhavam, chart)
    chandra_kundali = safe_compute(compute_chandra_kundali, chart)
    surya_kundali = safe_compute(compute_surya_kundali, chart)
    dasha_transit = safe_compute(compute_dasha_transit, chart)
    yoga_timings = safe_compute(compute_all_yoga_timings, chart)
    lal_kitab = safe_compute(compute_lal_kitab, chart)
    moon_nak = chart.planets["Moon"].nakshatra_index
    kota_chakra = safe_compute(compute_kota_chakra, moon_nak)
    nisheka = safe_compute(compute_nisheka, chart)
    eclipse_jd = to_jd(now_ist())
    eclipse_impacts = safe_compute(compute_upcoming_eclipse_impacts, chart, eclipse_jd, 1)

    # Pancha Pakshi birth bird (pure birth chart data)
    pp_bird = ""
    if panchang and hasattr(panchang, "paksha"):
        from daivai_engine.compute.pancha_pakshi import get_birth_bird

        pp_bird_result = safe_compute(get_birth_bird, moon_nak, panchang.paksha)
        if pp_bird_result and hasattr(pp_bird_result, "value"):
            pp_bird = pp_bird_result.value
        elif isinstance(pp_bird_result, str):
            pp_bird = pp_bird_result

    # Phase 2 modules (14 previously orphaned computations)
    phase2 = compute_phase2_modules(chart)

    # Verification
    verification = verify_chart_accuracy(chart)

    return FullChartAnalysis(
        chart=chart,
        lagna_lord=lagna_lord_name,
        mahadashas=mahadashas,
        current_md=md,
        current_ad=ad,
        narayana_dasha=narayana,
        yogini_dasha=yogini,
        ashtottari_dasha=ashtottari,
        chara_dasha=chara,
        kalachakra_dasha=kalachakra if not isinstance(kalachakra, list) else None,
        dasha_sandhi=sandhi,
        yogas=yogas,
        doshas=doshas,
        shadbala=shadbala,
        bhava_bala=bb,
        ashtakavarga=avk,
        vimshopaka=vimshopaka,
        ishta_kashta=ishta_kashta,
        deeptadi_avasthas=deeptadi,
        lajjitadi_avasthas=lajjitadi,
        gandanta=gandanta,
        graha_yuddha=yuddha,
        gand_mool=gand_mool,
        navamsha_positions=navamsha,
        vargottam_planets=vargottam if isinstance(vargottam, list) else [],
        double_transit=dt_lagna,
        double_transit_moon=dt_moon,
        sadesati=sadesati,
        jupiter_transit=jup_transit,
        rahu_ketu_transit=rk_transit,
        jaimini=jaimini,
        upapada=upapada,
        argala=argala,
        kp_positions=kp_pos,
        bhava_chalit=bhava_chalit,
        house_shifts=house_shifts,
        upagrahas=upagrahas,
        special_lagnas=sp_lagnas,
        birth_panchang=panchang,
        sudarshan=sudarshan,
        sahams=sahams,
        longevity=longevity,
        mangal_dosha=mangal,
        varga_analysis=varga,
        lordship_context=lordship_context,
        verification_warnings=verification,
        dispositor_tree=dispositor if not isinstance(dispositor, list) else None,
        badhaka=badhaka if not isinstance(badhaka, list) else None,
        bhavat_bhavam=bhavat_bhavam,
        chandra_kundali=chandra_kundali if not isinstance(chandra_kundali, list) else None,
        surya_kundali=surya_kundali if not isinstance(surya_kundali, list) else None,
        dasha_transit=dasha_transit if not isinstance(dasha_transit, list) else None,
        yoga_timings=yoga_timings if not isinstance(yoga_timings, list) else None,
        lal_kitab=lal_kitab if not isinstance(lal_kitab, list) else None,
        kota_chakra=kota_chakra if not isinstance(kota_chakra, list) else None,
        nisheka=nisheka if not isinstance(nisheka, list) else None,
        eclipse_impacts=eclipse_impacts,
        # Phase 2
        avakhada=phase2.get("avakhada") if not isinstance(phase2.get("avakhada"), list) else None,
        bhava_madhya=phase2.get("bhava_madhya")
        if not isinstance(phase2.get("bhava_madhya"), list)
        else None,
        bhrigu_bindu=phase2.get("bhrigu_bindu")
        if not isinstance(phase2.get("bhrigu_bindu"), list)
        else None,
        drekkana=phase2.get("drekkana") if not isinstance(phase2.get("drekkana"), list) else None,
        gochara=phase2.get("gochara") if not isinstance(phase2.get("gochara"), list) else None,
        hora=phase2.get("hora") if not isinstance(phase2.get("hora"), list) else None,
        medical=phase2.get("medical") if not isinstance(phase2.get("medical"), list) else None,
        mrityu_bhaga=phase2.get("mrityu_bhaga") or [],
        pushkara=phase2.get("pushkara") or [],
        sav_pinda=phase2.get("sav_pinda")
        if not isinstance(phase2.get("sav_pinda"), list)
        else None,
        d60_analysis=phase2.get("d60_analysis")
        if not isinstance(phase2.get("d60_analysis"), list)
        else None,
        current_transits=phase2.get("current_transits")
        if not isinstance(phase2.get("current_transits"), list)
        else None,
        varga_deep=phase2.get("varga_deep", {}),
        conditional_dashas=phase2.get("conditional_dashas", {}),
        pancha_pakshi_bird=pp_bird,
    )
