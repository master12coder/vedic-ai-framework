# DaivAI Data Flow — 16-Step Pipeline

## Input → FullChartAnalysis

```
INPUT: Name, DOB, TOB, Place, Lat, Lon, Timezone, Gender

STEP 1:  AYANAMSHA        Lahiri offset applied to all tropical positions
STEP 2:  CORE CHART       Swiss Ephemeris positions, signs, nakshatras, houses, dignity
STEP 3:  STRENGTH         Shadbala (6-fold), Bhava Bala, Vimshopaka, Ishta-Kashta
STEP 4:  DASHAS           Vimshottari (5-level) + 5 alternative + 7 conditional systems
STEP 5:  YOGAS + DOSHAS   320+ yoga checks, 10 dosha checks with cancellation rules
STEP 6:  AVASTHAS         Deeptadi (9 states), Lajjitadi (6 states)
STEP 7:  SPECIAL CHECKS   Gandanta, Gand Mool, Graha Yuddha, Mrityu Bhaga
STEP 8:  DIVISIONALS      16 vargas (D1-D60), Navamsha, Vargottam, deep D9/D10/D7/D12
STEP 9:  TRANSITS         Double transit, Sadesati, Gochara, Jupiter, Rahu-Ketu, SAV
STEP 10: JAIMINI          Chara Karakas, Arudha Padas, Karakamsha, Argala
STEP 11: KP SYSTEM        249 sub-lord divisions, Cuspal sub-lords
STEP 12: ADDITIONAL       Upagrahas, Panchang, Sudarshan, Sahams, Longevity
STEP 13: PHASE 1 ADV      Dispositor, Badhaka, Bhavat Bhavam, Dasha-Transit, Yoga Timing
STEP 14: PHASE 2 ADV      Avakhada, Gochara, Medical, Hora, Bhrigu Bindu, D60, Transits
STEP 15: STANDALONE       Muhurta, Varshphal, Prashna, Calendar, Matching (separate inputs)
STEP 16: VERIFICATION     Mathematical + Astronomical + Jyotish triple-layer checks

OUTPUT: FullChartAnalysis v5.1 — 67 typed fields, ~50ms, deterministic
```

## Key Numbers

- **100 modules** orchestrated by compute_full_analysis()
- **67 fields** in FullChartAnalysis Pydantic model
- **3643 tests** verifying computation accuracy
- **20+ YAML** knowledge files with provenance
- **552 BPHS verses** in scripture database

## Standalone Modules (Not in FullChartAnalysis)

These need different inputs — not part of birth chart analysis:

| Module | Why Standalone |
|--------|---------------|
| Matching (Kootas/Porutham) | Needs two charts |
| Muhurta | Needs date range, not birth chart |
| Prashna | Needs query time |
| Varshphal/Tithi Pravesh | Needs target year |
| Mundane | Event/country charts |
| Rectification | Birth time correction tool |
| Transit Finder | On-demand query (planet, event type, date range) |
| Numerology | Separate system |
| Pancha Pakshi (runtime) | Birth bird stored; yama state needs current time |
