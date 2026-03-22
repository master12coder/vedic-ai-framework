"""Nabhasa Sankhya Yoga detection — BPHS Chapter 13."""

from __future__ import annotations

from daivai_engine.compute.nabhasa_ashraya_dala import _r
from daivai_engine.models.yoga import YogaResult


_SANKHYA_MAP: dict[int, tuple[str, str, str, str]] = {
    1: (
        "Vallaki Yoga",
        "वल्लकी योग",
        "All 7 planets in 1 house — Veena (lute), musical, artistic, royal performer",
        "benefic",
    ),
    2: (
        "Dama Yoga",
        "दाम योग",
        "All 7 planets in 2 houses — garland, community leader, generous and wealthy",
        "benefic",
    ),
    3: (
        "Paasha Yoga",
        "पाश योग",
        "All 7 planets in 3 houses — noose, scheming, enslaved to work and duties",
        "malefic",
    ),
    4: (
        "Kedara Yoga",
        "केदार योग",
        "All 7 planets in 4 houses — field, helps many, service-oriented life",
        "mixed",
    ),
    5: (
        "Shoola Yoga",
        "शूल योग",
        "All 7 planets in 5 houses — trident, combative, faces many hardships",
        "malefic",
    ),
    6: (
        "Yuga Yoga",
        "युग योग",
        "All 7 planets in 6 houses — yoke, heretical views, poor and wretched",
        "malefic",
    ),
    7: (
        "Gola Yoga",
        "गोल योग",
        "All 7 planets in 7 houses — sphere, lonely, impoverished, helpless",
        "malefic",
    ),
}


def _sankhya_yoga(n_houses: int) -> YogaResult | None:
    """Return the applicable Sankhya Yoga based on distinct houses occupied. BPHS 13.28-34.

    Exactly one Sankhya yoga applies (they are mutually exclusive by definition).
    Maximum n_houses for 7 planets is 7.
    """
    count = min(n_houses, 7)
    entry = _SANKHYA_MAP.get(count)
    if not entry:
        return None
    name, name_hi, desc, effect = entry
    return _r(name, name_hi, [], desc, effect)
