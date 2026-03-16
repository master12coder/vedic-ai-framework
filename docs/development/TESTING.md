# Testing Guide

## Test Pyramid

```
         ╱╲
        ╱E2E╲        ~5 tests   — Full report generation with LLM
       ╱──────╲
      ╱ Integ. ╲     ~20 tests  — Pipeline, corrections, scripture
     ╱──────────╲
    ╱   Unit     ╲   ~200 tests — Computation, models, individual modules
   ╱──────────────╲
```

## Running Tests

```bash
make test             # full suite (~4 seconds)
make test-v           # verbose output
make test-cov         # with coverage
make test-safety      # safety-critical tests only
make test-fast        # unit tests only (skip integration)

pytest -k "mithuna"   # tests matching keyword
pytest -x             # stop on first failure
pytest tests/compute/ # specific directory
```

## Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_chart.py            # Core chart computation
├── test_dasha.py            # Dasha calculations
├── test_dosha.py            # Dosha detection
├── test_yoga.py             # Yoga detection
├── test_matching.py         # Compatibility matching
├── test_panchang.py         # Panchang elements
├── test_corrections.py      # Pandit correction system
├── test_llm_backend.py      # LLM backend factory
├── compute/                 # Computation subsystem tests
│   ├── test_ashtakavarga.py
│   ├── test_bhava_chalit.py
│   ├── test_divisional.py
│   ├── test_kp.py
│   ├── test_shadbala.py
│   └── test_upagraha.py
├── integration/             # Integration pipeline tests
│   └── test_full_pipeline.py
├── learn/                   # Learning system tests
│   ├── test_life_events.py
│   ├── test_prediction_tracker.py
│   ├── test_trust_scorer.py
│   └── test_validator.py
└── scriptures/              # Scripture database tests
    └── test_scripture_db.py
```

## Naming Convention

```python
def test_<what>_<condition>_<expected>():
    """<What> should <expected> when <condition>."""

# Examples:
def test_mithuna_lagna_jupiter_is_maraka():
    """Jupiter should be classified as maraka for Mithuna lagna."""

def test_gemstone_validation_catches_prohibited_pukhraj():
    """Validation should flag Yellow Sapphire recommendation for Mithuna."""

def test_chart_computation_lagna_matches_expected():
    """Chart computation should produce correct lagna for known input."""
```

## Primary Fixture

The **reference chart** used across the test suite:

```python
@pytest.fixture
def manish_chart() -> ChartData:
    """Reference chart: Manish Chaurasia — verified data."""
    return compute_chart(
        name="Manish Chaurasia",
        dob="13/03/1989",
        tob="12:17",
        lat=25.3176,
        lon=83.0067,
        tz_name="Asia/Kolkata",
        gender="Male",
    )
```

**Known verified values for this chart:**
- Lagna: Mithuna (Gemini) at 13.1 degrees
- Moon: Vrishabha (exalted) in Rohini nakshatra, pada 2
- Moon house: 12
- Jupiter: Vrishabha, house 12
- Current Mahadasha: Jupiter (maraka for Mithuna)

## Writing Safety Tests

Safety tests verify that gemstone recommendations and interpretations don't
produce dangerous output. These are the most important tests.

```python
import pytest

@pytest.mark.safety
def test_mithuna_pukhraj_prohibited(manish_chart):
    """Yellow Sapphire must NEVER be recommended for Mithuna lagna."""
    from jyotish.interpret.interpreter import (
        _build_lordship_context,
        validate_interpretation,
    )
    ctx = _build_lordship_context(manish_chart.lagna_sign)
    prohibited = [s["stone"] for s in ctx.get("prohibited_stones", [])]
    assert any("Pukhraj" in s for s in prohibited)

@pytest.mark.safety
def test_validation_catches_bad_recommendation(manish_chart):
    """Post-validation should catch prohibited stone in recommendation context."""
    from jyotish.interpret.interpreter import (
        _build_lordship_context,
        validate_interpretation,
    )
    ctx = _build_lordship_context(manish_chart.lagna_sign)
    bad = "I recommend wearing Yellow Sapphire for career growth."
    _, errors = validate_interpretation(bad, manish_chart.lagna_sign, ctx)
    assert len(errors) > 0
```

## Test Markers

```python
@pytest.mark.safety      # Gemstone/interpretation safety tests
@pytest.mark.slow        # Tests taking >5 seconds (E2E with LLM)
@pytest.mark.integration # Cross-layer integration tests
```

## Coverage Targets

| Layer       | Target | Notes                              |
|-------------|--------|------------------------------------|
| `compute/`  | 90%+   | Deterministic — easy to test       |
| `domain/`   | 85%+   | Models and rules                   |
| `interpret/` | 70%+  | Validation logic, not LLM output   |
| `learn/`    | 75%+   | Correction pipeline                |
| `deliver/`  | 60%+   | Formatting is less critical        |
