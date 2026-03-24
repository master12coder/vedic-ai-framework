# YAML Knowledge Layer — Coverage Matrix

Last updated: March 24, 2026

**42 YAML knowledge files exist** in `engine/src/daivai_engine/knowledge/`.

## Coverage Status

| # | Feature | YAML File(s) | Status |
|---|---------|-------------|--------|
| 1 | Ayanamsha | ayanamsha_reference.yaml (139) | DONE |
| 2 | Sign & House | nakshatra_data.yaml (1289) + house_significations.yaml (181) + sign_properties.yaml (190) | DONE |
| 3 | Dignity & States | dignity.yaml (186) + combustion.yaml (55) | DONE |
| 4 | Nakshatra & Pada | nakshatra_data.yaml (1289) + avakhada_data.yaml (256) | DONE |
| 5 | Lordship Rules | lordship_rules.yaml (1814) | DONE |
| 6 | Aspects | aspects.yaml (133) | DONE |
| 7 | Vimshottari | vimshottari_dasha.yaml (80) | DONE |
| 8 | Kalachakra | kalachakra_dasha_data.yaml (374) | DONE |
| 9 | Other Dashas | vimshottari_dasha.yaml (shared) | DONE |
| 10 | Shadbala | shadbala_reference.yaml (110) | DONE |
| 11 | Ashtakavarga | ashtakavarga_tables.yaml (109) | DONE |
| 12 | Yoga Detection | yoga_definitions.yaml (8304) | PARTIAL — ~342 defs not coded |
| 13 | Dosha Detection | dosha_definitions.yaml (124) | DONE |
| 14 | Divisional Charts | varga_significations.yaml (354) + shashtyamsha_data.yaml (385) | DONE |
| 15 | Vimshopaka | vimshopaka_weights.yaml (110) | DONE |
| 16 | Jaimini | (rules in code, no dedicated YAML) | PARTIAL — needs jaimini_rules.yaml |
| 17 | Bhava Bala | shadbala_reference.yaml (shared) | DONE |
| 18 | Special Lagnas | special_lagna_significations.yaml (158) | DONE |
| 19 | Panchang | nakshatra_data.yaml (shared) | DONE |
| 20 | Upagrahas | upagraha_significations.yaml (164) | DONE |
| 21 | Transit | transit_rules.yaml (586) + gochara_rules.yaml (268) | DONE |
| 22 | KP Sub-lords | (tables in code, kp_tables.py) | DONE |
| 23 | Sahams | saham_definitions.yaml (374) | DONE |
| 24 | Sudarshan | (rules in code) | PARTIAL — needs sudarshan_rules.yaml |
| 25 | Longevity | (rules in code) | PARTIAL — needs longevity_reference.yaml |
| 26 | Muhurta | (rules in code) | PARTIAL — needs muhurta_rules.yaml |
| 27 | Gemstone & Remedy | gemstone_logic.yaml (184) + gem_therapy_rules.yaml (628) + remedy_rules.yaml (181) | DONE |
| 28 | Matching | porutham_data.yaml (141) | DONE |
| 29 | Provenance | computation_sources.yaml (653) | DONE — 14 entries at "medium" confidence |
| 30 | Verification | (checks in code) | DONE |
| - | Medical | medical_rules.yaml (378) | DONE |
| - | Mantra/Yantra | mantra_rules.yaml (540) + mantras.yaml (81) + yantra_data.yaml (349) | DONE |
| - | Vastu | vastu_rules.yaml (442) | DONE |
| - | Numerology | numerology_rules.yaml (577) | DONE |
| - | Pancha Pakshi | pancha_pakshi_rules.yaml (149) | DONE |
| - | Namakarana | namakarana_rules.yaml (156) | DONE |
| - | Mundane | mundane_rules.yaml (417) | DONE |
| - | Prashna | ashtamangala_prashna.yaml (220) | DONE |
| - | Mrityu Bhaga | mrityu_bhaga.yaml (31) | DONE |
| - | Pushkara | pushkara_data.yaml (41) | DONE |
| - | Direction | direction_mapping.yaml (77) | DONE |
| - | Weekly Routine | weekly_routine.yaml (78) | DONE |

## Summary

- **42 YAML files** total (~19,000 lines of knowledge)
- **DONE:** 38 features fully backed by YAML
- **PARTIAL:** 4 features need YAML (Jaimini rules, Sudarshan, Longevity, Muhurta)
- **GAP:** ~342 yoga definitions in yoga_definitions.yaml not wired to code

## Remaining Work

1. Create `jaimini_rules.yaml` — 7vs8 karaka debate, rasi dasha rules
2. Create `sudarshan_rules.yaml` — triple overlay methodology
3. Create `longevity_reference.yaml` — Pindayu/Amshayu/Naisargika comparison
4. Create `muhurta_rules.yaml` — event-specific criteria
5. Wire ~342 uncoded yoga definitions to detection code
6. Verify 14 "medium" confidence provenance citations
