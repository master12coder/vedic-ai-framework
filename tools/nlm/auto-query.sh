#!/bin/bash
# Auto-query NLM on every user prompt submission.
# Called by Claude Code UserPromptSubmit hook.
# Reads user prompt from stdin, extracts keywords, queries nlm, injects results.
# Fail-safe: exits silently on any error. Never blocks the user.

set -e

# Bail out if nlm not available
command -v nlm >/dev/null 2>&1 || exit 0

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

# Skip if empty or very short prompt (greetings, yes/no, etc.)
if [ ${#USER_MSG} -lt 15 ]; then
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

# Need at least 2 keywords for a meaningful query
WORD_COUNT=$(echo "$KEYWORDS" | wc -w | tr -d ' ')
if [ "$WORD_COUNT" -lt 2 ]; then
    exit 0
fi

# Query nlm with extracted keywords
NLM_RESULT=$(nlm query "$KEYWORDS" --top-k 2 --quiet 2>/dev/null || echo "")

if [ -z "$NLM_RESULT" ]; then
    exit 0
fi

# Truncate to save tokens (max ~1500 chars / 40 lines)
NLM_SHORT=$(echo "$NLM_RESULT" | head -40)

# Output as JSON systemMessage (Claude Code injects this into context)
python3 -c "
import json
msg = '''[NLM Auto-Query: '$KEYWORDS']
$NLM_SHORT'''
print(json.dumps({'systemMessage': msg}))
" 2>/dev/null || exit 0
