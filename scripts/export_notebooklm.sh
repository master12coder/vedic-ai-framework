#!/usr/bin/env bash
# Export DaivAI knowledge base for Google NotebookLM.
# Creates 15 bundled .md files in exports/notebooklm/
# Usage: bash scripts/export_notebooklm.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/exports/notebooklm"
ENG="$ROOT/engine/src/daivai_engine"
KNOW="$ENG/knowledge"
SCRIP="$ENG/scriptures"
MODELS="$ENG/models"
COMPUTE="$ENG/compute"
PROMPTS="$ROOT/products/src/daivai_products/interpret/prompts"
DOCS="$ROOT/docs"

rm -rf "$OUT"
mkdir -p "$OUT"

bundle() {
    local outfile="$1"
    shift
    > "$outfile"
    for f in "$@"; do
        if [ -f "$f" ]; then
            local rel="${f#$ROOT/}"
            echo "# === FILE: $rel ===" >> "$outfile"
            echo "" >> "$outfile"
            cat "$f" >> "$outfile"
            echo "" >> "$outfile"
            echo "" >> "$outfile"
        fi
    done
}

echo "Exporting DaivAI knowledge base to $OUT ..."

# 01: Architecture & Rules
bundle "$OUT/01_architecture_and_rules.md" \
    "$ROOT/CLAUDE.md" \
    "$DOCS/architecture/overview.md" \
    "$DOCS/architecture/decisions.md" \
    "$DOCS/design/project-context.md" \
    "$DOCS/development/style-guide.md"

# 02: Safety & Vedic Guide
bundle "$OUT/02_safety_and_vedic_guide.md" \
    "$DOCS/vedic/gemstone-safety.md" \
    "$DOCS/vedic/interpretation-safety.md" \
    "$DOCS/vedic/lordship-guide.md"

# 03: Product Specs
bundle "$OUT/03_product_specs.md" \
    "$DOCS/products/kundali.md" \
    "$DOCS/products/remedies.md" \
    "$DOCS/products/daily.md" \
    "$DOCS/products/predictions.md" \
    "$DOCS/products/pandit.md" \
    "$DOCS/products/muhurta.md" \
    "$DOCS/products/matching.md"

# 04: Yoga Definitions (large — own source)
bundle "$OUT/04_yoga_definitions.md" \
    "$KNOW/yoga_definitions.yaml"

# 05: Lordship & Gemstone Rules
bundle "$OUT/05_lordship_and_gemstone_rules.md" \
    "$KNOW/lordship_rules.yaml" \
    "$KNOW/gem_therapy_rules.yaml" \
    "$KNOW/gem_therapy_logic.yaml" \
    "$KNOW/gemstone_logic.yaml"

# 06: Nakshatra & Signs
bundle "$OUT/06_nakshatra_and_signs.md" \
    "$KNOW/nakshatra_data.yaml" \
    "$KNOW/sign_properties.yaml" \
    "$KNOW/dignity.yaml" \
    "$KNOW/house_significations.yaml" \
    "$KNOW/aspects.yaml" \
    "$KNOW/combustion.yaml" \
    "$KNOW/pushkara_data.yaml" \
    "$KNOW/mrityu_bhaga.yaml"

# 07: Transit & Dasha Rules
bundle "$OUT/07_transit_and_dasha_rules.md" \
    "$KNOW/gochara_rules.yaml" \
    "$KNOW/transit_rules.yaml" \
    "$KNOW/vimshottari_dasha.yaml" \
    "$KNOW/kalachakra_dasha_data.yaml" \
    "$KNOW/ashtakavarga_tables.yaml" \
    "$KNOW/shadbala_reference.yaml" \
    "$KNOW/vimshopaka_weights.yaml" \
    "$KNOW/ayanamsha_reference.yaml"

# 08: Remedies Knowledge
bundle "$OUT/08_remedies_knowledge.md" \
    "$KNOW/mantra_rules.yaml" \
    "$KNOW/remedy_rules.yaml" \
    "$KNOW/vastu_rules.yaml" \
    "$KNOW/yantra_data.yaml" \
    "$KNOW/weekly_routine.yaml" \
    "$KNOW/mantras.yaml" \
    "$KNOW/direction_mapping.yaml"

