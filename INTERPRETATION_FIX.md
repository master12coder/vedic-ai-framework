# CRITICAL FIX: Interpretation Accuracy
# The LLM is giving GENERIC Vedic astrology instead of chart-specific analysis.
# The knowledge exists in YAML files — prompts just don't inject it.

---

## THE PROBLEM

Current flow:
  Chart computed (ACCURATE) → LLM gets raw positions → LLM GUESSES interpretation
  
Required flow:
  Chart computed → Lordship rules loaded for THIS lagna → Gemstone logic loaded → 
  Scripture citations loaded → Pandit Ji learned rules loaded → ALL injected into 
  prompt → LLM interprets WITH full context

---

## WHAT TO FIX

### Fix 1: interpreter.py — Load ALL knowledge before EVERY LLM call

The interpreter must build a comprehensive context package for each chart:

```python
def build_interpretation_context(chart_data):
    """Build complete context from all knowledge sources for this specific chart"""
    
    lagna = chart_data.lagna_sign  # e.g., "Mithuna"
    
    context = {}
    
    # 1. Lordship rules for THIS lagna
    lordship = load_yaml("knowledge/lordship_rules.yaml")
    context["lordship"] = lordship["lagnas"][lagna.lower()]
    # Includes: yogakaraka, benefics, malefics, maraka, gemstone recommendations
    
    # 2. Gemstone logic with contraindications
    gemstones = load_yaml("knowledge/gemstone_logic.yaml")
    context["gemstones"] = gemstones
    context["prohibited_stones"] = get_prohibited_for_lagna(lagna, lordship)
    context["recommended_stones"] = get_recommended_for_lagna(lagna, lordship)
    
    # 3. Scripture citations for planets in their houses
    scripture_rules = []
    for planet_name, planet in chart_data.planets.items():
        rules = scripture_db.query_by_planet(planet_name, planet.house)
        scripture_rules.extend(rules)
    context["scripture_citations"] = scripture_rules
    
    # 4. Pandit Ji learned rules (if any exist for this lagna)
    pandit_rules = correction_store.get_prompt_additions(lagna, 
        [p.name for p in chart_data.planets.values()])
    context["pandit_teachings"] = pandit_rules
    
    # 5. Yoga-specific interpretations
    for yoga in chart_data.yogas:
        yoga_rules = scripture_db.query_by_topic(yoga.name)
        context.setdefault("yoga_citations", []).extend(yoga_rules)
    
    return context
```

### Fix 2: EVERY prompt template must include MANDATORY RULES section

Add this to the TOP of every prompt template (before any interpretation request):

```markdown
## MANDATORY RULES FOR {{lagna}} LAGNA — DO NOT VIOLATE

### Lordship Classification:
- Yogakaraka: {{lordship.yogakaraka}} — BEST planet, always strengthen
- Functional Benefics: {{lordship.functional_benefics | join(', ')}}
- Functional Malefics: {{lordship.functional_malefics | join(', ')}}
- MARAKA (harmful) planets: {% for m in lordship.maraka %}{{m.planet}} ({{m.house}} lord — {{m.reason}}){% endfor %}

### GEMSTONE RULES (CRITICAL — wrong stones can HARM):
RECOMMENDED stones for {{lagna}}:
{% for stone in recommended_stones %}
- {{stone.stone}} for {{stone.planet}} — {{stone.reason}}
{% endfor %}

ABSOLUTELY PROHIBITED stones for {{lagna}}:
{% for stone in prohibited_stones %}
- {{stone.stone}} for {{stone.planet}} — {{stone.reason}}
{% endfor %}

### INTERPRETATION RULES:
- Every statement MUST reference a specific planetary position, house, or dasha
- Every gemstone recommendation MUST check against prohibited list above
- MARAKA planets: acknowledge BOTH their positive house AND maraka role
  Example: "Jupiter owns 10th (career, good) BUT ALSO 7th (maraka, harmful)"
- Do NOT give generic interpretations — tie EVERYTHING to this specific chart
```

