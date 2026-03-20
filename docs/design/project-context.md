# DaivAI — Complete Project Context for UI Development

> Paste this entire file into Claude.ai, v0.dev, or any AI tool before asking
> it to build UI. It gives full context: what the project is, how data flows,
> what each screen displays, and the design system to follow.

---

## What This Project Is

**DaivAI** is a Vedic astrology framework that computes birth charts using
NASA-grade Swiss Ephemeris and interprets them using AI (LLM) + classical rules.

**Users:** Indian families, astrology enthusiasts, professional Pandit Ji (astrologers)
**Platforms:** Mobile web (primary), WhatsApp image cards, PDF reports, Telegram bot, CLI
**Language:** Hindi-English bilingual. Headers in Devanagari, data in English, explanations in Hindi.
**Feel:** Sacred document, not corporate software. Like a Pandit Ji's notebook meets modern mobile app.

---

## Architecture (3 Layers — Read-Only for UI)

```
┌──────────────────────────────────────────────┐
│  UI LAYER (what you are building)            │
│  Mobile Web / WhatsApp Cards / PDF / Telegram│
│  Receives JSON data → Renders beautiful UI   │
└──────────────┬───────────────────────────────┘
               │ consumes JSON / API
┌──────────────▼───────────────────────────────┐
│  APPS LAYER (API + delivery)                 │
│  FastAPI web server, CLI, Telegram bot       │
│  Routes: /api/chart, /api/daily, etc.        │
└──────────────┬───────────────────────────────┘
               │ calls
┌──────────────▼───────────────────────────────┐
│  PRODUCTS LAYER (AI + business logic)        │
│  7 plugins: kundali, daily, remedies,        │
│  matching, muhurta, predictions, pandit      │
│  LLM interpretation + safety validation      │
└──────────────┬───────────────────────────────┘
               │ calls
┌──────────────▼───────────────────────────────┐
│  ENGINE LAYER (pure math, zero AI)           │
│  Swiss Ephemeris, YAML rules, Pydantic models│
│  Computes: charts, dashas, yogas, strengths  │
└──────────────────────────────────────────────┘
```

**Key rule:** UI layer receives pre-computed data as JSON. It never computes anything.
The UI is purely a rendering layer — it takes data and makes it beautiful.

---

## Data Models (What the UI Receives)

### Birth Chart (ChartData)
```json
{
  "name": "Manish Chaurasia",
  "dob": "13/03/1989",
  "tob": "12:17",
  "place": "Varanasi",
  "gender": "Male",
  "lagna_sign": "Mithuna",
  "lagna_sign_en": "Gemini",
  "lagna_sign_hi": "मिथुन",
  "lagna_degree": 15.3,
  "planets": {
    "Sun": {
      "name": "Sun", "sign": "Meena", "sign_en": "Pisces",
      "house": 10, "degree_in_sign": 28.1, "nakshatra": "Revati",
      "pada": 3, "dignity": "neutral", "avastha": "Mruta",
      "is_retrograde": false, "is_combust": false
    },
    "Moon": {
      "name": "Moon", "sign": "Vrishabha", "sign_en": "Taurus",
      "house": 12, "degree_in_sign": 17.5, "nakshatra": "Rohini",
      "pada": 2, "dignity": "exalted", "avastha": "Yuva",
      "is_retrograde": false, "is_combust": false
    }
    // ... 9 planets total: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu
  }
}
```

