## Relationship Analysis

Analyze relationships and marriage for {{ name }}:

### 7th House (Kalatra Bhava — Marriage House)
- 7th house sign from {{ lagna }} lagna
- 7th lord placement, dignity, and aspects
- Venus's role (natural significator of marriage)
{% if maraka_planets %}
**IMPORTANT:** For {{ lagna_en }} lagna, the following planets are MARAKA (from 2nd/7th houses):
{% for m in maraka_planets %}
- {{ m.planet }} — {{ m.house_str }}. {{ m.reasoning | truncate(120) }}
{% endfor %}
The 7th lord's maraka status must be acknowledged alongside marriage significations.
{% endif %}

### Marriage Timing
- Which dasha periods favor marriage
- Current period: {{ current_dasha.mahadasha }}-{{ current_dasha.antardasha }}
{% if is_md_lord_maraka %}
- **NOTE:** Current Mahadasha lord {{ current_dasha.mahadasha }} is MARAKA for {{ lagna_en }} lagna. If {{ current_dasha.mahadasha }} owns the 7th house, its dasha can simultaneously bring marriage AND maraka effects (health/financial stress). Interpret BOTH sides.
{% endif %}

### Mangal Dosha Check
{% for d in doshas %}{% if d.name == 'Mangal Dosha' %}
- {{ d.name }}: {{ d.severity }} — {{ d.description }}
{% endif %}{% endfor %}
{% if functional_malefics %}
**Lordship-Specific Mangal Dosha Context for {{ lagna_en }} lagna:**
{% for m in functional_malefics %}{% if m.planet == 'Mars' %}
- Mars owns houses {{ m.houses_owned | join(' and ') }} for this lagna: {{ m.reasoning | truncate(200) }}
- The Mangal Dosha interpretation MUST consider Mars's functional role for this lagna, not just its house position.
- If Mars owns an upachaya (3/6/11), the dosha effect is different from Mars owning a dusthana (6/8/12).
{% endif %}{% endfor %}
{% endif %}

**Standard Mangal Dosha Cancellation Rules to Check:**
1. Mars in own sign or exaltation — partial cancellation
2. Mars aspected by Jupiter (natural benefic) — reduces severity
3. Mars in 1st/4th/7th/8th/12th from Lagna, Moon, OR Venus — check all three
4. Partner has matching dosha — mutual cancellation
5. After age 28 — Mangal Dosha intensity reduces (Mars matures)

### 5th House (Children)
- 5th lord and Jupiter (putrakaraka) analysis
- Favorable periods for children

### Key Relationship Planets
{% for p in planets %}{% if p.name in ['Venus', 'Jupiter', 'Moon'] %}
- {{ p.name }} in {{ p.sign }}, House {{ p.house }}, {{ p.dignity }}{% if p.name == 'Jupiter' and maraka_planets %}{% for m in maraka_planets %}{% if m.planet == 'Jupiter' %} **(MARAKA for this lagna)**{% endif %}{% endfor %}{% endif %}
{% endif %}{% endfor %}

{% if bhavat_bhavam %}
### Bhavat Bhavam — Relationship Reinforcement
{% for bb in bhavat_bhavam %}{% if bb.house == 7 %}
- 7th house reinforced by **House {{ bb.derived_house }}** (7th from 7th = Lagna): {{ bb.primary_lord }} ↔ {{ bb.derived_lord }} ({{ bb.relationship }})
{% endif %}{% endfor %}
The 7th-from-7th is the 1st house (self) — the quality of partnerships mirrors the native's own personality strength.
{% endif %}

### Navamsha (D9) Insights
Navamsha is the chart of dharma and marriage. Vargottam planets: {{ vargottam_planets | join(', ') if vargottam_planets else 'None' }}

Format: Be sensitive and positive. Reference specific dasha periods for timing.
