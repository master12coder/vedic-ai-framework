## Lal Kitab Assessment & Remedies

Generate Lal Kitab-specific analysis for {{ name }} ({{ lagna }} Lagna).

**IMPORTANT:** Lal Kitab is a PARALLEL system to Parashari. It uses house-based
planet placement (Pakka Ghar), NOT sign-based dignity. Do NOT mix Parashari
lordship rules with Lal Kitab logic.

### Chart Basics
- Name: {{ name }}
- Lagna: {{ lagna }} ({{ lagna_en }})
- Current Dasha: {{ current_dasha.mahadasha }} > {{ current_dasha.antardasha }}

{% if lal_kitab %}
### Lal Kitab Planet Assessment
- Strongest Planet: {{ lal_kitab.strongest_planet }}
- Weakest Planet: {{ lal_kitab.weakest_planet }}
{% if lal_kitab.dormant_planets %}- Dormant (Soya Hua): {{ lal_kitab.dormant_planets | join(', ') }}{% endif %}

{% if lal_kitab.rins %}
### Rins (Karmic Debts)
{% for r in lal_kitab.rins %}
- **{{ r.name }}**: {{ r.severity }}
{% endfor %}
{% endif %}

{% if lal_kitab.remedies %}
### Matched Remedies
{% for r in lal_kitab.remedies %}
- {{ r.planet }} (House {{ r.house }}): {{ r.remedy }}
{% endfor %}
{% endif %}
{% else %}
*Lal Kitab data not available — compute full analysis first.*
{% endif %}

### Generate:
1. **Lal Kitab Planet Report** — For each planet, describe its Lal Kitab house position,
   whether it is in its Pakka Ghar, and its effect per Lal Kitab rules (NOT Parashari).

2. **Rin Analysis** — Explain each debt (Pitra Rin, Matri Rin, Stri Rin) and its
   karmic significance. Include the cause and the remedy tradition.

3. **Practical Remedies** — List 5-7 actionable Lal Kitab remedies. Include:
   - Daan (donations) with specific items and days
   - Behavioral remedies (things to avoid)
   - Ritual remedies (specific worship practices)
   - Object remedies (items to keep/wear)

4. **Dormant Planet Revival** — If any planets are dormant (Soya Hua), explain
   the Lal Kitab method to awaken them.

**Rules:**
- Use only Lal Kitab terminology and reasoning
- Do NOT recommend gemstones here (that is Parashari domain)
- Remedies must be practical and accessible
- Include Hindi/Urdu terms where traditional (e.g., "daan", "upay")