### Lordship Context (per lagna — determines planet colors)
```json
{
  "sign_lord": "Mercury",
  "yogakaraka": { "planet": "Venus" },
  "functional_benefics": [
    { "planet": "Mercury", "houses_owned": [1, 4] },
    { "planet": "Venus", "houses_owned": [5, 12] },
    { "planet": "Saturn", "houses_owned": [8, 9] }
  ],
  "functional_malefics": [
    { "planet": "Mars", "houses_owned": [6, 11] },
    { "planet": "Jupiter", "houses_owned": [7, 10] },
    { "planet": "Sun", "houses_owned": [3] }
  ],
  "maraka": [
    { "planet": "Moon", "houses": [2], "house_str": "2nd (maraka sthana)" },
    { "planet": "Jupiter", "houses": [7], "house_str": "7th (maraka sthana)" }
  ],
  "recommended_stones": [
    { "planet": "Mercury", "stone": "Emerald (Panna)", "reasoning": "Lagnesh..." }
  ],
  "prohibited_stones": [
    { "planet": "Jupiter", "stone": "Yellow Sapphire (Pukhraj)", "reasoning": "7th lord maraka..." },
    { "planet": "Mars", "stone": "Red Coral (Moonga)", "reasoning": "6th lord..." },
    { "planet": "Moon", "stone": "Pearl (Moti)", "reasoning": "2nd lord maraka..." }
  ]
}
```

### Dasha Periods
```json
{
  "mahadashas": [
    { "lord": "Moon", "start": "1989-03-13", "end": "1999-03-13" },
    { "lord": "Mars", "start": "1999-03-13", "end": "2006-03-14" },
    { "lord": "Rahu", "start": "2006-03-14", "end": "2024-03-13" },
    { "lord": "Jupiter", "start": "2024-03-13", "end": "2040-03-13" },
    { "lord": "Saturn", "start": "2040-03-13", "end": "2059-03-14" },
    { "lord": "Mercury", "start": "2059-03-14", "end": "2076-03-13" },
    { "lord": "Ketu", "start": "2076-03-13", "end": "2083-03-14" },
    { "lord": "Venus", "start": "2083-03-14", "end": "2103-03-13" },
    { "lord": "Sun", "start": "2103-03-13", "end": "2109-03-14" }
  ],
  "current_md": { "lord": "Jupiter", "start": "2024-03-13", "end": "2040-03-13" },
  "current_ad": { "lord": "Saturn", "start": "2026-05-01", "end": "2028-11-15" }
}
```

### Yoga Results
```json
[
  {
    "name": "Gajakesari", "name_hindi": "गजकेसरी योग",
    "is_present": true, "effect": "benefic",
    "planets_involved": ["Jupiter", "Moon"],
    "houses_involved": [7, 12],
    "description": "Jupiter in kendra from Moon — bestows wisdom and wealth"
  }
]
```

### Shadbala (Planet Strength)
```json
[
  { "planet": "Sun", "ratio": 1.2, "is_strong": true, "rank": 3 },
  { "planet": "Moon", "ratio": 1.8, "is_strong": true, "rank": 1 },
  { "planet": "Mars", "ratio": 0.7, "is_strong": false, "rank": 7 }
  // ... 7 planets (Sun through Saturn, no Rahu/Ketu)
]
```

### Ashtakavarga
```json
{
  "bhinna": {
    "Sun": [4, 3, 5, 2, 6, 4, 3, 5, 4, 3, 5, 4],
    "Moon": [5, 4, 3, 6, 4, 5, 3, 4, 5, 3, 4, 5]
  },
  "sarva": [28, 25, 30, 24, 32, 29, 27, 31, 26, 28, 30, 27],
  "total": 337
}
```

### Gemstone Weight Results
```json
[
  {
    "planet": "Mercury", "stone_name": "Emerald", "stone_name_hi": "पन्ना",
    "status": "recommended", "base_ratti": 6.5, "recommended_ratti": 3.08,
    "factors": [
      { "name": "Body Weight", "raw_value": "78 kg", "multiplier": 1.0 },
      { "name": "Avastha", "raw_value": "Kumara (10°)", "multiplier": 0.90 },
      { "name": "Dignity", "raw_value": "debilitated", "multiplier": 0.90 }
    ],
    "website_comparisons": {
      "GemPundit": 6.5, "BrahmaGems": 5.9, "ShubhGems": 7.8
    },
    "free_alternatives": {
      "mantra": "ओम् बुधाय नमः (9000x)",
      "daan": "Green moong on Wednesday",
      "color": "Green"
    }
  },
  {
    "planet": "Jupiter", "stone_name": "Yellow Sapphire", "stone_name_hi": "पुखराज",
    "status": "prohibited", "recommended_ratti": 0,
    "prohibition_reason": "Jupiter is 7th lord MARAKA for Mithuna lagna"
  }
]
```

