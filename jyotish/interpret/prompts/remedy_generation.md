## Remedies & Recommendations

Generate personalized remedies for {{ name }} based on chart analysis.

### Current Dasha Focus
- Mahadasha: {{ current_dasha.mahadasha }}{% if is_md_lord_maraka %} (**MARAKA** for {{ lagna }} lagna — this is a dangerous period){% endif %}
- Antardasha: {{ current_dasha.antardasha }}{% if current_dasha.antardasha == lagnesh %} (**LAGNESH** — protective sub-period){% endif %}
- Lagna: {{ lagna }} ({{ lagna_en }})
- Lagnesh: {{ lagnesh }}

### Doshas to Address
{% for d in doshas %}
- {{ d.name }} ({{ d.name_hindi }}): {{ d.severity }} — {{ d.description }}
{% endfor %}

### Weak Planets Needing Strengthening
{% for s in strengths %}{% if not s.is_strong %}
- {{ s.planet }} (Rank {{ s.rank }}, Strength {{ s.strength }})
{% endif %}{% endfor %}

### Generate These Remedies:

#### 1. Gemstone Recommendations

## GEMSTONE DECISION FRAMEWORK FOR {{ lagna }} ({{ lagna_en }}) LAGNA

**ALWAYS SAFE — Recommend with confidence:**
- **Lagnesh stone:** {{ lagnesh_stone }} ({{ lagnesh }} is lagna lord — always beneficial)
{% if yogakaraka_planet %}- **Yogakaraka stone:** {{ yogakaraka_stone }} ({{ yogakaraka_planet }} is yogakaraka — most auspicious){% endif %}

{% if recommended_stones %}
**RECOMMENDED stones (functional benefics):**
{% for stone in recommended_stones %}
- {{ stone.stone }} for {{ stone.planet }} — {{ stone.reasoning | truncate(150) }}
{% endfor %}
{% endif %}

{% if test_stones %}
**USE WITH CAUTION (test before permanent wear):**
{% for stone in test_stones %}
- {{ stone.stone }} for {{ stone.planet }} — {{ stone.reasoning | truncate(150) }}
{% endfor %}
{% endif %}

**NEVER RECOMMEND — these are PROHIBITED for {{ lagna_en }} lagna:**
{% for stone in prohibited_stones %}
- ❌ {{ stone.stone }} ({{ stone.planet }}) — {{ stone.reasoning | truncate(150) }}
{% endfor %}

{% for m in maraka_planets %}
- ❌ {{ m.planet }}'s stone — {{ m.planet }} is {{ m.house_str }} = MARAKA for {{ lagna_en }} lagna. Wearing activates death-inflicting house.
{% endfor %}

**CONTRAINDICATIONS (never wear these together):**
{% for c in contraindications %}
- {{ c }}
{% endfor %}

**PLANETARY FRIEND/ENEMY GROUPS:**
- Friend group (can wear together): {{ friend_group }}
- Enemy group (NEVER combine with friend group stones): {{ enemy_group }}

**FOR THIS CHART SPECIFICALLY:**
- Current Mahadasha lord: {{ current_dasha.mahadasha }}
- Is Mahadasha lord benefic for {{ lagna_en }}? {% if is_md_lord_benefic %}YES{% else %}NO{% endif %}
- Is Mahadasha lord maraka? {% if is_md_lord_maraka %}YES — DANGEROUS PERIOD. Lagnesh stone ({{ lagnesh_stone }}) during Maraka Mahadasha = PROTECTIVE SHIELD (Parashar principle){% else %}No{% endif %}

For each stone recommendation, include: weight, finger, metal, wearing day, mantra.

#### 2. Weekly Routine
Create a personalized weekly routine:
| Day | Planet | Activity | Why (from chart) |
|-----|--------|----------|------------------|

#### 3. Mantras
- Primary mantra for current Mahadasha lord
- Lagna lord ({{ lagnesh }}) mantra — ALWAYS include this
- Any dosha-specific mantras

#### 4. Daan (Donations)
- What to donate, when, to whom
- Based on weak/afflicted planets
{% if is_md_lord_maraka %}- Special daan for {{ current_dasha.mahadasha }} as maraka — to reduce harmful effects{% endif %}

#### 5. Behavioral Remedies
- Most practical actions for the current period
- Direction to face while working (from lagna)
- Colors to wear/avoid

Format: Structured, practical, specific. Include Hindi mantras in Devanagari.