### Fix 3: Gemstone prompt must use gemstone_logic.yaml decision framework

The remedy_generation.md prompt must include:

```markdown
## GEMSTONE DECISION FRAMEWORK FOR {{lagna}} LAGNA

ALWAYS SAFE:
- Lagnesh stone: {{lagnesh_stone}} ({{lagnesh}} is 1st lord)
- Yogakaraka stone: {{yogakaraka_stone}} ({{yogakaraka}} is yogakaraka)

USE WITH CAUTION:
- Current Mahadasha lord stone (only if lord is benefic for this lagna)
- Mixed lords (e.g., 8th+9th) — explain both sides

NEVER RECOMMEND:
{% for m in maraka_planets %}
- {{m.planet}}'s stone ({{m.planet}} is {{m.house}} lord = MARAKA for {{lagna}})
{% endfor %}
{% for ml in malefic_planets %}
- {{ml}}'s stone ({{ml}} is functional malefic for {{lagna}})
{% endfor %}

SPECIFIC CONTRAINDICATIONS:
- Never wear stones from enemy planetary groups together
- Friends group: {{friend_group}}
- Enemy group: {{enemy_group}}

FOR THIS CHART SPECIFICALLY:
- Current Mahadasha: {{current_md.lord}}
- Is Mahadasha lord benefic for {{lagna}}? {{is_md_lord_benefic}}
- Lagnesh stone during Maraka Mahadasha = PROTECTIVE SHIELD (Parashar principle)
```

### Fix 4: Specific fixes for Mithuna Lagna interpretation

For Mithuna lagna specifically, the system MUST know:

```yaml
mithuna_critical_rules:
  mercury:
    role: "LAGNESH (1st+4th lord) — most important planet"
    stone: "Panna (Emerald)"
    assessment: "param_shubh"
    note: "During Maraka Mahadasha, Lagnesh stone = protective shield"
  
  venus:
    role: "5th+12th lord — Yogakaraka (debatable, 5th is trikona)"
    stone: "Safed Pukhraj / Heera"
    assessment: "shubh"
    note: "Currently wearing 13 Ratti — Pandit Ji says reduce to 6-7"
  
  saturn:
    role: "8th+9th lord — MIXED (bhagya + arishta)"
    stone: "Neelam (Blue Sapphire)"
    assessment: "test_required"
    note: "5-night pillow test mandatory. Pandit Ji consent required."
  
  jupiter:
    role: "7th+10th lord — MARAKA"
    stone: "Peela Pukhraj (Yellow Sapphire)"
    assessment: "NEVER_WEAR"
    danger: "7th = maraka sthaan. Will cause dhan hani, swasthya hani."
    note: "Career growth from 10th lordship comes WITH financial drain from 7th lordship. Both happen simultaneously."
  
  mars:
    role: "6th+11th lord — functional malefic"
    stone: "Moonga (Red Coral)"
    assessment: "NEVER_WEAR"
    danger: "6th lord = shatru, rog, karz. Activating Mars increases enemies, disease, debt."
  
  moon:
    role: "2nd lord — MARAKA"
    stone: "Moti (Pearl)"
    assessment: "NEVER_WEAR"
    danger: "2nd = maraka sthaan. Dhan/swasthya hani."
  
  sun:
    role: "3rd lord — neutral (trishadaya)"
    stone: "Manikya (Ruby)"
    assessment: "unnecessary"
    note: "Neither shubh nor ashubh. Waste of money."
  
  rahu:
    stone: "Gomed (Hessonite)"
    assessment: "context_dependent"
  
  ketu:
    stone: "Lehsunia (Cat's Eye)"
    assessment: "context_dependent"

  friend_group: "Budh + Shukra + Shani → Panna + Safed Pukhraj + Neelam can be worn together"
  enemy_group: "Guru + Mangal + Surya + Chandra → their stones should NEVER be combined with friend group"
```