### Daily Guidance
```json
{
  "date": "2026-03-18", "vara": "Wednesday", "vara_hi": "बुधवार",
  "tithi": "Shukla Panchami", "nakshatra": "Rohini",
  "day_rating": 7, "recommended_color": "Green",
  "recommended_mantra": "ओम् बुधाय नमः",
  "rahu_kaal": "12:00-1:30 PM",
  "health_focus": "Digestion",
  "good_for": ["New beginnings", "Education", "Communication"],
  "avoid": ["Large investments", "Surgery"]
}
```

### Matching / Compatibility
```json
{
  "person1_name": "Manish", "person2_name": "Priya",
  "total_points": 28, "max_points": 36,
  "percentage": 77.8,
  "kootas": [
    { "name": "Varna", "name_hi": "वर्ण", "obtained": 1, "max": 1 },
    { "name": "Vashya", "name_hi": "वश्य", "obtained": 2, "max": 2 },
    { "name": "Tara", "name_hi": "तारा", "obtained": 3, "max": 3 },
    { "name": "Yoni", "name_hi": "योनि", "obtained": 3, "max": 4 },
    { "name": "Graha Maitri", "name_hi": "ग्रह मैत्री", "obtained": 5, "max": 5 },
    { "name": "Gana", "name_hi": "गण", "obtained": 5, "max": 6 },
    { "name": "Bhakoot", "name_hi": "भकूट", "obtained": 5, "max": 7 },
    { "name": "Nadi", "name_hi": "नाडी", "obtained": 4, "max": 8 }
  ]
}
```

### Muhurta Results
```json
[
  {
    "date": "2026-03-25", "day": "Wednesday",
    "nakshatra": "Rohini", "tithi": "Shukla Dashami",
    "score": 8.5,
    "reasons": ["Favorable nakshatra for marriage", "No Rahu Kaal conflict"]
  }
]
```

---

## Planet Color Rule (CRITICAL for UI)

Every planet's color depends on the LAGNA (ascendant sign). This is NOT fixed.
The same Jupiter is beneficial for one person and dangerous for another.

**UI must color planets based on lordship context, not generic colors.**

| Role | Color | Badge |
|------|-------|-------|
| Functional benefic | Deep Green #2E7D32 | शुभ |
| Functional malefic | Deep Red #C62828 | अशुभ |
| Yogakaraka | Gold #FF8F00 | योगकारक |
| Maraka (death-inflicting) | Dark Red #C62828 | मारक |
| Neutral | Gray #757575 | — |

For Mithuna (Gemini) lagna specifically:
- Mercury = GREEN (lagnesh, always beneficial)
- Venus = GOLD (yogakaraka, 5th lord)
- Saturn = GREEN with caution (9th lord but also 8th)
- Jupiter = RED (7th+10th lord, MARAKA — counterintuitive but correct)
- Mars = RED (6th+11th lord, chief malefic)
- Moon = RED (2nd lord, maraka)
- Sun = GRAY (3rd lord, mild malefic)

---

## Safety Rules (NON-NEGOTIABLE for Gemstone UI)

1. **NEVER show Pukhraj (Yellow Sapphire), Moonga (Red Coral), or Moti (Pearl) as
   recommended for Mithuna lagna.** These stones strengthen MARAKA/MALEFIC planets.
2. Prohibited stones must always show with RED warning and clear reason.
3. Gemstone weight comes from the 10-factor engine, not from body weight alone.
4. Always show: "No shastra prescribes exact weight" disclaimer.
5. Always show free alternatives (mantra, daan, color) — not everyone can buy gemstones.

---

## Hindi Abbreviations Used Throughout

