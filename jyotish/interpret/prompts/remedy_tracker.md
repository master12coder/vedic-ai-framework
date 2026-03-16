## Remedy Effectiveness Tracker

Review the remedies being followed and assess effectiveness for {{ name }}.

### Chart Context
- Lagna: {{ lagna }} ({{ lagna_en }})
- Current Dasha: {{ current_dasha.mahadasha }}-{{ current_dasha.antardasha }}

### Current Transits
{% if transits %}
{% for t in transits %}
- {{ t.name }} in {{ t.sign }} (House {{ t.house }}){% if t.retrograde %} [R]{% endif %}
{% endfor %}
{% endif %}

### Doshas Being Addressed
{% for d in doshas %}
- {{ d.name }}: {{ d.severity }} — {{ d.description }}
{% endfor %}

### Assessment Required

#### For Each Active Remedy, Evaluate:
1. Is the remedy still relevant for the current dasha period?
2. Has the transit picture changed (requiring remedy adjustment)?
3. Gemstone review: any contraindication changes?

#### Monthly Check Questions:
- Financial trend: improving/stable/declining?
- Health: any new issues?
- Relationships: harmony level?
- Career: progress/stagnation?

#### Remedy Adjustment Recommendations:
Based on transit changes and dasha progression, suggest:
- Which remedies to continue
- Which to pause (dasha period ended)
- New remedies to add for upcoming period

Format: Structured assessment with specific timeline references.
