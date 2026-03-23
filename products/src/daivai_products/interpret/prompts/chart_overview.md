## Chart Overview Analysis

Provide a comprehensive overview of this birth chart. Cover:

### 1. Lagna Analysis
- The {{ lagna }} ({{ lagna_en }}) ascendant and its characteristics
- Lagna lord ({{ lagnesh }}) placement and its implications
- Any planets in the 1st house
{% if lordship %}
**Lordship framework for {{ lagna_en }} lagna:**
- Lagnesh: {{ lagnesh }} — always the most important planet for the native
{% if yogakaraka_planet %}- Yogakaraka: {{ yogakaraka_planet }} — most auspicious functional planet{% endif %}
- Functional malefics:{% for m in functional_malefics %} {{ m.planet }}{% if not loop.last %},{% endif %}{% endfor %}

- Maraka planets:{% for m in maraka_planets %} {{ m.planet }} ({{ m.house_str }}){% if not loop.last %},{% endif %}{% endfor %}

{% endif %}

### 2. Strongest Planet
Based on the planetary strengths:
{% for s in strengths %}
- {{ s.planet }}: Rank {{ s.rank }}, Strength {{ s.strength }}{% if s.is_strong %} (STRONG){% endif %}
{% endfor %}

Identify the strongest and weakest planets and their impact. For each planet, note whether it is a functional benefic, malefic, or maraka for {{ lagna_en }} lagna.

### 3. Key Yogas
{% for y in yogas %}
- {{ y.name }} ({{ y.name_hindi }}): {{ y.description }}
{% endfor %}

Explain the most significant yogas and their life impact.

### 4. Vargottam Planets
{% if vargottam_planets %}Vargottam: {{ vargottam_planets | join(', ') }}{% else %}No vargottam planets.{% endif %}

{% if dispositor %}
### 5. Dispositor Chain (Planetary Energy Flow)
{% if dispositor.has_final_dispositor %}- Final Dispositor: **{{ dispositor.final_dispositor }}** — all planetary energy flows to this planet{% endif %}
{% if dispositor.mutual_receptions %}- Mutual Receptions: {{ dispositor.mutual_receptions | join(', ') }}{% endif %}
{% if dispositor.summary %}- {{ dispositor.summary }}{% endif %}
{% endif %}

{% if badhaka %}
### 6. Badhaka (Obstruction Analysis)
- Badhaka house: {{ badhaka.badhaka_house }}, Lord: **{{ badhaka.badhaka_lord }}** (in house {{ badhaka.badhaka_lord_house }})
- Severity: {{ badhaka.severity }}{% if badhaka.rahu_ketu_association %} — **Rahu/Ketu association** (past-life karmic blocks){% endif %}
{% if badhaka.obstruction_domains %}- Obstruction domains: {{ badhaka.obstruction_domains | join(', ') }}{% endif %}
{% endif %}

{% if bhavat_bhavam %}
### 7. Bhavat Bhavam (House-from-House Reinforcement)
Key derived houses and how they strengthen or weaken primary houses:
{% for bb in bhavat_bhavam %}{% if bb.house in [1, 2, 7, 10] %}
- House {{ bb.house }} reinforced by House {{ bb.derived_house }}: {{ bb.primary_lord }} (primary) — {{ bb.derived_lord }} (derived) — {{ bb.relationship }}
{% endif %}{% endfor %}
Analyze how derived-house lords support or undermine the primary houses.
{% endif %}

{% if chandra_kundali %}
### 8. Moon Chart Perspective (Chandra Kundali)
From Moon as reference lagna:
{% if chandra_kundali.kendras %}- Kendra planets: {{ chandra_kundali.kendras | join(', ') }}{% endif %}
{% if chandra_kundali.trikonas %}- Trikona planets: {{ chandra_kundali.trikonas | join(', ') }}{% endif %}
{% if chandra_kundali.dusthanas %}- Dusthana planets: {{ chandra_kundali.dusthanas | join(', ') }}{% endif %}
{% if chandra_kundali.summary %}- {{ chandra_kundali.summary }}{% endif %}
{% endif %}

{% if surya_kundali %}
### 9. Sun Chart Perspective (Surya Kundali)
From Sun as reference lagna (career/authority/soul purpose):
{% if surya_kundali.kendras %}- Kendra planets: {{ surya_kundali.kendras | join(', ') }}{% endif %}
{% if surya_kundali.trikonas %}- Trikona planets: {{ surya_kundali.trikonas | join(', ') }}{% endif %}
{% if surya_kundali.summary %}- {{ surya_kundali.summary }}{% endif %}
{% endif %}

{% if nisheka %}
### 10. Nisheka (Conception Chart Verification)
- Estimated conception: {{ nisheka.conception_date }}
- Nisheka Lagna: {{ nisheka.nisheka_lagna_sign }} | Moon: {{ nisheka.nisheka_moon_sign }}
- Birth verification: {% if nisheka.verification_passed %}**PASSED** — birth data consistent with BPHS Ch.4 rules{% else %}Inconclusive{% endif %}
{% if nisheka.summary %}- {{ nisheka.summary }}{% endif %}
{% endif %}

### Overall Life Theme
Based on the lagna, Moon nakshatra, and dominant planetary influences, describe the overall life theme for {{ name }}. Reference the functional benefic/malefic/maraka classification for {{ lagna_en }} lagna. Integrate dispositor flow, badhaka obstructions, and bhavat bhavam reinforcements into the synthesis.

Format: Use both English and Hindi key terms. Be specific with house numbers and planet references.
