# Jyotish Design System — Page Designs, Platform Specs & AI Prompts

> For brand, tokens, typography, components: see `design-system.md`.

---

## Pages to Design (14 total)

### PAGE 1: Title Page (श्री गणेशाय नमः)
**Used in:** PDF cover, Web landing after chart computation
**Components:** Sacred Header, Page Title Card
**Layout:**
```
+-------------------------+
|  ### SAFFRON BAR ###    |
|  श्री गणेशाय नमः         |
+-------------------------+
|                         |
|     [Name in large]     |
|  मनीष चौरसिया            |
|  Manish Chaurasia       |
|                         |
|  13/03/1989 | 12:17     |
|  वाराणसी                 |
|                         |
|  +-----+ +-----+       |
|  |मिथुन | |रोहिणी|       |
|  |लग्न  | |पाद 2|       |
|  +-----+ +-----+       |
|                         |
|  वर्तमान दशा: गुरु > बुध |
|                         |
|     शुभम् भवतु           |
+-------------------------+
```

---

### PAGE 2: D1 Birth Chart (राशि चक्र)
**Used in:** PDF page 2, Web chart result, Telegram image
**Components:** Sacred Header, Diamond Chart, Legend
**Data:**
- 9 planets placed in 12 houses
- Each planet: Hindi abbreviation + degree + functional role badge
- House numbers with sign names
- Legend at bottom: green = शुभ, red = अशुभ, gold = योगकारक

---

### PAGE 3: D9 Navamsha Chart (नवमांश)
**Used in:** PDF page 3 (detailed/pandit)
**Components:** Same Diamond Chart component, different data
**Extra:** Vargottam planets marked with star

---

### PAGE 4: Planet Positions Table (ग्रह स्थिति)
**Used in:** PDF, Web chart result
**Components:** Planet Row (x9), Status Badges
**Columns:**
| ग्रह | राशि | भाव | अंश | नक्षत्र | पाद | गति | अवस्था | बल | लग्न-फल |
**Mobile:** Horizontal scroll or stacked card view (one card per planet)

---

### PAGE 5: Dasha Timeline (दशा चक्र)
**Used in:** PDF, Web, Telegram
**Layout:** Vertical timeline (mobile-friendly, not horizontal Gantt)
```
  * चन्द्र MD (1989-1999) --- gray
  * मंगल MD (1999-2006) ---- red (malefic)
  * राहु MD (2006-2024) ---- gray
  o गुरु MD (2024-2040) ---- red (CURRENT, expanded)
    +- गुरु AD (2024-2026)
    +- शनि AD (2026-2029) <- अभी
    +- बुध AD (2029-2031) <- green (benefic)
    +- ...
  * शनि MD (2040-2059) ---- green (benefic)
  * बुध MD (2059-2076) ---- green (lagnesh!)
```
**Mobile:** Vertical is better than horizontal. Each MD is a row. Current expanded.

---

### PAGE 6: Ashtakavarga Grid (अष्टकवर्ग)
**Used in:** PDF, Web (pandit view)
**Layout:** 7 rows x 12 columns heatmap
- Green cells (5-8 bindus), Gold (3-4), Red (0-2)
- SAV total row at bottom
- Sign names in Hindi as column headers
- Planet names in Hindi as row headers
- Total: 337 shown prominently

---

### PAGE 7: Active Yogas (सक्रिय योग)
**Used in:** PDF, Web
**Layout:** Card stack (max 5-7 cards)
Each card:
```
+--------------------------+
| [green] हंस योग (Hamsa)  |
| शुभ — गुरु in कर्म भाव    |
| Forming: Jupiter in 10th  |
| "Bestows wisdom..."       |
+--------------------------+
```

---

### PAGE 8: Shadbala Strength (षड्बल)
**Used in:** PDF, Web (pandit view)
**Layout:** Horizontal bars or radial chart
- 7 planets, each with strength bar
- Green if ratio > 1.0, Red if < 1.0
- Strongest/Weakest highlighted
- "सबसे बलवान: शुक्र (1.8)" at top

---

### PAGE 9: Golden Period (स्वर्ण काल)
**Used in:** PDF, Web
**Layout:** Single highlight card with gold border
```
+---- GOLD BORDER ----------+
|  आपका स्वर्ण काल:          |
|  बुध महादशा               |
|  2059 — 2076              |
|                           |
|  लग्नेश की दशा — career,  |
|  intellect, communication |
|  at peak                  |
+---------------------------+
```

---

### PAGE 10: Gemstone Recommendation (रत्न सुझाव)
**Used in:** PDF, Web, Telegram
**Layout:** 3 sections — Recommended / Test / Prohibited
```
RECOMMENDED [check]
+--------------------------+
| [green] पन्ना (Emerald)  |
| Planet: बुध (Mercury)     |
| Weight: 3.08 रत्ती        |
| Factors: अवस्था कुमार,    |
|   नीच राशि, शुभ भाव      |
| vs GemPundit: 6.5 रत्ती   |
| Free alt: ओम् बुधाय नमः   |
+--------------------------+

PROHIBITED [x]
+--------------------------+
| [red] पुखराज (Y. Sapphire)|
| गुरु = 7th मारक lord     |
| Free: ओम् गुरुवे नमः      |
+--------------------------+
```

