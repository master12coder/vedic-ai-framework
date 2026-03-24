# DaivAI — Project Context: Planet Colors, Safety, References & Tech Stack

> This is the second half of the project context for UI development.
> For architecture overview and JSON data models, see `project-context.md`.

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

**See `docs/design/design-pages.md` for copy-paste prompts per page.**
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
1. Accept JSON data (examples in `project-context.md`)
2. Render it beautifully using the design system
3. Follow the planet color rules (from lordship context)
4. Follow the safety rules (prohibited stones always red)
