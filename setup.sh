#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  setup.sh  —  Run ONCE after git clone on any new machine
#  Does everything: installs nlm, hooks, initial index
#
#  Usage:
#    git clone <your-repo>
#    cd <repo>
#    bash setup.sh
# ─────────────────────────────────────────────────────────────

set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SkillCat Dev Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── 1. Detect OS ────────────────────────────────────────────
OS="linux"
[[ "$OSTYPE" == "darwin"* ]] && OS="mac"
[[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]] && OS="windows"
echo -e "${YELLOW}[1/5] Detected OS: $OS${NC}"

# ── 2. Install Python deps ──────────────────────────────────
echo -e "${YELLOW}[2/5] Installing nlm dependencies...${NC}"
if command -v pip3 &>/dev/null; then
    pip3 install rank-bm25 pypdf python-docx --quiet --break-system-packages 2>/dev/null \
    || pip3 install rank-bm25 pypdf python-docx --quiet
elif command -v pip &>/dev/null; then
    pip install rank-bm25 pypdf python-docx --quiet
else
    echo -e "${RED}❌ Python pip not found. Install Python 3 first.${NC}"
    exit 1
fi
echo -e "${GREEN}   ✓ dependencies installed${NC}"

# ── 3. Install nlm CLI globally ─────────────────────────────
echo -e "${YELLOW}[3/5] Installing nlm CLI...${NC}"

if [ "$OS" == "windows" ]; then
    # Windows — copy to a scripts folder, add to PATH via profile
    NLM_DIR="$HOME/.nlm_bin"
    mkdir -p "$NLM_DIR"
    cp "tools/nlm/nlm.py" "$NLM_DIR/nlm.py"
    # Create a batch wrapper
    cat > "$NLM_DIR/nlm.bat" << 'BAT'
@echo off
python "%~dp0nlm.py" %*
BAT
    # Add to PATH if not already there
    case ":$PATH:" in
        *":$NLM_DIR:"*) ;;
        *)
            echo "export PATH=\"$NLM_DIR:\$PATH\"" >> "$HOME/.bashrc"
            echo "export PATH=\"$NLM_DIR:\$PATH\"" >> "$HOME/.bash_profile" 2>/dev/null || true
            export PATH="$NLM_DIR:$PATH"
            ;;
    esac
    echo -e "${GREEN}   ✓ nlm installed at $NLM_DIR${NC}"
else
    # Mac / Linux
    sudo cp "tools/nlm/nlm.py" /usr/local/bin/nlm
    sudo chmod +x /usr/local/bin/nlm
    echo -e "${GREEN}   ✓ nlm installed at /usr/local/bin/nlm${NC}"
fi

# ── 4. Point git to committed hooks ────────────────────────
echo -e "${YELLOW}[4/5] Configuring git hooks (.githooks/)...${NC}"
git config core.hooksPath .githooks
chmod +x .githooks/* 2>/dev/null || true
echo -e "${GREEN}   ✓ git will now use .githooks/ from repo${NC}"

# ── 5. Initial nlm index ────────────────────────────────────
echo -e "${YELLOW}[5/5] Building initial NLM index...${NC}"
for dir in docs specs spec .claude; do
    [ -d "$dir" ] && nlm add "$dir" 2>/dev/null && echo "  ✓ indexed $dir/"
done
# Index root-level markdown files
find . -maxdepth 1 -name "*.md" | while read -r f; do
    nlm add "$f" 2>/dev/null && echo "  ✓ indexed $f"
done

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Setup complete! Everything ready.${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Git hooks    : auto-sync on every commit/push ✅"
echo "  NLM CLI      : $(nlm --version 2>/dev/null || echo 'ready')"
echo "  Index        : $(nlm stats 2>/dev/null | grep Chunks || echo 'empty — add your docs')"
echo ""
echo "  Next: nlm add /path/to/lms_functional_spec.pdf"
echo "        nlm add /path/to/nrc_architecture.md"
echo ""
