"""Tests for mantra computation module.

Primary fixture: manish_chart - Manish Chaurasia, Mithuna lagna (Gemini).
Known Mithuna facts:
  Lagna lord = Mercury
  Moon = Rohini Pada 2 → nakshatra lord = Moon, deity = Brahma/Prajapati
  Dasha proxy lord (Moon nakshatra lord) = Moon
"""

from __future__ import annotations

import pytest

from daivai_engine.compute.mantra import (
    compute_remedy_mantras,
    get_mantra_for_planet,
    get_nakshatra_mantra,
    get_nakshatra_mantra_by_number,
)
from daivai_engine.knowledge.loader import load_mantra_rules
from daivai_engine.models.chart import ChartData
from daivai_engine.models.remedies import MantraRecommendation, NakshatraMantra


# ── Knowledge YAML tests ──────────────────────────────────────────────────────


def test_mantra_rules_yaml_loads_all_nine_planets() -> None:
    """mantra_rules.yaml must contain all 9 Vedic grahas."""
    rules = load_mantra_rules()
    planets = rules.get("planets", {})
    expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
    assert expected == set(planets.keys())


def test_mantra_rules_yaml_has_27_nakshatra_mantras() -> None:
    """mantra_rules.yaml must have exactly 27 nakshatra deity mantras."""
    rules = load_mantra_rules()
    entries = rules.get("nakshatra_mantras", [])
    assert len(entries) == 27


def test_nakshatra_mantras_have_sequential_numbers() -> None:
    """Nakshatra numbers must be sequential 1-27 with no gaps."""
    rules = load_mantra_rules()
    entries = rules.get("nakshatra_mantras", [])
    numbers = sorted(e["number"] for e in entries)
    assert numbers == list(range(1, 28))


def test_mantra_rules_yaml_required_fields_per_planet() -> None:
    """Each planet entry must have beej, beej_mantra, japa_daily, japa_total."""
    rules = load_mantra_rules()
    for planet, data in rules.get("planets", {}).items():
        assert "beej" in data, f"{planet} missing beej"
        assert "beej_mantra" in data, f"{planet} missing beej_mantra"
        assert "japa_daily" in data, f"{planet} missing japa_daily"
        assert "japa_total" in data, f"{planet} missing japa_total"
        assert "gayatri" in data, f"{planet} missing gayatri"


def test_japa_totals_are_multiples_of_1000() -> None:
    """Traditional japa_total values are always multiples of 1000."""
    rules = load_mantra_rules()
    for planet, data in rules.get("planets", {}).items():
        total = data["japa_total"]
        assert total % 1000 == 0, f"{planet} japa_total {total} is not multiple of 1000"


# ── get_mantra_for_planet ─────────────────────────────────────────────────────


def test_get_mantra_for_mercury_returns_correct_beej() -> None:
    """Mercury's beej must be 'ब्रीं'."""
    rec = get_mantra_for_planet("Mercury")
    assert rec is not None
    assert rec.beej == "ब्रीं"


def test_get_mantra_for_sun_japa_total_is_7000() -> None:
    """Sun's japa_total for graha shanti must be 7000."""
    rec = get_mantra_for_planet("Sun")
    assert rec is not None
    assert rec.japa_total == 7000


def test_get_mantra_for_saturn_best_day_is_saturday() -> None:
    """Saturn mantra is always recited on Saturday."""
    rec = get_mantra_for_planet("Saturn")
    assert rec is not None
    assert "Saturday" in rec.best_day


def test_get_mantra_for_unknown_planet_returns_none() -> None:
    """Unknown planet name must return None gracefully."""
    rec = get_mantra_for_planet("Pluto")
    assert rec is None


def test_get_mantra_returns_mantra_recommendation_type() -> None:
    """get_mantra_for_planet must return a MantraRecommendation instance."""
    rec = get_mantra_for_planet("Jupiter")
    assert isinstance(rec, MantraRecommendation)


def test_all_nine_planets_return_valid_mantra() -> None:
    """All 9 Vedic planets must return a MantraRecommendation."""
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    for planet in planets:
        rec = get_mantra_for_planet(planet)
        assert rec is not None, f"{planet} returned None"
        assert rec.beej_mantra != "", f"{planet} has empty beej_mantra"


def test_get_mantra_for_rahu_deity_is_durga() -> None:
    """Rahu's presiding deity must be Devi Durga / Kali."""
    rec = get_mantra_for_planet("Rahu")
    assert rec is not None
    assert "Durga" in rec.deity


