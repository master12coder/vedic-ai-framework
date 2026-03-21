"""Tests for Sripati Paddhati Bhava Madhya and Sandhi computation.

Fixture: Manish Chaurasia — 13/03/1989, 12:17 PM, Varanasi
Lagna: Mithuna (Gemini)
"""

from __future__ import annotations

from daivai_engine.compute.bhava_madhya import (
    SANDHI_THRESHOLD,
    compute_sripati_bhava_madhya,
    compute_sripati_madhyas,
    get_planets_near_madhya,
    get_sandhi_planets,
)
from daivai_engine.constants import FULL_CIRCLE_DEG, PLANETS
from daivai_engine.models.bhava_madhya import (
    BhavaMadhya,
    PlanetSandhiStatus,
    SripatiBhavaMadhyaResult,
)
from daivai_engine.models.chart import ChartData


class TestSripatiMadhyas:
    """Tests for the core Madhya computation."""

    def test_returns_12_madhyas(self, manish_chart: ChartData) -> None:
        madhyas = compute_sripati_madhyas(manish_chart)
        assert len(madhyas) == 12

    def test_madhya_keys_are_1_to_12(self, manish_chart: ChartData) -> None:
        madhyas = compute_sripati_madhyas(manish_chart)
        assert set(madhyas.keys()) == set(range(1, 13))

    def test_all_madhyas_in_valid_range(self, manish_chart: ChartData) -> None:
        madhyas = compute_sripati_madhyas(manish_chart)
        for h, lon in madhyas.items():
            assert 0.0 <= lon < 360.0, f"House {h} Madhya={lon} out of range"

    def test_bhava1_madhya_equals_lagna(self, manish_chart: ChartData) -> None:
        """Sripati: ASC = Madhya of Bhava 1 (the defining property of this system)."""
        madhyas = compute_sripati_madhyas(manish_chart)
        # The Bhava 1 Madhya should equal the Lagna longitude
        lagna = manish_chart.lagna_longitude
        assert abs(madhyas[1] - lagna) < 0.01, (
            f"Bhava 1 Madhya={madhyas[1]:.4f} should equal Lagna={lagna:.4f}"
        )

    def test_bhava4_is_opposite_bhava10(self, manish_chart: ChartData) -> None:
        """IC = MC + 180°, so Bhava 4 and 10 Madhyas are exactly opposite."""
        madhyas = compute_sripati_madhyas(manish_chart)
        diff = abs(madhyas[4] - madhyas[10])
        if diff > 180:
            diff = 360 - diff
        assert abs(diff - 180.0) < 0.01, (
            f"Bhava 4 ({madhyas[4]:.4f}) and 10 ({madhyas[10]:.4f}) should be 180° apart"
        )

    def test_bhava7_is_opposite_bhava1(self, manish_chart: ChartData) -> None:
        """DSC = ASC + 180°, so Bhava 7 and 1 Madhyas are exactly opposite."""
        madhyas = compute_sripati_madhyas(manish_chart)
        diff = abs(madhyas[7] - madhyas[1])
        if diff > 180:
            diff = 360 - diff
        assert abs(diff - 180.0) < 0.01, (
            f"Bhava 7 ({madhyas[7]:.4f}) and 1 ({madhyas[1]:.4f}) should be 180° apart"
        )

    def test_madhyas_all_in_valid_range_sanity(self, manish_chart: ChartData) -> None:
        """Sanity check: all Madhya longitudes are within 0-360°."""
        madhyas = compute_sripati_madhyas(manish_chart)
        for _h, lon in madhyas.items():
            assert 0.0 <= lon < 360.0


