"""Domain model for Ashtakavarga computation results."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AshtakavargaResult:
    """Ashtakavarga point system result from BPHS chapters 66-72.

    Contains Bhinnashtakavarga (per-planet bindu tables), Sarvashtakavarga
    (aggregate across all contributors per sign), and the total bindu count
    which must always equal 337 for a valid computation.

    Attributes:
        bhinna: Per-planet bindu tables. Keys are planet names (Sun..Saturn),
                values are lists of 12 integers (one per sign, Aries..Pisces).
        sarva: Sarvashtakavarga — sum of all 7 Bhinna tables per sign (12 values).
        total: Sum of all Sarvashtakavarga values (must equal 337).
    """

    bhinna: dict[str, list[int]] = field(default_factory=dict)
    sarva: list[int] = field(default_factory=list)
    total: int = 0
