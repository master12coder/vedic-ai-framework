# Testing Guide

## Run Tests

```bash
make test                     # Full suite (530+ tests)
make test-safety              # Safety tests only (@pytest.mark.safety)
python -m pytest tests/ -v    # Verbose
python -m pytest tests/products/plugins/kundali/ -v   # One directory
```

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures: manish_chart, sample_chart
├── engine/                        # Engine computation tests
│   ├── test_chart.py              # Chart computation, lagna, planets
│   ├── test_dasha.py              # Vimshottari MD/AD/PD
│   ├── test_yoga.py               # Yoga detection
│   ├── test_dosha.py              # Dosha detection
│   ├── test_matching.py           # Ashtakoot compatibility
│   └── compute/                   # Advanced compute modules
│       ├── test_shadbala.py       # Six-fold strength
│       ├── test_ashtakavarga.py   # Bindu system (total=337)
│       ├── test_jaimini.py        # Chara karakas, arudha padas
│       ├── test_kp.py             # KP sub-lords
│       └── test_divisional.py     # D9/D10 charts
├── products/                      # Product layer tests
│   ├── test_safety.py             # Gemstone safety (ALL lagnas)
│   ├── test_knowledge_loader.py   # YAML loading
│   ├── test_llm_backend.py        # LLM factory
│   ├── test_corrections.py        # Pandit correction store
│   └── plugins/                   # Per-plugin tests
│       ├── kundali/               # 10 test files (charts, PDF, renderers)
│       ├── remedies/              # Gemstone weight engine
│       ├── daily/                 # 3-level guidance
│       ├── matching/              # Compatibility scoring
│       ├── muhurta/               # Auspicious dates
│       ├── pandit/                # Corrections
│       └── predictions/           # Accuracy tracking
├── integration/                   # End-to-end pipeline
└── safety/                        # Dedicated gemstone safety
```

## Primary Fixture

```python
@pytest.fixture
def manish_chart() -> ChartData:
    """Manish Chaurasia: 13/03/1989, 12:17 PM, Varanasi
    Known: Lagna=Mithuna, Moon=Rohini P2, Jupiter=MARAKA, Mercury=Lagnesh"""
    return compute_chart(
        name="Manish Chaurasia", dob="13/03/1989", tob="12:17",
        lat=25.3176, lon=83.0067, tz_name="Asia/Kolkata", gender="Male",
    )
```

Use `manish_chart` for ALL product tests. Known verified values:
- Panna (Emerald) = RECOMMENDED
- Pukhraj (Yellow Sapphire) = PROHIBITED (Jupiter = 7th MARAKA)
- Moonga (Red Coral) = PROHIBITED (Mars = 6th lord)
- Moti (Pearl) = PROHIBITED (Moon = 2nd MARAKA)

## Test Naming

```
test_{what}_{expected}_{condition}
```
Examples: `test_pukhraj_prohibited_for_mithuna_lagna`, `test_panna_weight_in_expected_range`

## Markers

| Marker | Usage | Run |
|--------|-------|-----|
| `@pytest.mark.safety` | Gemstone/interpretation safety | `pytest -m safety` |
| `@pytest.mark.slow` | Heavy computation | `pytest -m "not slow"` to skip |

## Before Every Commit

```bash
make all    # = make lint + make typecheck + make test + make audit
```

All 530+ tests must pass. Zero tolerance for safety test failures.