| English | Hindi | Abbreviation |
|---------|-------|--------------|
| Sun | सूर्य | सू |
| Moon | चन्द्र | चं |
| Mars | मंगल | मं |
| Mercury | बुध | बु |
| Jupiter | गुरु | गु |
| Venus | शुक्र | शु |
| Saturn | शनि | श |
| Rahu | राहु | रा |
| Ketu | केतु | के |
| Lagna | लग्न | — |
| Retrograde | वक्री | — |
| Combust | अस्त | — |
| Exalted | उच्च | — |
| Debilitated | नीच | — |
| Benefic | शुभ | — |
| Malefic | अशुभ | — |
| Maraka | मारक | — |
| Yogakaraka | योगकारक | — |

---

## 12 Signs in Hindi

| # | Sanskrit | Hindi | English |
|---|----------|-------|---------|
| 1 | Mesha | मेष | Aries |
| 2 | Vrishabha | वृषभ | Taurus |
| 3 | Mithuna | मिथुन | Gemini |
| 4 | Karka | कर्क | Cancer |
| 5 | Simha | सिंह | Leo |
| 6 | Kanya | कन्या | Virgo |
| 7 | Tula | तुला | Libra |
| 8 | Vrischika | वृश्चिक | Scorpio |
| 9 | Dhanu | धनु | Sagittarius |
| 10 | Makara | मकर | Capricorn |
| 11 | Kumbha | कुम्भ | Aquarius |
| 12 | Meena | मीन | Pisces |

---

## Design System (Summary)

| Token | Hex | Usage |
|-------|-----|-------|
| saffron | #FF6F00 | Primary accent, headers, sacred elements |
| cream | #FFFDE7 | Page/card backgrounds |
| deep-green | #2E7D32 | Benefic, recommended, positive |
| deep-red | #C62828 | Malefic, prohibited, danger |
| gold | #FF8F00 | Yogakaraka, golden period, ratings |
| indigo | #1A237E | Section headers, chart borders |
| text-primary | #212121 | Body text |
| text-secondary | #757575 | Captions |

**Font:** Noto Sans Devanagari (Google Fonts) for ALL text.
**Invocation:** "श्री गणेशाय नमः" on every page header (NOT "ॐ")
**Closing:** "शुभम् भवतु" in every footer
**Mobile-first:** 390px width primary. Scale up for tablet/desktop.

---

## Pages to Build (9 screens + design system)

1. **Title Page** — Name, birth details, lagna/moon/dasha badges
2. **D1 Birth Chart** — North Indian diamond with colored planets
3. **Planet Table** — 9 planet cards with strength + role badges
4. **Dasha Timeline** — Vertical timeline, current expanded, color-coded
5. **Gemstone Card** — Recommended weight + prohibited list + free alternatives
6. **Daily Guidance** — Rating, color, mantra, rahu kaal, good/avoid (WhatsApp card)
7. **Compatibility** — Two names, 8 koota bars, total score circle
8. **Muhurta Dates** — Ranked date cards with score and reasons
9. **Yoga Cards** — Active yogas with effect badges

**See `docs/design/page-prompts.md` for copy-paste prompts per page.**
**See `docs/design/design-system.md` for full component library.**

---

## Tech Stack for UI Layer

The UI is SEPARATE from the backend. It consumes JSON data via API.

**Recommended stack for the UI:**
- React + Tailwind CSS + shadcn/ui (v0.dev generates this)
- OR plain HTML/CSS/JS (simpler, works everywhere)
- Noto Sans Devanagari from Google Fonts
- Mobile-first responsive design
- Export: HTML pages, PNG image cards (for WhatsApp), PDF (via print CSS)

**The backend already exists.** It exposes:
- `/api/chart` — returns ChartData JSON
- `/api/daily` — returns daily guidance JSON
- More API routes can be added as needed

**The UI developer/AI only needs to:**
1. Accept JSON data (examples above)
2. Render it beautifully using the design system
3. Follow the planet color rules (from lordship context)
4. Follow the safety rules (prohibited stones always red)