### Fix 5: Mangal Dosha interpretation must be lagna-specific

Current: "Full Mangal Dosha — Mars in 12th house"
Required: Mars is 6th+11th lord for Mithuna. The dosha interpretation must consider:
- Mars ALSO owns 11th (gains) — so it's not purely malefic
- Mars in 12th = expenditure through enemies/competition, but also gains through foreign/hidden sources
- The standard Mangal Dosha cancellation rules must be checked:
  - Mars in own sign? No (Vrishabha is Venus's sign)
  - Mars aspected by benefic? Check Jupiter's aspect
  - Partner has matching dosha? Check if applicable
- Severity should be rated considering lordship, not just house position

### Fix 6: Current dasha interpretation must acknowledge Maraka

Current: "Jupiter period brings growth"
Required: "Jupiter Mahadasha is MARAKA period for Mithuna lagna. Jupiter owns 7th (maraka) AND 10th (career). This creates a SIMULTANEOUS pattern: career advancement WITH financial drain. Both effects are real and happen together, not separately. The current Mercury antardasha (Lagnesh) provides a PROTECTIVE window — this is when to wear Panna and strengthen Mercury for maximum protection against Jupiter's maraka effects."

### Fix 7: Add chart-specific validation in interpreter

After LLM generates interpretation, run a POST-CHECK:

```python
def validate_interpretation(interpretation_text, chart_data, lordship_rules):
    """Check LLM output for dangerous errors before showing to user"""
    
    lagna = chart_data.lagna_sign.lower()
    rules = lordship_rules["lagnas"][lagna]
    
    errors = []
    
    # Check: did LLM recommend a prohibited stone?
    prohibited = get_prohibited_stones(rules)
    for stone in prohibited:
        if stone.lower() in interpretation_text.lower():
            # Check if it's in a "recommended" context vs "avoid" context
            # Flag if recommended
            errors.append(f"DANGER: {stone} recommended but is PROHIBITED for {lagna} lagna")
    
    # Check: did LLM call a maraka planet "benefic"?
    for maraka in rules["maraka"]:
        planet = maraka["planet"]
        if f"{planet} is benefic" in interpretation_text or f"{planet} is auspicious" in interpretation_text:
            errors.append(f"ERROR: {planet} called benefic but is MARAKA for {lagna}")
    
    # Check: did LLM recommend worshipping a maraka planet?
    for maraka in rules["maraka"]:
        planet = maraka["planet"]
        if f"worship {planet}" in interpretation_text.lower():
            errors.append(f"DANGER: Recommended worshipping {planet} which is MARAKA")
    
    if errors:
        # Re-run LLM with error corrections OR append warnings
        return interpretation_text, errors
    
    return interpretation_text, []
```

---

## TESTING

After implementing fixes, test with Manish's chart and verify:

1. ✅ Panna (Emerald) recommended as PRIMARY stone
2. ✅ Safed Pukhraj mentioned as currently wearing
3. ✅ Yellow Sapphire (Pukhraj) listed as PROHIBITED with explanation
4. ✅ Moonga (Red Coral) listed as PROHIBITED
5. ✅ Pearl (Moti) listed as PROHIBITED
6. ✅ Ruby listed as UNNECESSARY
7. ✅ Jupiter described as MARAKA (7th+10th), not just "benefic"
8. ✅ Mercury described as LAGNESH and most important planet
9. ✅ Current dasha described as "Maraka mahadasha with Lagnesh protection window"
10. ✅ Mangal dosha interpreted with 6th+11th lordship context
11. ✅ Saturn described as 8th+9th MIXED, not just "discipline"
12. ✅ No generic predictions without chart factor reference

Run the report command after fixing:
python3 -m jyotish.cli report --name "Manish Chaurasia" --dob "13/03/1989" --tob "12:17" --place "Varanasi" --gender Male --llm groq

Compare output against Jyotish_Complete_Reference_Manish.md in the project files.
