"""Astronomical and geometric constants used across computation modules."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Circle geometry
# ---------------------------------------------------------------------------
FULL_CIRCLE_DEG = 360.0
HALF_CIRCLE_DEG = 180.0
NUM_SIGNS = 12
DEGREES_PER_SIGN = 30.0

# ---------------------------------------------------------------------------
# Nakshatra constants
# ---------------------------------------------------------------------------
NUM_NAKSHATRAS = 27
MAX_NAKSHATRA_INDEX = 26
NAKSHATRA_SPAN_DEG = FULL_CIRCLE_DEG / NUM_NAKSHATRAS  # 13.3333...
PADAS_PER_NAKSHATRA = 4

# ---------------------------------------------------------------------------
# Ashtakavarga
# ---------------------------------------------------------------------------
SARVASHTAKAVARGA_TOTAL = 337  # Sum of all SAV bindus is always 337

# ---------------------------------------------------------------------------
# Conjunction and aspect defaults
# ---------------------------------------------------------------------------
DEFAULT_CONJUNCTION_ORB = 10.0  # Degrees within which two planets are conjunct

# ---------------------------------------------------------------------------
# Daily suggestion
# ---------------------------------------------------------------------------
MAX_DAY_RATING = 10  # Day rating scale: 1 to MAX_DAY_RATING

# ---------------------------------------------------------------------------
# Dasha sub-systems
# ---------------------------------------------------------------------------
YOGINI_TOTAL_YEARS = 36   # Sum of 1+2+3+4+5+6+7+8
ASHTOTTARI_TOTAL_YEARS = 108  # Sum of Ashtottari dasha periods