# 09: Specialized Knowledge
bundle "$OUT/09_specialized_knowledge.md" \
    "$KNOW/medical_rules.yaml" \
    "$KNOW/mundane_rules.yaml" \
    "$KNOW/numerology_rules.yaml" \
    "$KNOW/pancha_pakshi_rules.yaml" \
    "$KNOW/namakarana_rules.yaml" \
    "$KNOW/saham_definitions.yaml" \
    "$KNOW/dosha_definitions.yaml" \
    "$KNOW/computation_sources.yaml" \
    "$KNOW/avakhada_data.yaml" \
    "$KNOW/ashtamangala_prashna.yaml" \
    "$KNOW/porutham_data.yaml" \
    "$KNOW/shashtyamsha_data.yaml" \
    "$KNOW/varga_significations.yaml" \
    "$KNOW/special_lagna_significations.yaml" \
    "$KNOW/upagraha_significations.yaml"

# 10: BPHS Scriptures (all chapters)
bundle "$OUT/10_bphs_scriptures.md" \
    "$SCRIP/bphs/chapter_03_planet_nature.yaml" \
    "$SCRIP/bphs/chapter_05_houses.yaml" \
    "$SCRIP/bphs/chapter_07_friendships.yaml" \
    "$SCRIP/bphs/chapter_10_yogas.yaml" \
    "$SCRIP/bphs/chapter_11_planet_house_effects.yaml" \
    "$SCRIP/bphs/chapter_13_house_lords.yaml" \
    "$SCRIP/bphs/chapter_15_raja_yoga.yaml" \
    "$SCRIP/bphs/chapter_16_dhana_yoga.yaml" \
    "$SCRIP/bphs/chapter_19_marriage.yaml" \
    "$SCRIP/bphs/chapter_20_bhava_effects.yaml" \
    "$SCRIP/bphs/chapter_25_dasha_effects.yaml" \
    "$SCRIP/bphs/chapter_31_argala.yaml" \
    "$SCRIP/bphs/chapter_34_vimshottari_effects.yaml" \
    "$SCRIP/bphs/chapter_36_dasha_phala.yaml" \
    "$SCRIP/bphs/chapter_47_ashtakavarga.yaml" \
    "$SCRIP/bphs/chapter_80_gemstones.yaml" \
    "$SCRIP/bphs/chapter_81_muhurta.yaml" \
    "$SCRIP/bphs/chapter_85_remedies.yaml" \
    "$SCRIP/bphs/chapter_93_remedies.yaml"

# 11: Lal Kitab Scripture
bundle "$OUT/11_lal_kitab_scripture.md" \
    "$SCRIP/lal_kitab/remedies.yaml"

# 12: Model Definitions (all .py in models/)
model_files=()
while IFS= read -r f; do model_files+=("$f"); done < <(find "$MODELS" -name '*.py' -not -name '__pycache__' | sort)
bundle "$OUT/12_model_definitions.md" "${model_files[@]}"

# 13: Prompt Templates
prompt_files=()
while IFS= read -r f; do prompt_files+=("$f"); done < <(find "$PROMPTS" -name '*.md' | sort)
bundle "$OUT/13_prompt_templates.md" "${prompt_files[@]}"

# 14: Engine Module Index (docstrings only)
{
    echo "# DaivAI Engine Module Index"
    echo ""
    echo "First 5 lines (docstring) of each compute module."
    echo "Total: $(find "$COMPUTE" -maxdepth 1 -name '*.py' ! -name '__init__.py' | wc -l | tr -d ' ') modules"
    echo ""
    for f in $(find "$COMPUTE" -maxdepth 1 -name '*.py' ! -name '__init__.py' | sort); do
        rel="${f#$ROOT/}"
        echo "## $rel"
        head -6 "$f"
        echo ""
    done
} > "$OUT/14_engine_module_index.md"

# 15: Project Plan
bundle "$OUT/15_project_plan.md" \
    "$ROOT/.claude/plans/iridescent-exploring-fern.md"

# Summary
echo ""
echo "=== Export Complete ==="
echo ""
echo "Files created in: $OUT"
echo ""
ls -lhS "$OUT"
echo ""
total_lines=$(cat "$OUT"/*.md | wc -l | tr -d ' ')
total_size=$(du -sh "$OUT" | cut -f1)
echo "Total: $total_lines lines, $total_size"
echo ""
echo "=== NotebookLM Upload Instructions ==="
echo ""
echo "1. Go to https://notebooklm.google.com"
echo "2. Create a new notebook"
echo "3. Click 'Add source' → 'Upload'"
echo "4. Drag all 15 .md files from: $OUT"
echo "5. Wait for processing (~1 min)"
echo ""
echo "Recommended notebooks:"
echo "  Notebook 1: Upload files 01-03 (architecture, safety, products)"
echo "  Notebook 2: Upload files 04-11 (all Vedic knowledge + scriptures)"
echo "  Notebook 3: Upload files 12-15 (models, prompts, module index, plan)"
echo ""
echo "Or upload ALL 15 into ONE notebook (under the 50-source limit)."
