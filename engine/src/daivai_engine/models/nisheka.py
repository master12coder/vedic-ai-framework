"""Domain models for Nisheka (conception) chart computation.

The Nisheka chart is derived from the birth chart using BPHS Ch.4 rules.
It provides a verification mechanism: the Nisheka lagna should correspond
to the birth Moon sign, or vice versa.

Source: BPHS Ch.4 (Adhana / Nisheka Lagna).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class NishekaResult(BaseModel):
    """Result of Nisheka (conception) chart computation.

    Contains the estimated conception date, the Nisheka lagna and Moon,
    and verification flags checking BPHS consistency rules.
    """

    model_config = ConfigDict(frozen=True)

    conception_jd: float
    conception_date: str  # DD/MM/YYYY
    conception_approx_days_before_birth: float

    nisheka_lagna_sign_index: int
    nisheka_lagna_sign: str
    nisheka_moon_sign_index: int
    nisheka_moon_sign: str

    nisheka_lagna_matches_birth_moon: bool
    birth_lagna_matches_nisheka_moon: bool
    verification_passed: bool

    summary: str
