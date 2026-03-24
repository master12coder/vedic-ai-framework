# Engine Feature Map — 30 Features

## Status Key
- DONE = Complete and tested
- PARTIAL = Functional with known gaps
- GAP = Missing or incomplete

## Master Table

| # | Feature | Code | YAML | Priority | Key Gap |
|---|---------|------|------|----------|---------|
| 1 | Ayanamsha | DONE | DONE | LOW | None |
| 2 | Sign & House Determination | DONE | DONE | LOW | None |
| 3 | Planetary Dignity & States | DONE | DONE | LOW | None |
| 4 | Nakshatra & Pada System | DONE | DONE | LOW | None |
| 5 | Lordship Rules (Bhavesh) | DONE | DONE | LOW | None |
| 6 | Planetary Aspects (Drishti) | DONE | PARTIAL | LOW | Aspect strength not implemented |
| 7 | Vimshottari Dasha | DONE | DONE | LOW | None |
| 8 | Kalachakra Dasha | DONE | DONE | LOW | None |
| 9 | Other Dasha Systems | DONE | PARTIAL | LOW | No YAML provenance |
| 10 | Shadbala (6-fold) | DONE | DONE | - | All 8 Kala Bala components implemented |
| 11 | Ashtakavarga | DONE | DONE | LOW | Kaksha not implemented |
| 12 | Yoga Detection | DONE | DONE | HIGH | ~40 YAML defs not coded |
| 13 | Dosha Detection | DONE | DONE | LOW | None |
| 14 | Divisional Charts | DONE | PARTIAL | LOW | No signification YAML |
| 15 | Vimshopaka Bala | DONE | MISSING | MEDIUM | 4 schemes complete, needs weight YAML |
| 16 | Jaimini System | DONE | PARTIAL | LOW | 7vs8 karaka not documented |
| 17 | Bhava Bala | DONE | MISSING | MEDIUM | No YAML formulas |
| 18 | Special Lagnas | DONE | MISSING | MEDIUM | No YAML significations |
| 19 | Panchang Elements | DONE | PARTIAL | LOW | None |
| 20 | Upagrahas | DONE | MISSING | MEDIUM | No YAML formulas |
| 21 | Transit Analysis | DONE | PARTIAL | LOW | None |
| 22 | KP Sub-lords | DONE | MISSING | MEDIUM | No YAML 249-entry table |
| 23 | Sahams | DONE | MISSING | MEDIUM | Only 6 of ~50 sahams |
| 24 | Sudarshan Chakra | DONE | MISSING | MEDIUM | No YAML methodology |
| 25 | Longevity Analysis | DONE | MISSING | MEDIUM | Only Pindayu method |
| 26 | Muhurta | DONE | PARTIAL | LOW | No event-specific YAML |
| 27 | Gemstone & Remedy | DONE | DONE | LOW | None |
| 28 | Ashtakoot Matching | DONE | PARTIAL | LOW | No scoring table YAML |
| 29 | Provenance System | PARTIAL | PARTIAL | HIGH | 11 unverified citations |
| 30 | Verification System | DONE | PARTIAL | LOW | None |

## Summary

| Category | Count |
|----------|-------|
| Total features | 30 |
| Code DONE | 30 |
| Code PARTIAL | 0 |
| YAML DONE | 12 |
| YAML PARTIAL | 10 |
| YAML MISSING | 8 |

## Phase 1 Additions (March 2026 Sessions)

Beyond the original 30, these were added during Phase 1 implementation:
- Dispositor tree (BPHS Ch.13)
- Badhaka analysis (BPHS Ch.44-45)
- Bhavat Bhavam (BPHS Ch.5)
- Dasha-Transit integration (BPHS Ch.25)
- Yoga activation timing
- Lal Kitab (1939-1952)
- Kota Chakra (Tajaka Neelakanthi)
- Nisheka conception chart (BPHS Ch.4)
- Eclipse natal impact (Surya Siddhanta)
- Chandra/Surya Kundali (Uttarakalamrita)
- Medical astrology (body mapping, tridosha)
- Bhrigu Bindu (destiny point)
- Avakhada Chakra (birth classification)
- Pushkara Navamsha/Bhaga
- Mrityu Bhaga (critical degrees)
- Hora chart analysis
- Drekkana D3 analysis
- Deep varga analysis (D9/D10/D7/D12)
- D60 Shastyamsha analysis
- SAV transit scoring
- 7 conditional dasha systems
- Pancha Pakshi birth bird
- lagna_lord explicit field
