# Gemstone Safety Guide

## Why This Matters

In Vedic astrology, gemstones strengthen the planet they represent. Wearing
the **wrong** gemstone — particularly one for a maraka (death-inflicting) or
functional malefic planet — can cause real harm: health problems, financial
loss, relationship damage.

This is the most safety-critical aspect of the DaivAI.

## Core Principle

> **Never strengthen what should not be strengthened.**

A planet that is a maraka or functional malefic for a specific lagna should
NOT be strengthened via its gemstone, regardless of its natural beneficence.

**Example:** Jupiter is universally considered a "great benefic" — but for
Mithuna (Gemini) lagna, Jupiter owns the 7th house (maraka sthana) and 10th
house (kendra, causing Kendradhipati dosha). Recommending Yellow Sapphire
(Pukhraj) for a Mithuna native can activate Jupiter's maraka effects.

## Gemstone Decision Framework

### Always Safe
- **Lagnesh stone** — the ascendant lord's gemstone is always beneficial
- **Yogakaraka stone** — the planet owning both kendra + trikona

### Use With Caution
- **Debilitated planet stone** — test for 3 days before committing
- **Mixed lordship stone** (e.g., 8th+9th) — consult lordship rules
- **Blue Sapphire (Neelam)** — always trial for 3-5 nights on pillow

### Never Recommend
- **Maraka planet stone** — lords of 2nd and 7th houses
- **Pure functional malefic stone** — lords of 6th, 8th, 12th (unless also trikona)
- **Enemy group stones together** — Sun-Saturn, Moon-Rahu, Jupiter-Venus

## Lagna-Specific Quick Reference

| Lagna      | Lagnesh Stone        | Yogakaraka Stone      | PROHIBITED Stones                |
|------------|----------------------|-----------------------|----------------------------------|
| Mesha      | Red Coral (Mars)     | Ruby (Sun)            | Diamond (Venus), Emerald (Mercury) |
| Vrishabha  | Diamond (Venus)      | Blue Sapphire (Saturn) | Ruby (Sun), Red Coral (Mars)    |
| Mithuna    | Emerald (Mercury)    | Diamond (Venus)       | Yellow Sapphire (Jupiter), Red Coral (Mars), Pearl (Moon) |
| Karka      | Pearl (Moon)         | Red Coral (Mars)      | Blue Sapphire (Saturn), Emerald (Mercury) |
| Simha      | Ruby (Sun)           | Red Coral (Mars)      | Diamond (Venus), Blue Sapphire (Saturn) |
| Kanya      | Emerald (Mercury)    | Diamond (Venus)       | Yellow Sapphire (Jupiter), Red Coral (Mars) |
| Tula       | Diamond (Venus)      | Blue Sapphire (Saturn) | Ruby (Sun), Red Coral (Mars)    |
| Vrischika  | Red Coral (Mars)     | Yellow Sapphire (Jupiter) | Diamond (Venus), Emerald (Mercury) |
| Dhanu      | Yellow Sapphire (Jupiter) | Red Coral (Mars)  | Diamond (Venus), Blue Sapphire (Saturn) |
| Makara     | Blue Sapphire (Saturn) | Diamond (Venus)     | Red Coral (Mars), Pearl (Moon)  |
| Kumbha     | Blue Sapphire (Saturn) | Diamond (Venus)     | Yellow Sapphire (Jupiter), Red Coral (Mars) |
| Meena      | Yellow Sapphire (Jupiter) | Red Coral (Mars)  | Diamond (Venus), Blue Sapphire (Saturn) |

**Source:** `jyotish/knowledge/lordship_rules.yaml` — the authoritative reference.

## Safety Implementation

### Layer 1: Prompt Injection
Every LLM call includes the `MANDATORY RULES` section in the system prompt
with lagna-specific benefic/malefic/maraka classification and prohibited stones.

### Layer 2: Post-Generation Validation
`validate_interpretation()` in `interpreter.py` scans LLM output for:
- Prohibited stone names in recommendation context
- Maraka planets called "benefic" or "auspicious"
- Worship/strengthening of maraka planets

### Layer 3: Gemstone Advisor Logic
`domain/rules/gemstone_advisor.py` implements programmatic recommendation
logic based on functional role, not natural beneficence.

## Maraka Dual-Nature Rule

Maraka planets often own both a maraka house AND a positive house. The
interpretation must acknowledge **both**:

> "Jupiter owns the 10th house (career — positive) BUT ALSO the 7th house
> (maraka sthana — death-inflicting). Career growth and health/financial
> risks happen SIMULTANEOUSLY, not separately."

Never describe a maraka planet as purely benefic or purely malefic.

## Contraindications (Never Wear Together)

- Ruby + Blue Sapphire (Sun-Saturn enmity)
- Pearl + Hessonite (Moon-Rahu enmity)
- Red Coral + Emerald (Mars-Mercury enmity, debatable)
- Yellow Sapphire + Diamond (Jupiter-Venus enmity)
- Yellow Sapphire + Emerald (Jupiter-Mercury enmity)

**Source:** `jyotish/knowledge/gemstone_logic.yaml`