---

### PAGE 11: Daily Guidance (दैनिक मार्गदर्शन)
**Used in:** Web, Telegram, WhatsApp image
**Layout:** Single card, 3 levels
**Simple (1 card for WhatsApp):**
```
+--------------------------+
| 18 मार्च 2026 | मंगलवार   |
| ******* 7/10             |
| Color: Red               |
| Mantra: हनुमान चालीसा      |
| Rahu Kaal: 3:00-4:30 PM  |
| Good: नई शुरुआत, व्यायाम   |
| Avoid: बड़ा निवेश           |
+--------------------------+
```

---

### PAGE 12: Compatibility Report (गुण मिलान)
**Used in:** Web, PDF
**Layout:**
- Two name badges side by side
- 8 koota scores as progress bars
- Total score as large number with color indicator
- "36 में से 28 गुण = अति उत्तम"

---

### PAGE 13: Muhurta Results (शुभ मुहूर्त)
**Used in:** Web, PDF
**Layout:** Card list (top 5 dates)
Each card:
```
+--------------------------+
| #1 — 25 मार्च 2026       |
| बुधवार | रोहिणी नक्षत्र    |
| Score: 8.5/10            |
| [check] Favorable tithi  |
| [check] No Rahu Kaal     |
| [warn] Moon in 8th       |
+--------------------------+
```

---

### PAGE 14: Accuracy Certificate (प्रमाणपत्र)
**Used in:** PDF last page
**Layout:** Formal certificate card
- Computation metadata table
- Cross-verification note
- Disclaimer in Hindi: "यह computational tool है, Pandit Ji का विकल्प नहीं"
- QR code placeholder for verification link

---

## Design for Each Platform

### Mobile Web (Primary)
- 390px width, full height scroll
- Bottom tab bar: Home | Chart | Daily | Remedies | More
- Pull-to-refresh on daily page
- Share button generates WhatsApp image

### WhatsApp Image Card
- 1080x1080 or 1080x1920 PNG
- One card = one insight (daily, gemstone, yoga)
- Large text, readable without zooming
- Brand watermark at bottom

### PDF (A4)
- Same components, laid out for print
- Saffron header band on every page
- Page numbers in footer
- "श्री गणेशाय नमः" on page 1 only

### Telegram
- Markdown formatted text
- Send chart as image attachment
- Inline keyboard buttons for navigation

---

## AI Prompt to Generate All Pages

Copy-paste this into v0.dev or Claude.ai:

```
Design a complete mobile-first Vedic astrology app called "DaivAI".

Color scheme: saffron (#FF6F00), cream (#FFFDE7), deep green (#2E7D32),
deep red (#C62828), gold (#FF8F00), indigo (#1A237E).

Font: Noto Sans Devanagari for all text. Hindi-English bilingual.

Header: Every page starts with a saffron bar containing "श्री गणेशाय नमः" in white.
Footer: "शुभम् भवतु | daivai"

Design these pages (390px mobile width):

1. TITLE PAGE: Person's name large in Devanagari, birth details, lagna badge
   (saffron pill), moon nakshatra badge, current dasha display.

2. BIRTH CHART: North Indian diamond layout inside a card. 12 houses with
   Hindi sign names. Planets colored: green=benefic, red=malefic, gold=yogakaraka.
   Show degree next to planet name.

3. PLANET TABLE: 9 rows, one per planet. Columns: planet (Hindi+EN), sign, house,
   degree, nakshatra, motion badges (retrograde=blue pill, combust=orange pill),
   strength ratio, functional role (शुभ/अशुभ/मारक badge).

4. DASHA TIMELINE: Vertical timeline with 9 mahadasha periods. Current period
   expanded to show antardashas. Color-coded by benefic/malefic. "अभी" badge
   on current period.

5. GEMSTONE CARD: Recommended stone with green left border, weight in ratti,
   key factors as pills, website comparison line. Prohibited stone with red
   left border and warning icon. Free alternatives section.

6. DAILY GUIDANCE: Single card with day rating (stars), color recommendation,
   mantra, rahu kaal time, good/avoid lists. Optimized for WhatsApp sharing.

7. YOGA CARDS: Stack of 3-5 cards, each showing yoga name (Hindi), effect badge
   (शुभ/अशुभ), forming planets, one-line description.

8. GOLDEN PERIOD: Single highlight card with gold border showing best upcoming
   dasha period and preparation advice.

Use shadcn/ui components. Tailwind CSS. All text must be readable at mobile size.
No tiny text. Generous padding. Sacred document feel, not corporate dashboard.
```

---

## Quick Start for Each Tool
- **v0.dev:** Paste the prompt above, click generate, iterate per page
- **Claude.ai Artifacts:** "Create an interactive HTML prototype" + prompt above
- **Adobe Express:** Search "spiritual" template, apply saffron/cream palette
- **Gemini:** "Design layout mockup for Vedic astrology mobile app" + theme
