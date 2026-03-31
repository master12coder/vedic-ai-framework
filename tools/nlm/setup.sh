#!/bin/bash
# NLM Setup — one-time setup per project
# Usage: bash tools/nlm/setup.sh

set -e

echo "=== NLM Setup ==="
echo ""

# Detect OS
OS="$(uname -s)"
case "$OS" in
    Darwin|Linux) ;;
    MINGW*|MSYS*|CYGWIN*)
        echo "Windows detected. Please run manually:"
        echo "  pip install rank-bm25 pypdf python-docx"
        echo "  Copy tools/nlm/nlm.py to a directory in your PATH"
        exit 1
        ;;
esac

# Check Python 3
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python 3.10+ first."
    exit 1
fi
echo "Python: $(python3 --version)"

# Install dependencies
echo "Installing Python deps..."
pip3 install rank-bm25 pypdf python-docx --break-system-packages --quiet 2>/dev/null \
    || pip3 install rank-bm25 pypdf python-docx --quiet 2>/dev/null \
    || pip3 install rank-bm25 pypdf python-docx --user --quiet
echo "  Done."

# Make nlm.py executable
chmod +x tools/nlm/nlm.py

# Create symlink
NLM_SRC="$(cd "$(dirname "$0")" && pwd)/nlm.py"
if [ -d "$HOME/.local/bin" ]; then
    ln -sf "$NLM_SRC" "$HOME/.local/bin/nlm"
    echo "Symlink: ~/.local/bin/nlm -> $NLM_SRC"
elif sudo ln -sf "$NLM_SRC" /usr/local/bin/nlm 2>/dev/null; then
    echo "Symlink: /usr/local/bin/nlm -> $NLM_SRC"
else
    mkdir -p "$HOME/bin"
    ln -sf "$NLM_SRC" "$HOME/bin/nlm"
    echo "Symlink: ~/bin/nlm -> $NLM_SRC"
    echo "  (Add ~/bin to PATH if not already)"
fi

# Set git hooks path
git config core.hooksPath .githooks
echo "Git hooks: .githooks/"

# Build initial index — docs only
echo ""
echo "Building initial index..."

# Root-level .md files
for f in *.md; do
    [ -f "$f" ] && nlm add "$f" --force --quiet 2>/dev/null || true
done

# Documentation directories
for dir in docs specs wiki architecture; do
    [ -d "$dir" ] && nlm add "$dir" --force || true
done

echo ""
echo "=== Summary ==="
nlm stats
echo ""
echo "Setup complete. NLM auto-query will run on every Claude Code prompt."
