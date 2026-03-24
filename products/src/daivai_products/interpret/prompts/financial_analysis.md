## Financial Analysis

Analyze the wealth and financial prospects for {{ name }} based on:

### Key Financial Houses
- **2nd House (Dhana Bhava):** Accumulated wealth, family money, speech{% if house_lords %} — Lord: {{ house_lords.get(2, 'Unknown') }}{% for m in maraka_planets %}{% if m.planet == house_lords.get(2, '') %} **(MARAKA)**{% endif %}{% endfor %}{% endif %}
- **11th House (Labha Bhava):** Income, gains, fulfillment of desires{% if house_lords %} — Lord: {{ house_lords.get(11, 'Unknown') }}{% endif %}
- **5th House:** Speculative gains, past life merit{% if house_lords %} — Lord: {{ house_lords.get(5, 'Unknown') }}{% endif %}
- **9th House (Bhagya Bhava):** Fortune, luck{% if house_lords %} — Lord: {{ house_lords.get(9, 'Unknown') }}{% endif %}

### Dhan Yogas Present
{% for y in yogas %}
{% if 'Dhan' in y.name or 'Lakshmi' in y.name %}
- {{ y.name }}: {{ y.description }}
{% endif %}
{% endfor %}

### Jupiter's Role
Jupiter is the natural significator of wealth. Its placement:
{% for p in planets %}{% if p.name == 'Jupiter' %}
- Jupiter in {{ p.sign }}, House {{ p.house }}, Dignity: {{ p.dignity }}
{% for m in maraka_planets %}{% if m.planet == 'Jupiter' %}
**NOTE:** Jupiter is a MARAKA for {{ lagna_en }} lagna ({{ m.house_str }}). Jupiter's wealth significations are MODIFIED by its maraka status — financial gains may come with strings attached (health costs, unexpected expenses).
{% endif %}{% endfor %}
{% endif %}{% endfor %}

### Financial Timeline by Dasha
{% for md in mahadashas %}
- {{ md.lord }} period ({{ md.start }} - {{ md.end }}): Financial implications{% for m in maraka_planets %}{% if m.planet == md.lord %} **[MARAKA — financial drain risk]**{% endif %}{% endfor %}
{% endfor %}

{% if hora_info %}
### Hora Chart (Wealth Indicator)
- {{ hora_info.wealth_indicator }}
{% if hora_info.sun_hora_planets %}- Planets in Sun's Hora (self-earned wealth): {{ hora_info.sun_hora_planets | join(', ') }}{% endif %}
{% if hora_info.moon_hora_planets %}- Planets in Moon's Hora (inherited/passive wealth): {{ hora_info.moon_hora_planets | join(', ') }}{% endif %}
{% endif %}

{% if bhavat_bhavam %}
### Bhavat Bhavam — Wealth Reinforcement
{% for bb in bhavat_bhavam %}{% if bb.house in [2, 11] %}
- House {{ bb.house }} reinforced by **House {{ bb.derived_house }}**: {{ bb.primary_lord }} ↔ {{ bb.derived_lord }} ({{ bb.relationship }})
{% endif %}{% endfor %}
The 2nd-from-2nd (3rd) and 11th-from-11th (9th) houses reveal the *sustainability* of wealth — strong derived lords indicate lasting financial growth.
{% endif %}

### Wealth-Building Advice
Based on strong houses and planets, suggest optimal financial strategies. Reference functional benefic/malefic classification for {{ lagna_en }} lagna.

Format: Include specific dasha periods for financial highs and lows. Hindi + English.
