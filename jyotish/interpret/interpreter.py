"""Main interpretation orchestrator — combines chart data with LLM prompts.

Loads lordship rules, gemstone logic, scripture citations, and Pandit Ji
corrections BEFORE every LLM call so the model has full chart-specific
knowledge context.  Also validates LLM output for dangerous gemstone errors.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Template

from jyotish.compute.chart import ChartData
from jyotish.compute.dasha import compute_mahadashas, find_current_dasha
from jyotish.compute.yoga import detect_all_yogas
from jyotish.compute.dosha import detect_all_doshas
from jyotish.compute.strength import compute_planet_strengths
from jyotish.compute.divisional import compute_navamsha, get_vargottam_planets
from jyotish.interpret.llm_backend import LLMBackend, get_backend
from jyotish.scriptures import scripture_db
from jyotish.learn.corrections import PanditCorrectionStore
from jyotish.utils.logging_config import get_logger

logger = get_logger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
_KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"

# ---------------------------------------------------------------------------
# YAML / knowledge helpers
# ---------------------------------------------------------------------------

_lordship_cache: dict[str, Any] | None = None
_gemstone_cache: dict[str, Any] | None = None


def _load_yaml(filename: str) -> dict[str, Any]:
    """Load a YAML knowledge file."""
    path = _KNOWLEDGE_DIR / filename
    if not path.exists():
        logger.warning("Knowledge file not found: %s", path)
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _get_lordship_data() -> dict[str, Any]:
    """Load and cache lordship rules."""
    global _lordship_cache
    if _lordship_cache is None:
        _lordship_cache = _load_yaml("lordship_rules.yaml")
    return _lordship_cache


def _get_gemstone_data() -> dict[str, Any]:
    """Load and cache gemstone logic."""
    global _gemstone_cache
    if _gemstone_cache is None:
        _gemstone_cache = _load_yaml("gemstone_logic.yaml")
    return _gemstone_cache


def _build_lordship_context(lagna_sign: str) -> dict[str, Any]:
    """Build lordship context for this specific lagna from YAML rules.

    Returns a dict with keys: sign_lord, yogakaraka, functional_benefics,
    functional_malefics, maraka, house_lords, recommended_stones,
    prohibited_stones, test_stones, gemstone_recommendations.
    """
    lordship_data = _get_lordship_data()
    lagna_key = lagna_sign.lower()
    lagna_rules = lordship_data.get("lagnas", {}).get(lagna_key, {})

    if not lagna_rules:
        logger.warning("No lordship rules for lagna: %s", lagna_sign)
        return {}

    # Build recommended / prohibited / test stone lists
    gem_recs = lagna_rules.get("gemstone_recommendations", {})
    recommended_stones: list[dict[str, str]] = []
    prohibited_stones: list[dict[str, str]] = []
    test_stones: list[dict[str, str]] = []

    for planet, info in gem_recs.items():
        rec = info.get("recommendation", "neutral")
        stone = info.get("gemstone", "Unknown")
        reasoning = info.get("reasoning", "").strip()
        entry = {"planet": planet, "stone": stone, "reasoning": reasoning}
        if rec == "wear":
            recommended_stones.append(entry)
        elif rec == "avoid":
            prohibited_stones.append(entry)
        elif rec == "test":
            test_stones.append(entry)

    # Format maraka entries with readable house strings
    maraka_raw = lagna_rules.get("maraka", [])
    maraka_formatted: list[dict[str, Any]] = []
    for m in maraka_raw:
        houses = m.get("houses", [])
        house_labels = {
            2: "2nd (maraka sthana)",
            7: "7th (maraka sthana)",
        }
        house_str = " + ".join(
            house_labels.get(h, f"{h}th") for h in houses
        )
        maraka_formatted.append({
            "planet": m.get("planet", ""),
            "houses": houses,
            "house_str": house_str,
            "reasoning": m.get("reasoning", "").strip(),
        })

    return {
        "sign_lord": lagna_rules.get("sign_lord", ""),
        "yogakaraka": lagna_rules.get("yogakaraka", {}),
        "functional_benefics": lagna_rules.get("functional_benefics", []),
        "functional_malefics": lagna_rules.get("functional_malefics", []),
        "maraka": maraka_formatted,
        "house_lords": lagna_rules.get("house_lords", {}),
        "gemstone_recommendations": gem_recs,
        "recommended_stones": recommended_stones,
        "prohibited_stones": prohibited_stones,
        "test_stones": test_stones,
    }


def _build_gemstone_context() -> dict[str, Any]:
    """Load gemstone_logic.yaml context for prompt injection."""
    data = _get_gemstone_data()
    return {
        "gemstone_data": data.get("gemstones", {}),
        "contraindications": data.get("contraindications", []),
        "decision_framework": data.get("decision_framework", {}),
        "planetary_friendships": data.get("planetary_friendships", {}),
    }


def _build_scripture_context(chart: ChartData) -> list[str]:
    """Load relevant scripture citations for each planet in this chart."""
    citations: list[str] = []
    for planet_name, planet in chart.planets.items():
        refs = scripture_db.query_by_planet(planet_name, planet.house)
        for ref in refs[:2]:  # Top 2 per planet to control prompt size
            citations.append(scripture_db.get_citation(ref))
    return citations


# ---------------------------------------------------------------------------
# Prompt loading / rendering
# ---------------------------------------------------------------------------


def _load_prompt(template_name: str) -> str:
    """Load a prompt template from the prompts directory."""
    path = PROMPTS_DIR / template_name
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text()


def _render_prompt(template_name: str, context: dict[str, Any]) -> str:
    """Load and render a Jinja2 prompt template."""
    raw = _load_prompt(template_name)
    template = Template(raw)
    return template.render(**context)


# ---------------------------------------------------------------------------
# Chart context builder
# ---------------------------------------------------------------------------


def _build_chart_context(chart: ChartData) -> dict[str, Any]:
    """Build a context dictionary from chart data for prompt rendering.

    Includes:
    - All computed chart data (planets, yogas, doshas, strengths, dasha)
    - Lordship rules for THIS lagna (benefics, malefics, maraka, gemstones)
    - Gemstone logic with contraindications
    - Scripture citations for planets in their houses
    - Pandit Ji learned corrections
    """
    yogas = detect_all_yogas(chart)
    doshas = detect_all_doshas(chart)
    strengths = compute_planet_strengths(chart)
    vargottam = get_vargottam_planets(chart)
    mahadashas = compute_mahadashas(chart)

    try:
        md, ad, pd = find_current_dasha(chart)
        current_dasha = {
            "mahadasha": md.lord,
            "antardasha": ad.lord,
            "pratyantardasha": pd.lord,
            "md_start": md.start.strftime("%d/%m/%Y"),
            "md_end": md.end.strftime("%d/%m/%Y"),
            "ad_start": ad.start.strftime("%d/%m/%Y"),
            "ad_end": ad.end.strftime("%d/%m/%Y"),
        }
    except Exception:
        current_dasha = {"mahadasha": "Unknown", "antardasha": "Unknown", "pratyantardasha": "Unknown"}

    planet_summary = []
    for p in chart.planets.values():
        planet_summary.append({
            "name": p.name,
            "sign": p.sign,
            "sign_en": p.sign_en,
            "house": p.house,
            "degree": f"{p.degree_in_sign:.1f}\u00b0",
            "nakshatra": p.nakshatra,
            "pada": p.pada,
            "dignity": p.dignity,
            "retrograde": p.is_retrograde,
            "combust": p.is_combust,
            "sign_lord": p.sign_lord,
        })

    yoga_summary = [
        {"name": y.name, "name_hindi": y.name_hindi, "description": y.description, "effect": y.effect}
        for y in yogas if y.is_present
    ]

    dosha_summary = [
        {"name": d.name, "name_hindi": d.name_hindi, "severity": d.severity, "description": d.description}
        for d in doshas if d.is_present
    ]

    strength_summary = [
        {"planet": s.planet, "rank": s.rank, "strength": s.total_relative, "is_strong": s.is_strong}
        for s in strengths
    ]

    # ------------------------------------------------------------------
    # Knowledge context: lordship, gemstones, scripture, pandit rules
    # ------------------------------------------------------------------
    lordship_ctx = _build_lordship_context(chart.lagna_sign)
    gemstone_ctx = _build_gemstone_context()
    scripture_citations = _build_scripture_context(chart)

    try:
        pandit_store = PanditCorrectionStore()
        pandit_teachings = pandit_store.get_prompt_additions(lagna=chart.lagna_sign)
    except Exception:
        pandit_teachings = ""

    # Determine if current Mahadasha lord is benefic for this lagna
    md_lord = current_dasha.get("mahadasha", "")
    benefic_names = [b.get("planet", "") for b in lordship_ctx.get("functional_benefics", [])]
    malefic_names = [m.get("planet", "") for m in lordship_ctx.get("functional_malefics", [])]
    maraka_names = [m.get("planet", "") for m in lordship_ctx.get("maraka", [])]
    is_md_lord_benefic = md_lord in benefic_names
    is_md_lord_maraka = md_lord in maraka_names

    # Lagnesh info
    lagnesh = lordship_ctx.get("sign_lord", "")
    lagnesh_stone = ""
    yogakaraka_info = lordship_ctx.get("yogakaraka", {})
    yogakaraka_planet = yogakaraka_info.get("planet", "") if isinstance(yogakaraka_info, dict) else ""
    yogakaraka_stone = ""

    gem_recs = lordship_ctx.get("gemstone_recommendations", {})
    if lagnesh and lagnesh in gem_recs:
        lagnesh_stone = gem_recs[lagnesh].get("gemstone", "")
    if yogakaraka_planet and yogakaraka_planet in gem_recs:
        yogakaraka_stone = gem_recs[yogakaraka_planet].get("gemstone", "")

    # Friend / enemy groups from gemstone_logic.yaml
    friends_map = gemstone_ctx.get("planetary_friendships", {}).get("friends", {})
    enemies_map = gemstone_ctx.get("planetary_friendships", {}).get("enemies", {})

    # Build friend group around lagnesh
    friend_group_planets: set[str] = set()
    if lagnesh:
        friend_group_planets.add(lagnesh)
        for friend in friends_map.get(lagnesh, []):
            if friend in benefic_names:
                friend_group_planets.add(friend)

    gemstone_data = gemstone_ctx.get("gemstone_data", {})
    friend_group_str = " + ".join(
        f"{p} ({gemstone_data.get(p, {}).get('primary', {}).get('name_en', '?')})"
        for p in sorted(friend_group_planets)
    )

    enemy_group_planets = set(malefic_names + maraka_names) - friend_group_planets
    enemy_group_str = " + ".join(
        f"{p} ({gemstone_data.get(p, {}).get('primary', {}).get('name_en', '?')})"
        for p in sorted(enemy_group_planets)
    )

    return {
        # --- Existing chart data ---
        "name": chart.name,
        "dob": chart.dob,
        "tob": chart.tob,
        "place": chart.place,
        "gender": chart.gender,
        "lagna": chart.lagna_sign,
        "lagna_en": chart.lagna_sign_en,
        "lagna_hi": chart.lagna_sign_hi,
        "lagna_degree": f"{chart.lagna_degree:.1f}\u00b0",
        "planets": planet_summary,
        "yogas": yoga_summary,
        "doshas": dosha_summary,
        "strengths": strength_summary,
        "vargottam_planets": vargottam,
        "current_dasha": current_dasha,
        "mahadashas": [
            {"lord": md.lord, "start": md.start.strftime("%d/%m/%Y"), "end": md.end.strftime("%d/%m/%Y")}
            for md in mahadashas
        ],
        # --- Lordship context ---
        "lordship": lordship_ctx,
        "yogakaraka": yogakaraka_info,
        "yogakaraka_planet": yogakaraka_planet,
        "yogakaraka_stone": yogakaraka_stone,
        "functional_benefics": lordship_ctx.get("functional_benefics", []),
        "functional_malefics": lordship_ctx.get("functional_malefics", []),
        "maraka_planets": lordship_ctx.get("maraka", []),
        "house_lords": lordship_ctx.get("house_lords", {}),
        "recommended_stones": lordship_ctx.get("recommended_stones", []),
        "prohibited_stones": lordship_ctx.get("prohibited_stones", []),
        "test_stones": lordship_ctx.get("test_stones", []),
        "gemstone_recs": gem_recs,
        # --- Gemstone logic ---
        "contraindications": gemstone_ctx.get("contraindications", []),
        "friend_group": friend_group_str,
        "enemy_group": enemy_group_str,
        # --- Lagnesh / dasha benefic info ---
        "lagnesh": lagnesh,
        "lagnesh_stone": lagnesh_stone,
        "is_md_lord_benefic": is_md_lord_benefic,
        "is_md_lord_maraka": is_md_lord_maraka,
        # --- Scripture & Pandit Ji ---
        "scripture_citations": scripture_citations,
        "pandit_teachings": pandit_teachings,
    }


# ---------------------------------------------------------------------------
# Post-generation safety validation (Fix 7)
# ---------------------------------------------------------------------------

# Regex-safe words that indicate a POSITIVE recommendation context
_RECOMMEND_WORDS = re.compile(
    r"\b(recommend|wear|beneficial|auspicious|strengthen|suitable|advised|should wear|must wear)\b",
    re.IGNORECASE,
)
# Words that indicate the text is already cautioning AGAINST the stone
_AVOID_WORDS = re.compile(
    r"\b(avoid|never|prohibited|harmful|dangerous|do not|don\'t|maraka|malefic|contraindicated)\b",
    re.IGNORECASE,
)


def _is_recommended_context(text: str, stone_name: str) -> bool:
    """Check if a stone name appears in a recommendation context.

    Returns True if the stone appears near 'recommend/wear' words
    WITHOUT nearby 'avoid/never/prohibited' words.
    """
    stone_lower = stone_name.lower()
    text_lower = text.lower()

    # Find all occurrences of the stone name
    idx = 0
    while True:
        pos = text_lower.find(stone_lower, idx)
        if pos == -1:
            break
        # Look at a window around the mention
        window_start = max(0, pos - 150)
        window_end = min(len(text_lower), pos + len(stone_lower) + 150)
        window = text_lower[window_start:window_end]

        has_recommend = bool(_RECOMMEND_WORDS.search(window))
        has_avoid = bool(_AVOID_WORDS.search(window))

        # If recommended without avoidance qualifier, flag it
        if has_recommend and not has_avoid:
            return True

        idx = pos + 1

    return False


def validate_interpretation(
    text: str,
    lagna_sign: str,
    lordship_ctx: dict[str, Any],
) -> tuple[str, list[str]]:
    """Check LLM output for dangerous errors before showing to user.

    Returns:
        (possibly_amended_text, list_of_error_strings)
    """
    errors: list[str] = []

    prohibited = lordship_ctx.get("prohibited_stones", [])
    maraka_list = lordship_ctx.get("maraka", [])

    # Check 1: Did LLM recommend a prohibited stone?
    for entry in prohibited:
        stone = entry.get("stone", "")
        planet = entry.get("planet", "")
        # Check both the full stone string and common names within it
        stone_names = [stone]
        # Extract individual names e.g. "Yellow Sapphire (Pukhraj)" -> ["Yellow Sapphire", "Pukhraj"]
        if "(" in stone:
            parts = stone.replace(")", "").split("(")
            stone_names = [p.strip() for p in parts if p.strip()]

        for sn in stone_names:
            if sn.lower() in text.lower() and _is_recommended_context(text, sn):
                errors.append(
                    f"DANGER: {stone} ({planet}'s stone) appears to be RECOMMENDED "
                    f"but is PROHIBITED for {lagna_sign} lagna. "
                    f"{planet} is a functional malefic/maraka."
                )
                break

    # Check 2: Did LLM call a maraka planet "benefic" or "auspicious"?
    text_lower = text.lower()
    for m in maraka_list:
        planet = m.get("planet", "")
        if not planet:
            continue
        p_lower = planet.lower()
        bad_patterns = [
            f"{p_lower} is benefic",
            f"{p_lower} is auspicious",
            f"{p_lower} is a benefic",
            f"{p_lower} as benefic",
            f"benefic {p_lower}",
        ]
        for pat in bad_patterns:
            if pat in text_lower:
                houses = m.get("house_str", "")
                errors.append(
                    f"ERROR: {planet} called benefic/auspicious but is MARAKA "
                    f"({houses}) for {lagna_sign} lagna."
                )
                break

    # Check 3: Did LLM recommend worshipping a maraka planet?
    for m in maraka_list:
        planet = m.get("planet", "")
        if not planet:
            continue
        p_lower = planet.lower()
        worship_patterns = [
            f"worship {p_lower}",
            f"pray to {p_lower}",
            f"strengthen {p_lower}",
            f"propitiate {p_lower}",
        ]
        for pat in worship_patterns:
            if pat in text_lower:
                errors.append(
                    f"WARNING: Recommended strengthening/worshipping {planet} "
                    f"which is MARAKA for {lagna_sign} lagna. "
                    f"Propitiating a maraka can activate harmful effects."
                )
                break

    if errors:
        warning_block = (
            "\n\n---\n"
            "## \u26a0\ufe0f SAFETY VALIDATION WARNINGS\n"
            "The following issues were detected by the Parashari rule engine:\n\n"
        )
        for err in errors:
            warning_block += f"- {err}\n"
        warning_block += (
            "\nPlease consult the lordship rules for your lagna before "
            "following any flagged recommendation above.\n"
        )
        return text + warning_block, errors

    return text, []


# ---------------------------------------------------------------------------
# Public interpretation API
# ---------------------------------------------------------------------------


def interpret_chart(
    chart: ChartData,
    backend: LLMBackend | None = None,
    sections: list[str] | None = None,
) -> dict[str, str]:
    """Generate full chart interpretation using LLM.

    Loads lordship rules, gemstone logic, scripture citations, and Pandit Ji
    corrections before every LLM call.  Validates output afterwards.

    Args:
        chart: Computed chart data
        backend: LLM backend to use (default from config)
        sections: Specific sections to interpret (default: all)

    Returns:
        Dictionary of section_name -> interpreted text
    """
    if backend is None:
        backend = get_backend()

    context = _build_chart_context(chart)
    lordship_ctx = context.get("lordship", {})
    system_prompt = _render_prompt("system_prompt.md", context)

    all_sections = [
        "chart_overview",
        "career_analysis",
        "financial_analysis",
        "health_analysis",
        "relationship_analysis",
        "spiritual_profile",
        "remedy_generation",
    ]

    if sections:
        all_sections = [s for s in sections if s in all_sections]

    results: dict[str, str] = {}

    for section in all_sections:
        template_name = f"{section}.md"
        try:
            user_prompt = _render_prompt(template_name, context)
            response = backend.generate(system_prompt, user_prompt)

            # Post-generation safety validation
            validated, validation_errors = validate_interpretation(
                response, chart.lagna_sign, lordship_ctx,
            )
            if validation_errors:
                logger.warning(
                    "Validation errors in %s for %s lagna: %s",
                    section, chart.lagna_sign, validation_errors,
                )
            results[section] = validated

        except FileNotFoundError:
            results[section] = f"[Template {template_name} not found]"
        except Exception as e:
            results[section] = f"[Error generating {section}: {e}]"

    return results


def interpret_with_events(
    chart: ChartData,
    events: list[dict[str, str]],
    backend: LLMBackend | None = None,
) -> str:
    """Interpret chart with life event validation.

    Args:
        chart: Computed chart data
        events: List of {"date": "DD/MM/YYYY", "event": "description"}
        backend: LLM backend
    """
    if backend is None:
        backend = get_backend()

    context = _build_chart_context(chart)
    context["life_events"] = events

    system_prompt = _render_prompt("system_prompt.md", context)
    user_prompt = _render_prompt("life_event_validation.md", context)

    return backend.generate(system_prompt, user_prompt)


def get_daily_suggestion(
    chart: ChartData,
    backend: LLMBackend | None = None,
) -> str:
    """Get daily suggestion based on transits."""
    if backend is None:
        backend = get_backend()

    from jyotish.compute.transit import compute_transits
    transit_data = compute_transits(chart)

    context = _build_chart_context(chart)
    context["transits"] = [
        {"name": t.name, "sign": t.sign, "house": t.natal_house_activated, "retrograde": t.is_retrograde}
        for t in transit_data.transits
    ]
    context["major_transits"] = transit_data.major_transits
    context["transit_date"] = transit_data.target_date

    system_prompt = _render_prompt("system_prompt.md", context)
    user_prompt = _render_prompt("daily_suggestion.md", context)

    return backend.generate(system_prompt, user_prompt)
