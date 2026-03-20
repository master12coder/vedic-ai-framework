"""Tests that validate YAML knowledge files against Python constants.

Ensures the YAML (auditable by Pandits) matches the code (used in computation).
Any discrepancy means either the YAML or the code needs fixing.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from daivai_engine.constants import (
    COMBUSTION_LIMITS,
    DASHA_SEQUENCE,
    DASHA_YEARS,
    EXALTATION,
    EXALTATION_DEGREE,
    NAKSHATRA_LORDS,
    NAKSHATRAS,
    NATURAL_FRIENDS,
    SIGN_LORDS,
)


_KNOWLEDGE = Path(__file__).parent.parent.parent / "engine" / "src" / "daivai_engine" / "knowledge"


def _load(name: str) -> dict:
    with open(_KNOWLEDGE / name) as f:
        return yaml.safe_load(f)


class TestDignityYamlMatchesConstants:
    def test_exaltation_signs_match(self) -> None:
        data = _load("dignity.yaml")
        for planet, info in data["planets"].items():
            expected_sign = EXALTATION.get(planet)
            actual_sign = info["exaltation"]["sign_index"]
            assert expected_sign == actual_sign, f"{planet} exaltation mismatch"

    def test_exaltation_degrees_match(self) -> None:
        data = _load("dignity.yaml")
        for planet, info in data["planets"].items():
            expected_deg = EXALTATION_DEGREE.get(planet)
            actual_deg = info["exaltation"]["exact_degree"]
            assert expected_deg == actual_deg, f"{planet} exaltation degree mismatch"

    def test_friends_match(self) -> None:
        data = _load("dignity.yaml")
        for planet, info in data["planets"].items():
            if "friends" in info:
                expected = set(NATURAL_FRIENDS.get(planet, []))
                actual = set(info["friends"])
                assert expected == actual, f"{planet} friends mismatch: {expected} vs {actual}"


class TestVimshottariYamlMatchesConstants:
    def test_sequence_matches(self) -> None:
        data = _load("vimshottari_dasha.yaml")
        yaml_seq = [entry["planet"] for entry in data["sequence"]]
        assert yaml_seq == DASHA_SEQUENCE

    def test_years_match(self) -> None:
        data = _load("vimshottari_dasha.yaml")
        for entry in data["sequence"]:
            assert DASHA_YEARS[entry["planet"]] == entry["years"]

    def test_total_120(self) -> None:
        data = _load("vimshottari_dasha.yaml")
        assert data["total_years"] == 120

    def test_nakshatra_lords_match(self) -> None:
        data = _load("vimshottari_dasha.yaml")
        for nak, lord in data["nakshatra_to_lord"].items():
            idx = NAKSHATRAS.index(nak)
            assert NAKSHATRA_LORDS[idx] == lord, f"{nak} lord mismatch"


class TestSignPropertiesYaml:
    def test_twelve_signs(self) -> None:
        data = _load("sign_properties.yaml")
        assert len(data["signs"]) == 12

    def test_rulers_match_constants(self) -> None:
        data = _load("sign_properties.yaml")
        for sign in data["signs"]:
            idx = sign["index"]
            assert SIGN_LORDS[idx] == sign["ruler"], f"Sign {idx} ruler mismatch"


class TestAshtakavargaYaml:
    def test_seven_planets(self) -> None:
        data = _load("ashtakavarga_tables.yaml")
        assert len(data["planets"]) == 7

    def test_sav_total_documented(self) -> None:
        data = _load("ashtakavarga_tables.yaml")
        assert data["sav_total"] == 337


class TestCombustionYaml:
    def test_limits_match_constants(self) -> None:
        data = _load("combustion.yaml")
        limits = data["combustion_limits"]
        for planet, limit in COMBUSTION_LIMITS.items():
            yaml_limit = limits.get(planet, {})
            if isinstance(yaml_limit, dict):
                actual = yaml_limit.get(
                    "normal", yaml_limit.get("direct", yaml_limit.get("degrees"))
                )
            else:
                actual = yaml_limit
            assert actual == limit, (
                f"{planet} combustion limit mismatch: YAML={actual} vs code={limit}"
            )


class TestDoshaDefinitionsYaml:
    def test_ten_doshas_defined(self) -> None:
        data = _load("dosha_definitions.yaml")
        assert len(data) >= 10

    def test_each_has_source(self) -> None:
        data = _load("dosha_definitions.yaml")
        for name, info in data.items():
            if isinstance(info, dict) and "source" in info:
                assert info["source"], f"{name} missing source"


class TestHouseSignificationsYaml:
    def test_twelve_houses(self) -> None:
        data = _load("house_significations.yaml")
        assert len(data["houses"]) == 12

    def test_each_has_karaka(self) -> None:
        data = _load("house_significations.yaml")
        for house_num, info in data["houses"].items():
            assert "natural_karaka" in info, f"House {house_num} missing karaka"


class TestShadbalaReferenceYaml:
    def test_naisargika_values(self) -> None:
        """Verify Naisargika Bala values match BPHS exactly."""
        data = _load("shadbala_reference.yaml")
        values = data["naisargika_bala"]["values"]
        assert values["Sun"] == 60.00
        assert values["Moon"] == 51.43
        assert values["Saturn"] == 8.57

    def test_required_shadbala_values(self) -> None:
        data = _load("shadbala_reference.yaml")
        values = data["required_shadbala"]["values"]
        from daivai_engine.compute.strength import REQUIRED_SHADBALA

        for planet, req in REQUIRED_SHADBALA.items():
            assert values[planet] == req, f"{planet} required shadbala mismatch"
