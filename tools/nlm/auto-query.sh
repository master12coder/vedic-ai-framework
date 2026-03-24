#!/bin/bash
# Auto-query NLM on every user prompt submission.
# Called by Claude Code UserPromptSubmit hook.
# Reads user prompt from stdin, extracts keywords, queries nlm, injects results.

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PHASE_FILE="$PROJECT_DIR/docs/architecture/phase-status.md"

# Read user prompt from stdin (JSON: {"user_message": "..."})
INPUT=$(cat)
USER_MSG=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('user_message', data.get('message', '')))
except:
    print('')
" 2>/dev/null || echo "")

# Skip if empty or very short prompt (greetings, etc.)
if [ ${#USER_MSG} -lt 10 ]; then
    exit 0
fi

# Extract keywords (remove common words, take first 8 meaningful words)
KEYWORDS=$(echo "$USER_MSG" | python3 -c "
import sys
stop = {'the','a','an','is','are','was','were','be','been','being','have','has','had',
        'do','does','did','will','would','shall','should','may','might','must','can',
        'could','i','you','we','they','he','she','it','my','your','our','their','this',
        'that','these','those','what','which','who','whom','when','where','why','how',
        'not','no','yes','and','or','but','if','then','else','for','to','from','with',
        'in','on','at','by','of','into','about','as','all','each','every','both','few',
        'more','most','other','some','such','than','too','very','just','also','now',
        'here','there','please','want','need','make','let','me','its','so','up','out',
        'like','get','go','know','see','look','think','take','come','give','tell','use',
        'done','start','check','review','before','after','next','phase','layer'}
words = sys.stdin.read().lower().split()
keywords = [w for w in words if w not in stop and len(w) > 2][:8]
print(' '.join(keywords))
" 2>/dev/null || echo "")

if [ -z "$KEYWORDS" ]; then
    exit 0
fi

# Query nlm with extracted keywords
NLM_RESULT=$(nlm query "$KEYWORDS" --top-k 2 --quiet 2>/dev/null || echo "")

# Get current phase from phase-status.md
PHASE_LINE=""
if [ -f "$PHASE_FILE" ]; then
    PHASE_LINE=$(grep "NOT STARTED\|PARTIAL\|DONE" "$PHASE_FILE" | head -5 2>/dev/null || echo "")
fi

# Build system message
if [ -n "$NLM_RESULT" ] || [ -n "$PHASE_LINE" ]; then
    # Truncate nlm result to save tokens (max 1500 chars)
    NLM_SHORT=$(echo "$NLM_RESULT" | head -40)

    MSG="[NLM Auto-Query: '$KEYWORDS']"
    if [ -n "$NLM_SHORT" ]; then
        MSG="$MSG\n$NLM_SHORT"
    fi
    if [ -n "$PHASE_LINE" ]; then
        MSG="$MSG\n\n[Phase Status]\n$PHASE_LINE"
    fi

    # Output as JSON systemMessage (Claude Code injects this into context)
    python3 -c "
import json, sys
msg = '''$MSG'''
print(json.dumps({'systemMessage': msg}))
" 2>/dev/null
fi
