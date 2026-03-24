# Engine Research Priorities

Research topics for deep-dive, ordered by priority. Each needs classical text verification before implementation.

## HIGH Priority

### ~~1. Shadbala Kala Bala~~ — RESOLVED
All 8 components implemented (Masa, Abda, Tribhaga present in kala_bala.py lines 329-339).

### ~~2. Vimshopaka Bala~~ — RESOLVED
4 schemes complete (Shadvarga/Saptvarga/Dashavarga/Shodashavarga). 16 vargas available.

### 1. Provenance (11 unverified citations)
- **Gap:** 11 of 47 computation citations unverified against real BPHS verses
- **Source:** scriptures/bphs/*.yaml (552 verses)
- **Research:** Cross-check each citation against Santhanam translation
- **Collect:** Corrected verse numbers, flag any wrong references

### 4. Yoga YAML → Code Gap (~40 definitions)
- **Gap:** ~40 yoga definitions in YAML not programmatically checked
- **Research:** Internal audit — which YAML yogas have no code check?
- **Collect:** List with importance rating per uncoded yoga

## MEDIUM Priority

### 5. Aspect Strength (Purna/Adhika/Sama/Alpa)
- **Source:** BPHS chapter on aspects
- **Research:** Does BPHS define partial aspect strength or only full?
- **Impact:** Low — most schools treat all aspects as full

### 6. Ashtakavarga Kaksha (8 sub-divisions)
- **Source:** BPHS Ch.48-52
- **Research:** 8 x 3.75 degree segments per sign, planet ruler per segment

### 7. KP Sub-lord Table (249 entries)
- **Source:** Krishnamurthy Paddhati
- **Research:** Complete 249-entry table, KP-specific ayanamsha

### 8. Jaimini 7 vs 8 Karakas
- **Source:** Jaimini Sutras, BPHS
- **Research:** Does BPHS use 7 or 8? Exact verse. Sanjay Rath vs PVR positions.

### 9. Sahams (expand from 6 to ~20)
- **Source:** Tajaka Neelakanthi
- **Research:** Major life-event sahams with day/night formulas

### 10. Event-specific Muhurta Rules
- **Source:** Muhurta Chintamani
- **Research:** Per-event criteria (wedding, business, gemstone wearing)

## LOW Priority

### 11-30. Feature-specific research topics
See docs/engine/feature-map.md for per-feature research topics. Most are verification tasks (cross-checking existing values against classical texts) rather than new implementations.

## Research Workflow

1. **Search** using provided terms
2. **Verify** against DrikPanchang, Jagannatha Hora, BPHS translations
3. **Collect** exact data (tables, formulas, verse numbers)
4. **Share** findings in Claude Project for verification
5. **Claude Code** updates engine YAML + computation + tests
6. **make all** to verify nothing broke

## Beyond Phase 1 (Future Suggestions)

| # | Feature | Difficulty | Phase |
|---|---------|-----------|-------|
| 1 | Sarvatobhadra Chakra (28x28 grid) | Hard | 1+ |
| 2 | Tajaka Yogas (16 types) for Varshphal | Medium | 1+ |
| 3 | Festival Date Engine | Hard | 2 |
| 4 | Dasha Pravesh Charts | Medium | 2 |
| 5 | Eclipse Analysis (already done!) | Hard | ✓ Done |
| 6 | Ashtamangala Prashna | Hard | 3 |
