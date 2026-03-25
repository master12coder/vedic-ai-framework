# Family Bond Kundali (परिवार बंध कुण्डली)

> Cross-chart family analysis — gemstone synergy, wealth flow, dasha sync

## Status

- **Phase 1.5 (Engine)**: DONE — 6 compute modules, 3 model files, gem_therapy_core extended
- **Phase 4 (Plugin)**: NOT STARTED — plugin, prompts, CLI commands deferred

## The Discovery

Individual kundali analysis treats each person in isolation. A real Varanasi
Pandit considers cross-chart interactions:

1. **Rashyadhipati**: Rahu/Ketu give results of their sign lord's functional
   nature. Without this, Gomed was incorrectly "neutral" for Vrischik lagna
   when it should be SAFE (Rahu in Dhanu, sign lord = Jupiter = 2+5L = most benefic).

2. **Karmic Complementarity**: One spouse's prohibited stone = the other's
   recommended stone. "जो एक के लिए विष, दूसरे के लिए अमृत"

3. **Wealth Flow**: Who earns vs who accumulates — determines which spouse
   should manage finances.

4. **Conjunction Penalty**: Lagnesh conjunct Rahu/6L/8L/12L reduces gemstone
   weight (stone amplifies ALL conjunct energies).

## Engine Modules (Phase 1.5)

| Module | Purpose | Lines |
|--------|---------|-------|
| `compute/functional_nature.py` | Functional nature of any planet per lagna + Rahu/Ketu rashyadhipati | ~140 |
| `compute/cross_chart.py` | Cross-chart planetary interactions between two charts | ~210 |
| `compute/wealth_flow.py` | Earner/accumulator/distributor classification | ~120 |
| `compute/conjunction_penalty.py` | Gemstone weight penalty from malefic conjunctions | ~80 |
| `compute/family_gemstone_synergy.py` | Cross-family gemstone complementarity analysis | ~170 |
| `compute/dasha_sync.py` | Synchronised dasha timeline for family members | ~125 |
| `models/functional_nature.py` | FunctionalNature, ShadowPlanetNature | ~50 |
| `models/cross_chart.py` | PlanetOverlay, CrossChartResult | ~50 |
| `models/family_bond.py` | WealthFlowProfile, ConjunctionPenalty, FamilyGemSynergyResult, DashaSyncResult | ~110 |

### Key Extension: gem_therapy_core.py

Post-processes Rahu/Ketu via `get_shadow_planet_nature()`. Rahu/Ketu no longer
default to "neutral" — they resolve through their sign lord's functional nature
per the lagna. This is the fix for the Gomed miss.

## API

```python
# Functional nature (any planet, any lagna)
from daivai_engine.compute.functional_nature import get_functional_nature, get_shadow_planet_nature
nature = get_functional_nature("Jupiter", "Scorpio")  # yogakaraka, 2+5L
shadow = get_shadow_planet_nature("Rahu", chart)  # sign lord resolution

# Cross-chart interactions
from daivai_engine.compute.cross_chart import compute_cross_chart_interactions
result = compute_cross_chart_interactions(chart_a, chart_b)

# Wealth flow
from daivai_engine.compute.wealth_flow import classify_wealth_flow
profile = classify_wealth_flow(chart)  # "accumulator", "distributor", etc.

# Conjunction penalty
from daivai_engine.compute.conjunction_penalty import compute_conjunction_penalty
penalty = compute_conjunction_penalty(chart, "Mercury")  # penalty_factor: 0.50

# Family gemstone synergy
from daivai_engine.compute.family_gemstone_synergy import compute_family_gem_synergy
synergy = compute_family_gem_synergy([chart_a, chart_b])

# Dasha sync
from daivai_engine.compute.dasha_sync import compute_dasha_sync
sync = compute_dasha_sync([chart_a, chart_b])
```

## Validation Cases

| Case | Individual | Family Bond |
|------|-----------|-------------|
| Gomed for Vrischik lagna (Rahu in Dhanu) | neutral | SAFE (Jupiter = 2+5L) |
| Pukhraj: Manish (Mithuna) vs Vaishali (Vrischik) | Manish: prohibited | Karmic complement |
| Mercury conjunct Rahu (Manish) | Panna: recommended | Panna: recommended at 50% weight |
| Wealth flow (Manish: 2L+11L+10L in 12th) | Not analysed | Distributor pattern |

## Deferred to Phase 4

- `products/plugins/family_bond/` plugin
- LLM prompt templates (couple_analysis, wealth_strategy, gemstone_family)
- CLI commands (`daivai family bond`, `daivai family add`)
- Multi-school validation matrix (7 schools, weighted voting)
- PDF report rendering
- `family_bond_rules.yaml` knowledge file