class TestSripatiBhavaMadhya:
    """Tests for the full Bhava Madhya result."""

    def test_returns_correct_type(self, manish_chart: ChartData) -> None:
        result = compute_sripati_bhava_madhya(manish_chart)
        assert isinstance(result, SripatiBhavaMadhyaResult)

    def test_has_12_bhavas(self, manish_chart: ChartData) -> None:
        result = compute_sripati_bhava_madhya(manish_chart)
        assert len(result.bhavas) == 12

    def test_bhavas_keyed_1_to_12(self, manish_chart: ChartData) -> None:
        result = compute_sripati_bhava_madhya(manish_chart)
        assert set(result.bhavas.keys()) == set(range(1, 13))

    def test_all_madhya_longitudes_valid(self, manish_chart: ChartData) -> None:
        result = compute_sripati_bhava_madhya(manish_chart)
        for h, bm in result.bhavas.items():
            assert 0.0 <= bm.madhya_longitude < 360.0, (
                f"Bhava {h} madhya={bm.madhya_longitude} out of range"
            )

    def test_all_sandhi_longitudes_valid(self, manish_chart: ChartData) -> None:
        result = compute_sripati_bhava_madhya(manish_chart)
        for h, bm in result.bhavas.items():
            assert 0.0 <= bm.sandhi_longitude < 360.0, (
                f"Bhava {h} sandhi={bm.sandhi_longitude} out of range"
            )

    def test_arc_spans_sum_to_360(self, manish_chart: ChartData) -> None:
        """12 Bhava arc spans must sum to 360°."""
        result = compute_sripati_bhava_madhya(manish_chart)
        total = sum(bm.arc_span for bm in result.bhavas.values())
        assert abs(total - FULL_CIRCLE_DEG) < 0.1, (
            f"Arc spans sum to {total:.4f}°, expected 360°"
        )

    def test_bhava_models_are_correct_type(self, manish_chart: ChartData) -> None:
        result = compute_sripati_bhava_madhya(manish_chart)
        for bm in result.bhavas.values():
            assert isinstance(bm, BhavaMadhya)

    def test_all_planets_present(self, manish_chart: ChartData) -> None:
        result = compute_sripati_bhava_madhya(manish_chart)
        for planet in PLANETS:
            assert planet in result.planet_status, f"{planet} missing from planet_status"

    def test_planet_bhava_in_range(self, manish_chart: ChartData) -> None:
        result = compute_sripati_bhava_madhya(manish_chart)
        for name, ps in result.planet_status.items():
            assert 1 <= ps.bhava <= 12, f"{name} bhava={ps.bhava} out of 1-12"

    def test_planet_status_type(self, manish_chart: ChartData) -> None:
        result = compute_sripati_bhava_madhya(manish_chart)
        for ps in result.planet_status.values():
            assert isinstance(ps, PlanetSandhiStatus)

    def test_distance_to_sandhi_non_negative(self, manish_chart: ChartData) -> None:
        result = compute_sripati_bhava_madhya(manish_chart)
        for name, ps in result.planet_status.items():
            assert ps.distance_to_sandhi >= 0.0, (
                f"{name} distance_to_sandhi={ps.distance_to_sandhi} is negative"
            )

    def test_distance_to_madhya_non_negative(self, manish_chart: ChartData) -> None:
        result = compute_sripati_bhava_madhya(manish_chart)
        for name, ps in result.planet_status.items():
            assert ps.distance_to_madhya >= 0.0, (
                f"{name} distance_to_madhya={ps.distance_to_madhya} is negative"
            )

    def test_is_in_sandhi_consistent_with_distance(self, manish_chart: ChartData) -> None:
        """is_in_sandhi must match distance_to_sandhi < SANDHI_THRESHOLD."""
        result = compute_sripati_bhava_madhya(manish_chart)
        for name, ps in result.planet_status.items():
            expected = ps.distance_to_sandhi < SANDHI_THRESHOLD
            assert ps.is_in_sandhi == expected, (
                f"{name}: is_in_sandhi={ps.is_in_sandhi} but dist={ps.distance_to_sandhi:.4f}"
                f" threshold={SANDHI_THRESHOLD:.4f}"
            )

    def test_method_label(self, manish_chart: ChartData) -> None:
        result = compute_sripati_bhava_madhya(manish_chart)
        assert result.method == "Sripati Paddhati"

    def test_bhava1_madhya_at_lagna(self, manish_chart: ChartData) -> None:
        """The core Sripati property: Bhava 1 Madhya = Ascendant."""
        result = compute_sripati_bhava_madhya(manish_chart)
        bhava1_madhya = result.bhavas[1].madhya_longitude
        lagna = manish_chart.lagna_longitude
        assert abs(bhava1_madhya - lagna) < 0.01, (
            f"Bhava 1 Madhya {bhava1_madhya:.4f} ≠ Lagna {lagna:.4f}"
        )


class TestSandhiHelpers:
    """Tests for helper functions."""

    def test_get_sandhi_planets_returns_list(self, manish_chart: ChartData) -> None:
        sandhi_planets = get_sandhi_planets(manish_chart)
        assert isinstance(sandhi_planets, list)

    def test_sandhi_planets_are_actually_in_sandhi(self, manish_chart: ChartData) -> None:
        sandhi_planets = get_sandhi_planets(manish_chart)
        for ps in sandhi_planets:
            assert ps.is_in_sandhi is True

    def test_get_planets_near_madhya_returns_list(self, manish_chart: ChartData) -> None:
        near_madhya = get_planets_near_madhya(manish_chart)
        assert isinstance(near_madhya, list)

    def test_near_madhya_planets_within_threshold(self, manish_chart: ChartData) -> None:
        threshold = 5.0
        near_madhya = get_planets_near_madhya(manish_chart, threshold=threshold)
        for ps in near_madhya:
            assert ps.distance_to_madhya <= threshold, (
                f"{ps.name}: distance_to_madhya={ps.distance_to_madhya} > threshold={threshold}"
            )

    def test_sandhi_planets_subset_of_all_planets(self, manish_chart: ChartData) -> None:
        result = compute_sripati_bhava_madhya(manish_chart)
        sandhi_planets = get_sandhi_planets(manish_chart)
        all_planet_names = set(result.planet_status.keys())
        for ps in sandhi_planets:
            assert ps.name in all_planet_names


class TestSandhiThreshold:
    """Tests for the 3°20' sandhi threshold constant."""

    def test_sandhi_threshold_is_3_degrees_20_minutes(self) -> None:
        """SANDHI_THRESHOLD must be exactly 3°20' = 10/3 degrees."""
        expected = 10.0 / 3.0  # 3.333...°
        assert abs(SANDHI_THRESHOLD - expected) < 1e-9
