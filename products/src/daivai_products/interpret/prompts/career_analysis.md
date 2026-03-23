## Career Analysis

Analyze the career prospects for {{ name }} based on:

### 10th House (Karma Bhava)
- 10th house sign from {{ lagna }} lagna
- 10th lord placement, dignity, and aspects
- Any planets in the 10th house
{% if house_lords %}
- 10th lord for {{ lagna_en }}: {{ house_lords.get(10, 'Unknown') }}
{% for m in functional_malefics %}{% if m.planet == house_lords.get(10, '') %}
**IMPORTANT:** The 10th lord ({{ m.planet }}) is a FUNCTIONAL MALEFIC for {{ lagna_en }} lagna (owns houses {{ m.houses_owned | join(', ') }}). Career success through this planet comes with complications.
{% endif %}{% endfor %}
{% for m in maraka_planets %}{% if m.planet == house_lords.get(10, '') %}
**CRITICAL:** The 10th lord ({{ m.planet }}) is also a MARAKA for {{ lagna_en }} lagna ({{ m.house_str }}). Career growth and maraka effects happen SIMULTANEOUSLY. Career advancement may come WITH financial drain or health stress.
{% endif %}{% endfor %}
{% endif %}

### Key Career Indicators
- Dasamsha (D10) implications
- 10th lord's nakshatra and its career significations
- Mercury's strength (communication/business)
- Saturn's role (discipline/service)

### Current Career Dasha
- Current Mahadasha: {{ current_dasha.mahadasha }} ({{ current_dasha.md_start }} to {{ current_dasha.md_end }})
- Current Antardasha: {{ current_dasha.antardasha }}
{% if is_md_lord_maraka %}
**{{ current_dasha.mahadasha }} Mahadasha is a MARAKA period for {{ lagna_en }} lagna.**
{% for m in maraka_planets %}{% if m.planet == current_dasha.mahadasha %}
{{ current_dasha.mahadasha }} owns {{ m.house_str }}. This creates a SIMULTANEOUS pattern: whatever positive houses {{ current_dasha.mahadasha }} owns will give results, BUT the maraka effects (health risks, financial drain) run in parallel.
{% endif %}{% endfor %}
{% if current_dasha.antardasha == lagnesh %}
The current {{ current_dasha.antardasha }} Antardasha (LAGNESH) provides a PROTECTIVE window within the maraka Mahadasha. This is the best sub-period for self-strengthening and wearing the Lagnesh stone ({{ lagnesh_stone }}).
{% endif %}
{% endif %}

### Career Timeline
Map the dasha periods to career phases:
{% for md in mahadashas %}
- {{ md.lord }} Mahadasha ({{ md.start }} to {{ md.end }}): Career implications{% for m in maraka_planets %}{% if m.planet == md.lord %} **[MARAKA PERIOD]**{% endif %}{% endfor %}
{% endfor %}

For each dasha, state whether the lord is a functional benefic, malefic, or maraka for {{ lagna_en }} lagna.

{% if bhavat_bhavam %}
### Bhavat Bhavam — Career Reinforcement
{% for bb in bhavat_bhavam %}{% if bb.house == 10 %}
- 10th house reinforced by **House {{ bb.derived_house }}** (10th from 10th): {{ bb.primary_lord }} ↔ {{ bb.derived_lord }} ({{ bb.relationship }})
{% endif %}{% endfor %}
The 10th-from-10th house shows the *foundation* of career success — its lord's strength directly impacts professional longevity.
{% endif %}

### Recommended Career Fields
Based on the chart's dominant planets and houses, suggest suitable career fields.

Format: Be specific with timing using dasha periods. Use both English and Hindi terms.
