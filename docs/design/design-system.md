# Jyotish Design System — Brand, Components & Tokens

> Paste this into v0.dev, Claude.ai Artifacts, or any AI design tool.
> For page designs and platform specs, see `design-pages.md`.

---

## Brand Identity

**Name:** DaivAI — Vedic Astrology Intelligence
**Feel:** Sacred document meets modern mobile app. Like a Pandit Ji's notebook, not a software dashboard.
**Invocation:** "श्री गणेशाय नमः" (not "ॐ" — use the proper invocation before any kundali)
**Closing:** "शुभम् भवतु" (May auspiciousness prevail)
**Language:** Hindi-English mix. Headers in Devanagari, data in English, explanations in Hindi. Like how a modern Pandit speaks.

---

## Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `saffron` | `#FF6F00` | Primary brand, headers, top bars, sacred accent |
| `saffron-light` | `#FFF3E0` | Hover states, card highlights |
| `cream` | `#FFFDE7` | Page background, body fill |
| `deep-green` | `#2E7D32` | Benefic planets, positive indicators, recommended |
| `deep-red` | `#C62828` | Malefic planets, prohibited, danger warnings |
| `gold` | `#FF8F00` | Yogakaraka planet, golden period, star ratings |
| `indigo` | `#1A237E` | Section headers, chart borders, text headings |
| `text-primary` | `#212121` | Body text |
| `text-secondary` | `#757575` | Captions, footnotes, metadata |
| `bg-card` | `#FFFFFF` | Card background |
| `border` | `#E0E0E0` | Card borders, dividers |

**Rule:** Never use pure black (#000). Never use blue links. Saffron is the only accent color for interactive elements.

---

## Typography

| Style | Font | Size (mobile) | Size (desktop) | Weight | Usage |
|-------|------|---------------|----------------|--------|-------|
| `display` | Noto Sans Devanagari | 28px | 36px | 700 | Page titles (श्री गणेशाय नमः) |
| `h1` | Noto Sans Devanagari | 22px | 28px | 600 | Section headers |
| `h2` | Noto Sans Devanagari | 18px | 22px | 600 | Sub-section headers |
| `h3` | Noto Sans Devanagari | 16px | 18px | 500 | Card titles |
| `body` | Noto Sans Devanagari | 14px | 16px | 400 | Body text |
| `body-hi` | Noto Sans Devanagari | 15px | 17px | 400 | Hindi body text (slightly larger for readability) |
| `caption` | Noto Sans | 12px | 13px | 400 | Footnotes, metadata |
| `data` | JetBrains Mono / monospace | 13px | 14px | 400 | Degrees, numbers, coordinates |

---

## Spacing System

| Token | Value | Usage |
|-------|-------|-------|
| `xs` | 4px | Inside badges |
| `sm` | 8px | Between related items |
| `md` | 16px | Card padding, section gaps |
| `lg` | 24px | Between sections |
| `xl` | 32px | Page margins (mobile) |
| `2xl` | 48px | Page margins (desktop) |

**Mobile-first:** All designs start at 390px width (iPhone 14). Scale up to 768px (tablet) and 1024px (desktop).

---

## Reusable Components

### 1. Sacred Header Bar
- Full-width saffron (#FF6F00) bar, 56px height
- White text, centered: "श्री गणेशाय नमः"
- Appears on EVERY page/screen as the first element
- On PDF: saffron band across top of every page

### 2. Page Title Card
- Cream background, indigo text
- Person's name (large, Devanagari + English)
- Birth details: DOB | TOB | Place
- Lagna badge: rounded pill, saffron background, white text "मिथुन लग्न"
- Moon badge: "चन्द्र: रोहिणी पाद 2"
- Current dasha badge: "गुरु > बुध दशा"

### 3. Diamond Chart (North Indian)
- Traditional diamond shape inside a rounded card
- Thick indigo borders (3px)
- 12 triangular houses, each showing:
  - Sign name in Hindi (small, gray, top of triangle)
  - Planet abbreviations in Devanagari (large, colored by role)
  - Degree value (small, below planet name)
- Planet colors: green = benefic for THIS lagna, red = malefic, gold = yogakaraka
- "लग्न" label in the center
- Card has: title bar ("D1 राशि चक्र"), rounded corners, subtle shadow

### 4. Planet Row (reusable for tables)
- Left: Planet icon/emoji + Hindi name + English name
- Middle: Sign, House, Degree, Nakshatra
- Right: Status badges (वक्री = blue pill, अस्त = orange pill, उच्च = green pill, नीच = red pill)
- Alternating row colors: white / cream

### 5. Dasha Badge
- Pill-shaped, color based on planet's functional role
- Shows: Hindi planet name + date range
- Current dasha has pulsing border or "अभी" badge

### 6. Gemstone Card
- Card with colored left border (green = recommended, red = prohibited, gold = test)
- Stone image placeholder (circle with stone color)
- Stone name (Hindi + English)
- Weight: "3.08 रत्ती (Recommended)" in large text
- Key factors as small pills: "अवस्था: कुमार", "गरिमा: नीच"
- vs Website: "GemPundit: 6.5 | Ours: 3.08"

### 7. Status Badge
- Small rounded pill
- Green + "शुभ" for benefic
- Red + "अशुभ" for malefic
- Gold + "मिश्र" for mixed
- Red + "मारक" for maraka
- Gold + "योगकारक" for yogakaraka

### 8. Info Card
- White card with rounded corners (12px)
- Subtle border (#E0E0E0)
- Optional saffron left border (4px) for emphasis
- Title in indigo h3
- Body in text-primary
- Footer caption in text-secondary

### 9. Warning Card
- Red left border (4px)
- Red icon (shield/warning)
- Used for prohibited stones, maraka warnings

### 10. Sacred Footer
- "शुभम् भवतु" centered
- "daivai" small caption
- Page number (for PDF)
