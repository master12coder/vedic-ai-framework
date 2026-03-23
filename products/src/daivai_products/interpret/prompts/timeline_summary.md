## 10-Year Forecast & Timeline

Provide a timeline forecast for {{ name }} based on upcoming dasha periods.

### Dasha Timeline
{% for md in mahadashas %}
- **{{ md.lord }} Mahadasha:** {{ md.start }} to {{ md.end }}
{% endfor %}

### Current Period
- Running: {{ current_dasha.mahadasha }}-{{ current_dasha.antardasha }}

{% if dasha_transit %}
### Dasha-Transit Current Assessment
- Overall: **{{ dasha_transit.overall_favorability }}**
- {{ dasha_transit.summary }}
{% if dasha_transit.event_domains %}- Active life domains: {{ dasha_transit.event_domains | join(', ') }}{% endif %}
{% endif %}

{% if yoga_timings %}
### Yoga Activation Windows
- {{ yoga_timings.summary }}
{% if yoga_timings.currently_active %}- **Currently Active Yogas:** {{ yoga_timings.currently_active | join(', ') }}{% endif %}
{% if yoga_timings.most_significant %}- Most Significant: {{ yoga_timings.most_significant }}{% endif %}
{% endif %}

{% if eclipse_impacts %}
### Upcoming Eclipse Impacts
{% for ei in eclipse_impacts %}{% if ei.is_significant %}
- **{{ ei.type }}** on {{ ei.date }}: Most affected planet — **{{ ei.most_affected }}**. {{ ei.summary }}
{% endif %}{% endfor %}
{% for ei in eclipse_impacts %}{% if not ei.is_significant %}
- {{ ei.type }} on {{ ei.date }}: {{ ei.most_affected }} — minor impact
{% endif %}{% endfor %}
Factor significant eclipses into the year-by-year forecast below.
{% endif %}

### Forecast Requirements

#### Year-by-Year Summary (Next 10 Years)
For each year, provide:
- Dominant dasha influence
- Key themes (career, health, relationships, finances)
- Best months and challenging months
- One actionable recommendation

#### Golden Periods
Identify the most favorable upcoming periods based on:
- Benefic planet dashas
- Yogakaraka dasha
- Trikona lord periods

#### Challenging Periods
Identify periods needing caution:
- Dusthana lord dashas
- Maraka periods
- Saturn/Rahu transits

#### Key Decision Windows
Best times for: property purchase, career change, marriage, health investments.

Format: Year-by-year breakdown with specific months where possible.
