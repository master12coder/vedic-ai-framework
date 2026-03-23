"""Tests for dispositor tree computation.

Source: BPHS Ch.13, Phaladeepika Ch.2.
"""

from __future__ import annotations

import pytest

from daivai_engine.compute.dispositor import (
    _find_mutual_receptions,
    _get_dispositor,
    _is_in_own_sign,
    _trace_chain,
    compute_dispositor_tree,
)
from daivai_engine.constants import OWN_SIGNS, SIGN_LORDS
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dispositor import (
    DispositorTree,
    MutualReception,
)


class TestDispositorTreeStructure:
    """Tests for the overall structure of DispositorTree output."""

    def test_returns_model_instance(self, manish_chart: ChartData) -> None:
        """compute_dispositor_tree returns a DispositorTree."""
        result = compute_dispositor_tree(manish_chart)
        assert isinstance(result, DispositorTree)

    def test_chains_has_all_planets(self, manish_chart: ChartData) -> None:
        """Every planet in the chart has a dispositor chain."""
        result = compute_dispositor_tree(manish_chart)
        for planet_name in manish_chart.planets:
            assert planet_name in result.chains

    def test_chain_starts_with_planet(self, manish_chart: ChartData) -> None:
        """Each chain starts with the planet itself."""
        result = compute_dispositor_tree(manish_chart)
        for planet_name, chain in result.chains.items():
            assert chain.chain[0] == planet_name

    def test_chain_length_consistent(self, manish_chart: ChartData) -> None:
        """chain_length equals len(chain) - 1."""
        result = compute_dispositor_tree(manish_chart)
        for chain in result.chains.values():
            assert chain.chain_length == len(chain.chain) - 1

    def test_final_dispositors_non_empty(self, manish_chart: ChartData) -> None:
        """At least one final dispositor exists."""
        result = compute_dispositor_tree(manish_chart)
        assert len(result.final_dispositors) >= 1

    def test_final_dispositors_are_classical(self, manish_chart: ChartData) -> None:
        """Final dispositors are classical planets (not Rahu/Ketu)."""
        classical = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        result = compute_dispositor_tree(manish_chart)
        for fd in result.final_dispositors:
            assert fd in classical

    def test_summary_non_empty(self, manish_chart: ChartData) -> None:
        """Summary string is non-empty."""
        result = compute_dispositor_tree(manish_chart)
        assert result.summary


class TestDispositorLink:
    """Tests for individual dispositor links."""

    def test_dispositor_is_sign_lord(self, manish_chart: ChartData) -> None:
        """The dispositor of each planet is the lord of the sign it occupies."""
        for planet_name, planet_data in manish_chart.planets.items():
            link = _get_dispositor(planet_name, manish_chart)
            expected_lord = SIGN_LORDS[planet_data.sign_index]
            assert link.dispositor == expected_lord

    def test_dispositor_sign_matches_planet(self, manish_chart: ChartData) -> None:
        """Link's sign_index matches the planet's actual sign."""
        for planet_name, planet_data in manish_chart.planets.items():
            link = _get_dispositor(planet_name, manish_chart)
            assert link.sign_index == planet_data.sign_index


class TestChainTracing:
    """Tests for chain tracing logic."""

    def test_own_sign_planet_self_terminates_classical(self, manish_chart: ChartData) -> None:
        """A classical planet in its own sign has itself as final dispositor."""
        classical = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        for planet_name, planet_data in manish_chart.planets.items():
            if planet_name not in classical:
                continue
            own = OWN_SIGNS.get(planet_name, [])
            if planet_data.sign_index in own:
                chain = _trace_chain(planet_name, manish_chart)
                assert chain.final_dispositor == planet_name
                assert chain.chain_length <= 1

    def test_chain_terminates(self, manish_chart: ChartData) -> None:
        """Every chain terminates (no infinite loops)."""
        for planet_name in manish_chart.planets:
            chain = _trace_chain(planet_name, manish_chart)
            assert chain.final_dispositor is not None
            assert len(chain.chain) >= 1

    def test_chain_no_duplicate_except_loop(self, manish_chart: ChartData) -> None:
        """Chain elements are unique unless a loop is detected."""
        for planet_name in manish_chart.planets:
            chain = _trace_chain(planet_name, manish_chart)
            if not chain.is_in_loop:
                # All elements should be unique except possibly the final dispositor
                # which may appear at the end if it was already in the chain
                seen = set()
                for p in chain.chain:
                    if p in seen and p != chain.final_dispositor:
                        pytest.fail(f"Duplicate {p} in non-loop chain for {planet_name}")
                    seen.add(p)


