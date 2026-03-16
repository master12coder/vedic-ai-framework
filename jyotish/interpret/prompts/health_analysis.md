## Health Analysis

Analyze the health profile for {{ name }} based on:

### 6th House (Roga Bhava — Disease House)
- 6th house lord placement and dignity{% if house_lords %} — 6th Lord: {{ house_lords.get(6, 'Unknown') }}{% endif %}
- Any planets in the 6th house
- Malefic influences on the 6th house

### Planet-Body Mapping
- Sun → Heart, bones, eyes, vitality
- Moon → Mind, blood, fluids, lungs
- Mars → Blood, muscles, head, accidents
- Mercury → Nervous system, skin, speech
- Jupiter → Liver, fat, diabetes, growth
- Venus → Reproductive system, kidneys, throat
- Saturn → Joints, teeth, chronic disease, aging

### Vulnerable Periods
Based on dasha of 6th/8th lord or afflicted planets:
{% for md in mahadashas %}
- {{ md.lord }} period: Health implications{% for m in maraka_planets %}{% if m.planet == md.lord %} **[MARAKA PERIOD — heightened health risk. {{ m.planet }} owns {{ m.house_str }}]**{% endif %}{% endfor %}
{% endfor %}
{% if maraka_planets %}

**MARAKA PLANET HEALTH WARNING for {{ lagna_en }} lagna:**
{% for m in maraka_planets %}
- **{{ m.planet }}** is MARAKA ({{ m.house_str }}). During {{ m.planet }}'s Mahadasha/Antardasha, the native faces elevated health and mortality risk. Preventive care is critical.
{% endfor %}
{% endif %}

### Current Health Focus
- Current Mahadasha: {{ current_dasha.mahadasha }}{% if is_md_lord_maraka %} **(MARAKA — active health risk period)**{% endif %}
- Which body systems need attention now
{% if is_md_lord_maraka %}
- The {{ current_dasha.mahadasha }} Mahadasha being a maraka period means the body systems ruled by {{ current_dasha.mahadasha }} need extra attention. Lagnesh ({{ lagnesh }}) strengthening is protective.
{% endif %}

### Doshas Affecting Health
{% for d in doshas %}
- {{ d.name }}: {{ d.description }}
{% endfor %}

### Preventive Recommendations
Based on weak planets and vulnerable periods, suggest preventive health measures.
{% if lagnesh_stone %}
- Wearing {{ lagnesh_stone }} (Lagnesh stone) is always protective for overall health.
{% endif %}

Format: Be specific but sensitive. Reference specific planets and periods.
