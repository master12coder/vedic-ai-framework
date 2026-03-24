# KALACHAKRA DASHA — Foundations, Tables & Structural Logic
## For vedic-ai-framework: BPHS Chapter 46 Deep Research

**Compiled from:** BPHS (Santhanam Translation), PVR Narasimha Rao's Tutorial & Raghavacharya Method Paper (2004), Heikki Malaska's Kalachakra Dasa System Analysis, Sanjay Prabhakaran's Jyotish Research, Eastrovedica Lesson 45, and multiple cross-referenced scholarly sources.

> For Kalachakra Navamsha, Gatis, Deha/Jeeva, computation, interpretation,
> and implementation notes, see `kalachakra-sequences.md`.

---

## 1. FOUNDATIONAL CONCEPT

Kalachakra Dasha = "Wheel of Time" Dasha. Parasara called it **"the most respectable of all dasa systems"** (BPHS 46.6-11). Before explaining it to Maitreya, Parasara prayed to the Lord — a gesture not enacted for any other dasha.

**Key distinction from Vimshottari:**
- Vimshottari = planetary dasha (based on Moon's nakshatra)
- Kalachakra = **rashi (sign) dasha** (based on Moon's nakshatra PADA / navamsha)
- Vimshottari shows the state of the native's **mind** as time progresses
- Kalachakra shows the **physical and spiritual experience** — the "how" and "where"

**Birth time sensitivity:** 1 minute error in birth time shifts all Kalachakra dasha dates by ~3 months. This makes it both extremely difficult to use with unverified times AND the premier tool for birth time rectification.

---

## 2. RASHI DASHA DURATIONS (Table 1)

Signs owned by the same planet have identical dasha years:

| Rashi | Ruler | Years |
|-------|-------|-------|
| Mesha (Aries) | Mangal (Mars) | 7 |
| Vrishabha (Taurus) | Shukra (Venus) | 16 |
| Mithuna (Gemini) | Budha (Mercury) | 9 |
| Karka (Cancer) | Chandra (Moon) | 21 |
| Simha (Leo) | Surya (Sun) | 5 |
| Kanya (Virgo) | Budha (Mercury) | 9 |
| Tula (Libra) | Shukra (Venus) | 16 |
| Vrishchika (Scorpio) | Mangal (Mars) | 7 |
| Dhanu (Sagittarius) | Guru (Jupiter) | 10 |
| Makara (Capricorn) | Shani (Saturn) | 4 |
| Kumbha (Aquarius) | Shani (Saturn) | 4 |
| Meena (Pisces) | Guru (Jupiter) | 10 |

**Planet summary:** Sun=5, Moon=21, Mars=7, Mercury=9, Jupiter=10, Venus=16, Saturn=4

---

## 3. THE TWO CHAKRAS: SAVYA AND APASAVYA

### 3.1 Savya Chakra (Direct/Zodiacal)
The 12 navamsha signs in order: **Ar, Ta, Ge, Cn, Le, Vi, Li, Sc, Sg, Cp, Aq, Pi**

Planetary lordship sequence: Mars, Venus, Mercury, Moon, Sun, Mercury, Venus, Mars, Jupiter, Saturn, Saturn, Jupiter

### 3.2 Apasavya Chakra (Irregular/Anti-zodiacal — "Mirror Image")
The 12 navamsha signs: **Sc, Li, Vi, Cn, Le, Ge, Ta, Ar, Pi, Aq, Cp, Sg**

The Apasavya Chakra is formed by the **mirror images** of zodiacal signs:
- Ar <-> Sc (both Mars)
- Ta <-> Li (both Venus)
- Ge <-> Vi (both Mercury)
- Cn <-> Cn (Moon owns only Cancer — mirrors itself)
- Le <-> Le (Sun owns only Leo — mirrors itself)
- Sg <-> Pi (both Jupiter)
- Cp <-> Aq (both Saturn)

**Why the jumps?** The lordship constraint forces irregular progression. Starting from Scorpio going anti-zodiacally: Sc(Mars), Li(Venus), Vi(Mercury), then Moon and Sun must come — but they own only Cn and Le — so it jumps to Cn, Le, then back to Ge(Mercury), Ta(Venus), Ar(Mars), Pi(Jupiter), Aq(Saturn), Cp(Saturn), Sg(Jupiter).

---

## 4. NAKSHATRA GROUPINGS (Table 3)

27 nakshatras alternate in groups of 3 between Savya and Apasavya. Within each cycle, there are 2 sub-groups:

### 4.1 Savya Cycle (15 nakshatras)

**Savya-I (Ashwini Group — 10 nakshatras):**
Ashwini, Krittika, Punarvasu, Ashlesha, Hasta, Swati, Moola, Uttarashadha, Poorvabhadrapada, Revati

**Savya-II (Bharani Group — 5 nakshatras):**
Bharani, Pushyami, Chitra, Poorvashadha, Uttarabhadrapada

### 4.2 Apasavya Cycle (12 nakshatras)

**Apasavya-I (Rohini Group — 4 nakshatras):**
Rohini, Magha, Vishakha, Shravana

**Apasavya-II (Mrigashira Group — 8 nakshatras):**
Mrigashira, Ardra, Poorvaphalguni, Uttaraphalguni, Anuradha, Jyeshtha, Dhanishtha, Shatabhisha

### 4.3 Full Nakshatra Classification (for quick lookup)

| Nak# | Nakshatra | Cycle | Group |
|------|-----------|-------|-------|
| 1 | Ashwini | Savya | I |
| 2 | Bharani | Savya | II |
| 3 | Krittika | Savya | I |
| 4 | Rohini | Apasavya | I |
| 5 | Mrigashira | Apasavya | II |
| 6 | Ardra | Apasavya | II |
| 7 | Punarvasu | Savya | I |
| 8 | Pushyami | Savya | II |
| 9 | Ashlesha | Savya | I |
| 10 | Magha | Apasavya | I |
| 11 | Poorvaphalguni | Apasavya | II |
| 12 | Uttaraphalguni | Apasavya | II |
| 13 | Hasta | Savya | I |
| 14 | Chitra | Savya | II |
| 15 | Swati | Savya | I |
| 16 | Vishakha | Apasavya | I |
| 17 | Anuradha | Apasavya | II |
| 18 | Jyeshtha | Apasavya | II |
| 19 | Moola | Savya | I |
| 20 | Poorvashadha | Savya | II |
| 21 | Uttarashadha | Savya | I |
| 22 | Shravana | Apasavya | I |
| 23 | Dhanishtha | Apasavya | II |
| 24 | Shatabhisha | Apasavya | II |
| 25 | Poorvabhadrapada | Savya | I |
| 26 | Uttarabhadrapada | Savya | II |
| 27 | Revati | Savya | I |

---

## 5. THE 108-PADA-TO-SIGN MAPPING (Master Dasha Sequences)

### 5.1 Savya-I Group (Ashwini-type nakshatras)
**Applies to:** Ashwini, Krittika, Punarvasu, Ashlesha, Hasta, Swati, Moola, Uttarashadha, Poorvabhadrapada, Revati

| Pada | Dasha Sequence (9 signs) | Paramayus | Deha | Jeeva |
|------|--------------------------|-----------|------|-------|
| 1 | Ar, Ta, Ge, Cn, Le, Vi, Li, Sc, Sg | 100 | Ar | Sg |
| 2 | Cp, Aq, Pi, Sc, Li, Vi, Cn, Le, Ge | 85 | Cp | Ge |
| 3 | Ta, Ar, Pi, Aq, Cp, Sg, Ar, Ta, Ge | 83 | Ta | Ge |
| 4 | Cn, Le, Vi, Li, Sc, Sg, Cp, Aq, Pi | 86 | Cn | Pi |

### 5.2 Savya-II Group (Bharani-type nakshatras)
**Applies to:** Bharani, Pushyami, Chitra, Poorvashadha, Uttarabhadrapada

| Pada | Dasha Sequence (9 signs) | Paramayus | Deha | Jeeva |
|------|--------------------------|-----------|------|-------|
| 1 | Sc, Li, Vi, Cn, Le, Ge, Ta, Ar, Pi | 100 | Sc | Pi |
| 2 | Aq, Cp, Sg, Ar, Ta, Ge, Cn, Le, Vi | 85 | Aq | Vi |
| 3 | Li, Sc, Sg, Cp, Aq, Pi, Sc, Li, Vi | 83 | Li | Vi |
| 4 | Cn, Le, Ge, Ta, Ar, Pi, Aq, Cp, Sg | 86 | Cn | Sg |

### 5.3 Apasavya-I Group (Rohini-type nakshatras)
**Applies to:** Rohini, Magha, Vishakha, Shravana

**IMPORTANT:** For Apasavya nakshatras, Deha and Jeeva are REVERSED — Deha = 9th sign, Jeeva = 1st sign.

| Pada | Dasha Sequence (9 signs) | Paramayus | Deha | Jeeva |
|------|--------------------------|-----------|------|-------|
| 1 | Sg, Cp, Aq, Pi, Ar, Ta, Ge, Le, Cn | 86 | Cn | Sg |
| 2 | Vi, Li, Sc, Pi, Aq, Cp, Sg, Sc, Li | 83 | Li | Vi |
| 3 | Vi, Le, Cn, Ge, Ta, Ar, Sg, Cp, Aq | 85 | Aq | Vi |
| 4 | Pi, Ar, Ta, Ge, Le, Cn, Vi, Li, Sc | 100 | Sc | Pi |

### 5.4 Apasavya-II Group (Mrigashira-type nakshatras)
**Applies to:** Mrigashira, Ardra, Poorvaphalguni, Uttaraphalguni, Anuradha, Jyeshtha, Dhanishtha, Shatabhisha

| Pada | Dasha Sequence (9 signs) | Paramayus | Deha | Jeeva |
|------|--------------------------|-----------|------|-------|
| 1 | Pi, Aq, Cp, Sg, Sc, Li, Vi, Le, Cn | 86 | Cn | Pi |
| 2 | Ge, Ta, Ar, Sg, Cp, Aq, Pi, Ar, Ta | 83 | Ta | Ge |
| 3 | Ge, Le, Cn, Vi, Li, Sc, Pi, Aq, Cp | 85 | Cp | Ge |
| 4 | Sg, Sc, Li, Vi, Le, Cn, Ge, Ta, Ar | 100 | Ar | Sg |

### 5.5 Paramayus Summary

| | Pada 1 | Pada 2 | Pada 3 | Pada 4 |
|---|--------|--------|--------|--------|
| **Savya** | 100 | 85 | 83 | 86 |
| **Apasavya** | 86 | 83 | 85 | 100 |

---

## 6. THE STRUCTURAL LOGIC (PVR Narasimha Rao's Discovery)

### 6.1 The Z and M(Z) Pattern

Let Z = zodiacal sequence: Ar, Ta, Ge, Cn, Le, Vi, Li, Sc, Sg, Cp, Aq, Pi
Let M(Z) = mirror images: Sc, Li, Vi, Cn, Le, Ge, Ta, Ar, Pi, Aq, Cp, Sg

Write Z and M(Z) consecutively = 24 signs. Write this cycle 3 times = 72 signs.
Split into dasha cycles of 9 signs each = 8 dasha cycles.

These 8 cycles correspond to the 4 padas x 2 groups within the Savya mega-cycle.

Similarly, inverse of Z = Pi, Aq, Cp, Sg, Sc, Li, Vi, Le, Cn, Ge, Ta, Ar and its mirror image, written 3 times and split into 8 cycles of 9, gives the Apasavya mega-cycle.

### 6.2 The Nava-Navamsha (D-81) Insight

**PVR Narasimha Rao's critical discovery:** The "dasha sequences" listed in BPHS for each pada are actually the **nava-navamsha (D-81)** — navamsha within navamsha — signs corresponding to the 9 equal parts of each pada.

**Derivation example — Ashwini 1st Pada:**
- Ashwini 1st pada = Aries navamsha
- Treat Aries as a rashi and find navamshas within it
- Aries contains: Ashwini 1, 2, 3, 4 + Bharani 1, 2, 3, 4 + Krittika 1
- Kalachakra navamshas: Ar, Ta, Ge, Cn, Le, Vi, Li, Sc, Sg
- This matches the dasha sequence exactly!

**Derivation example — Ashwini 2nd Pada:**
- Ashwini 2nd pada = Taurus navamsha
- Taurus contains: Krittika 2, 3, 4 + Rohini 1, 2, 3, 4 + Mrigashira 1, 2
- Kalachakra navamshas: Cp, Aq, Pi, Sc, Li, Vi, Cn, Le, Ge
- Note: Krittika is Savya, Rohini/Mrigashira are Apasavya — uses Kalachakra navamsha (not standard navamsha)

### 6.3 The Mahadasha vs. Bhukti Controversy

**Standard view (most scholars):** The 9-sign sequences are Mahadashas.

**Raghavacharya's view (supported by PVR):** The 9-sign sequences are actually **Antardashas/Bhuktis**, not Mahadashas. Mahadashas are a progression of Moon's navamsha (like Vimshottari is progression of Moon's nakshatra).

**Key verse (often ignored by scholars):**
> *"narasya janma kaale vaa prasna kaale yadamsakah*
> *tadaadi nava raaseenaamabdaastasyaayuruchyate"*

Translation: "Whatever navamsha is active at birth or prasna, years of nine amshas starting from it form the ayu (longevity)."

**Raghavacharya method (Mrigashira 4th pada example):**
- Mrigashira 4 = Aries Kalachakra navamsha
- 9 Mahadashas = 9 consecutive padas from Mrigashira 4: Mrigashira 4, Ardra 1, 2, 3, 4, Punarvasu 1, 2, 3, 4
- Their Kalachakra navamshas: Ar, Pi, Aq, Cp, Sg, Ar, Ta, Ge, Cn
- The BPHS sequences (Sg, Sc, Li, Vi, Le, Cn, Ge, Ta, Ar) are used for **Antardashas within** each Mahadasha
