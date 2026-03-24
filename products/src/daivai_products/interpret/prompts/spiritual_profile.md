## Spiritual & Psychological Profile

Analyze the spiritual and psychological nature of {{ name }}:

### Moon Nakshatra Analysis
{% for p in planets %}{% if p.name == 'Moon' %}
- Moon in {{ p.nakshatra }}, Pada {{ p.pada }}
- Moon sign: {{ p.sign }} ({{ p.sign_en }})
- Moon house: {{ p.house }}
{% endif %}{% endfor %}

This nakshatra reveals the core psychological nature, emotional patterns, and spiritual inclinations.

### Lagna & Moon Combination
- Lagna: {{ lagna }} — external personality
- Moon: The emotional self and subconscious patterns
{% if lagnesh %}
- Lagnesh {{ lagnesh }} connects identity to its house placement and dignity
{% endif %}

### 9th House (Dharma Bhava)
- 9th lord placement and its spiritual implications{% if house_lords %} — 9th Lord: {{ house_lords.get(9, 'Unknown') }}{% endif %}
- Jupiter (guru planet) analysis
{% for m in maraka_planets %}{% if m.planet == 'Jupiter' %}
**Note:** Jupiter is MARAKA for {{ lagna_en }} lagna. Its spiritual guidance role is complicated by maraka status. The native may experience spiritual growth through challenging experiences.
{% endif %}{% endfor %}

### 12th House (Moksha Bhava)
- 12th house connections to spirituality and liberation{% if house_lords %} — 12th Lord: {{ house_lords.get(12, 'Unknown') }}{% endif %}
- Ketu's placement (natural moksha karaka)

### Psychological Strengths
Based on strong planets:
{% for s in strengths %}{% if s.is_strong %}
- {{ s.planet }} (Rank {{ s.rank }}): Psychological strength this brings
{% endif %}{% endfor %}

### Spiritual Practices Suited
Based on the Moon nakshatra and dominant planets, recommend spiritual practices.
- Align practices with functional benefics for {{ lagna_en }} lagna
- {{ lagnesh }} mantra is always primary for self-realization

{% if d60_info %}
### D60 Shastyamsha (Past-Life Indicators)
- {{ d60_info.summary }}
- Benefic D60 placements: {{ d60_info.benefic_count }} | Malefic: {{ d60_info.malefic_count }}
{% endif %}

Format: Deep, introspective tone. Use both Hindi spiritual terms and English explanations.