def test_get_mantra_for_ketu_deity_is_ganesha() -> None:
    """Ketu's presiding deity must be Lord Ganesha."""
    rec = get_mantra_for_planet("Ketu")
    assert rec is not None
    assert "Ganesha" in rec.deity


# ── get_nakshatra_mantra ──────────────────────────────────────────────────────


def test_get_nakshatra_mantra_rohini_returns_brahma() -> None:
    """Rohini's presiding deity must be Brahma / Prajapati."""
    mantra = get_nakshatra_mantra("Rohini")
    assert mantra is not None
    assert "Brahma" in mantra.deity or "Prajapati" in mantra.deity


def test_get_nakshatra_mantra_ashwini_number_is_1() -> None:
    """Ashwini is nakshatra number 1."""
    mantra = get_nakshatra_mantra("Ashwini")
    assert mantra is not None
    assert mantra.nakshatra_number == 1


def test_get_nakshatra_mantra_revati_deity_is_pushan() -> None:
    """Revati (nakshatra 27) is ruled by Pushan."""
    mantra = get_nakshatra_mantra("Revati")
    assert mantra is not None
    assert "Pushan" in mantra.deity


def test_get_nakshatra_mantra_case_insensitive() -> None:
    """Nakshatra lookup must be case-insensitive."""
    m1 = get_nakshatra_mantra("Rohini")
    m2 = get_nakshatra_mantra("rohini")
    assert m1 is not None
    assert m2 is not None
    assert m1.nakshatra_number == m2.nakshatra_number


def test_get_nakshatra_mantra_unknown_returns_none() -> None:
    """Unknown nakshatra name must return None gracefully."""
    mantra = get_nakshatra_mantra("Zeta Reticuli")
    assert mantra is None


def test_get_nakshatra_mantra_by_number_returns_correct_entry() -> None:
    """Lookup by number=4 must return Rohini."""
    mantra = get_nakshatra_mantra_by_number(4)
    assert mantra is not None
    assert mantra.nakshatra_en == "Rohini"


def test_get_nakshatra_mantra_returns_nakshatra_mantra_type() -> None:
    """Must return a NakshatraMantra instance."""
    mantra = get_nakshatra_mantra("Pushya")
    assert isinstance(mantra, NakshatraMantra)


# ── compute_remedy_mantras ────────────────────────────────────────────────────


def test_compute_remedy_mantras_includes_lagna_lord(manish_chart: ChartData) -> None:
    """Mercury (Mithuna lagna lord) must always be in Manish's mantra plan."""
    recs = compute_remedy_mantras(manish_chart)
    planets = [r.planet for r in recs]
    assert "Mercury" in planets


def test_compute_remedy_mantras_lagna_lord_is_first(manish_chart: ChartData) -> None:
    """Lagna lord must be the first (highest-priority) mantra."""
    recs = compute_remedy_mantras(manish_chart)
    assert len(recs) >= 1
    assert recs[0].planet == "Mercury"


def test_compute_remedy_mantras_returns_at_most_five(manish_chart: ChartData) -> None:
    """Remedy mantras must not exceed 5 - prevents practice overload."""
    recs = compute_remedy_mantras(manish_chart)
    assert len(recs) <= 5


def test_compute_remedy_mantras_no_duplicate_planets(manish_chart: ChartData) -> None:
    """Each planet must appear at most once in the mantra plan."""
    recs = compute_remedy_mantras(manish_chart)
    planets = [r.planet for r in recs]
    assert len(planets) == len(set(planets))


def test_compute_remedy_mantras_each_has_nonempty_reason(manish_chart: ChartData) -> None:
    """Every recommendation must have a non-empty reason string."""
    recs = compute_remedy_mantras(manish_chart)
    for rec in recs:
        assert rec.reason != "", f"{rec.planet} has empty reason"


def test_compute_remedy_mantras_returns_list_type(manish_chart: ChartData) -> None:
    """Return type must be list of MantraRecommendation."""
    recs = compute_remedy_mantras(manish_chart)
    assert isinstance(recs, list)
    for rec in recs:
        assert isinstance(rec, MantraRecommendation)


def test_compute_remedy_mantras_all_have_japa_counts(manish_chart: ChartData) -> None:
    """All recommendations must have positive japa_daily and japa_total."""
    recs = compute_remedy_mantras(manish_chart)
    for rec in recs:
        assert rec.japa_daily > 0
        assert rec.japa_total > 0


@pytest.mark.safety
def test_compute_remedy_mantras_sample_chart(sample_chart: ChartData) -> None:
    """compute_remedy_mantras must work on any valid chart without error."""
    recs = compute_remedy_mantras(sample_chart)
    assert isinstance(recs, list)
    assert len(recs) >= 1