class TestMutualReception:
    """Tests for mutual reception (parivartana) detection."""

    def test_mutual_receptions_are_valid_pairs(self, manish_chart: ChartData) -> None:
        """Each mutual reception has two distinct planets."""
        receptions = _find_mutual_receptions(manish_chart)
        for mr in receptions:
            assert isinstance(mr, MutualReception)
            assert mr.planet_a != mr.planet_b

    def test_mutual_reception_sign_exchange(self, manish_chart: ChartData) -> None:
        """In a mutual reception, A is in B's sign and B is in A's sign."""
        receptions = _find_mutual_receptions(manish_chart)
        for mr in receptions:
            # A is in a sign owned by B
            assert SIGN_LORDS[mr.sign_a] == mr.planet_b
            # B is in a sign owned by A
            assert SIGN_LORDS[mr.sign_b] == mr.planet_a

    def test_no_duplicate_pairs(self, manish_chart: ChartData) -> None:
        """No duplicate mutual reception pairs (A-B and B-A counted once)."""
        receptions = _find_mutual_receptions(manish_chart)
        pairs = [tuple(sorted([mr.planet_a, mr.planet_b])) for mr in receptions]
        assert len(pairs) == len(set(pairs))


class TestOwnSignDetection:
    """Tests for own-sign check helper."""

    def test_sun_in_leo_is_own_sign(self, manish_chart: ChartData) -> None:
        """Sun in Leo (index 4) should be detected as own sign."""
        sun = manish_chart.planets["Sun"]
        if sun.sign_index == 4:
            assert _is_in_own_sign("Sun", manish_chart)

    def test_rahu_own_sign_check(self, manish_chart: ChartData) -> None:
        """Rahu has co-lordship of Aquarius (10) per OWN_SIGNS."""
        rahu = manish_chart.planets["Rahu"]
        expected = rahu.sign_index in OWN_SIGNS.get("Rahu", [])
        assert _is_in_own_sign("Rahu", manish_chart) == expected


class TestDispositorTreeManish:
    """Tests with the known Manish Chaurasia chart (Mithuna lagna)."""

    def test_has_single_flag_consistent(self, manish_chart: ChartData) -> None:
        """has_single_final_dispositor matches length of final_dispositors."""
        result = compute_dispositor_tree(manish_chart)
        assert result.has_single_final_dispositor == (len(result.final_dispositors) == 1)

    def test_all_chains_converge_when_single(self, manish_chart: ChartData) -> None:
        """If single final dispositor, all chains point to same planet."""
        result = compute_dispositor_tree(manish_chart)
        if result.has_single_final_dispositor:
            fd = result.final_dispositors[0]
            for chain in result.chains.values():
                assert chain.final_dispositor == fd

    def test_dispositor_tree_with_sample_chart(self, sample_chart: ChartData) -> None:
        """Dispositor tree computation works for a second chart too."""
        result = compute_dispositor_tree(sample_chart)
        assert isinstance(result, DispositorTree)
        assert len(result.chains) == len(sample_chart.planets)

    def test_rahu_ketu_not_final_dispositor(self, manish_chart: ChartData) -> None:
        """Rahu and Ketu should not appear as final dispositors."""
        result = compute_dispositor_tree(manish_chart)
        assert "Rahu" not in result.final_dispositors
        assert "Ketu" not in result.final_dispositors
