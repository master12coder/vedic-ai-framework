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

### 5. Overall Life Theme
Based on the lagna, Moon nakshatra, and dominant planetary influences, describe the overall life theme for {{ name }}. Reference the functional benefic/malefic/maraka classification for {{ lagna_en }} lagna.

Format: Use both English and Hindi key terms. Be specific with house numbers and planet references.
