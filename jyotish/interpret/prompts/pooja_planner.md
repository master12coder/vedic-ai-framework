## Personalized Pooja Planner

Generate a weekly and monthly worship schedule for {{ name }} based on their chart.

### Chart Context
- Lagna: {{ lagna }} ({{ lagna_en }})
- Current Dasha: {{ current_dasha.mahadasha }}-{{ current_dasha.antardasha }}

### Planetary Strengths
{% for s in strengths %}
- {{ s.planet }}: Rank {{ s.rank }}{% if s.is_strong %} (STRONG){% endif %}
{% endfor %}

### Doshas Active
{% for d in doshas %}
- {{ d.name }}: {{ d.description }}
{% endfor %}

### Generate
Create a personalized worship schedule:

#### Weekly Pooja Schedule
| Day | Planet Focus | Temple/Deity | Mantra | Reason (from chart) |
|-----|-------------|-------------|--------|---------------------|

Rules:
- ALWAYS strengthen the Lagna lord
- Yogakaraka planet should have dedicated worship
- Current Mahadasha lord needs attention
- Skip worship for pure malefic lords (6th lord, unless also trikona lord)

#### Monthly Observances
- Which Ekadashi to observe
- Pradosh vrat if Saturn needs strengthening
- Specific Poornima/Amavasya rituals based on Moon placement

#### Special Remedies for Current Period
Based on {{ current_dasha.mahadasha }}-{{ current_dasha.antardasha }}:
- Specific mantra with count
- Specific daan items and timing
- Behavioral adjustment

Format: Include Hindi mantras in Devanagari. Be specific to this chart.
