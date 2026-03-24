# OVERNIGHT BUILD PLAN — Phases 5-7, File Structure & Execution Order

> For context, architecture decisions, and Phases 1-4,
> see `overnight-plan.md`.

---

## PHASE 5: ADDITIONAL PAGES (Hours 8-10)

### Task 5.1: Dasha Deep-dive Page

File: `apps/src/daivai_app/web/templates/dasha.html`

Full vertical timeline with ALL mahadashas.
Current mahadasha expanded to show all antardashas.
Current antardasha has pulsing "अभी" badge.
Golden period highlighted with gold border.
Past events listed if available.

### Task 5.2: Ratna Vidhan Page

File: `apps/src/daivai_app/web/templates/ratna.html`

Three sections:
1. Recommended stones (green) with full details
2. Test with caution (amber)
3. Prohibited stones (red) with danger explanation
4. Free alternatives (mantra, daan, color)
5. Pandit Ji consultation questions
6. Honesty disclaimer about weight formulas

### Tests for Phase 5:
```python
def test_dasha_page_shows_all_mahadashas()
def test_current_antardasha_marked()
def test_golden_period_displayed()
def test_ratna_page_shows_prohibited_stones()
def test_free_alternatives_shown()
```

---

## PHASE 6: DEPLOYMENT CONFIG (Hours 10-11)

### Task 6.1: Oracle Cloud Setup Script

File: `scripts/deploy/setup_oracle.sh`

```bash
#!/bin/bash
# Run on fresh Oracle Cloud ARM VM (Ubuntu 22.04)

# System
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3.12-venv git build-essential

# App
git clone https://github.com/master12coder/daivai.git /opt/jyotish
cd /opt/jyotish
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e "apps/[web]"

# Environment
cat > /opt/jyotish/.env << EOF
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DATABASE_URL=sqlite:///opt/daivai/data/daivai.db
ALLOWED_EMAILS=manish@email.com,panditji@email.com
EOF

# Caddy (reverse proxy + auto SSL)
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/caddy-stable-archive-keyring.gpg] https://dl.cloudsmith.io/public/caddy/stable/deb/debian any-version main" | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy

# Caddyfile
sudo cat > /etc/caddy/Caddyfile << EOF
jyotish.yourdomain.com {
    reverse_proxy localhost:8000
}
EOF

sudo systemctl enable caddy
sudo systemctl start caddy

# Gunicorn systemd service
sudo cat > /etc/systemd/system/jyotish.service << EOF
[Unit]
Description=DaivAI Web App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/jyotish
EnvironmentFile=/opt/jyotish/.env
ExecStart=/opt/jyotish/.venv/bin/gunicorn daivai_app.web.app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable jyotish
sudo systemctl start jyotish

# Daily backup to Google Drive
pip install rclone
# Configure rclone with Google Drive (one-time interactive)
cat > /opt/jyotish/scripts/backup.sh << 'EOF'
#!/bin/bash
cp /opt/jyotish/data/daivai.db /opt/jyotish/data/backup-$(date +%Y%m%d).db
rclone copy /opt/jyotish/data/backup-*.db gdrive:jyotish-backups/
find /opt/jyotish/data/backup-*.db -mtime +7 -delete
EOF
chmod +x /opt/jyotish/scripts/backup.sh

# Cron: backup at 3 AM daily
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/jyotish/scripts/backup.sh") | crontab -

echo "DaivAI deployed. Visit https://jyotish.yourdomain.com"
```

### Task 6.2: Google OAuth Setup Instructions

File: `docs/deployment/google-oauth-setup.md`

Step-by-step with screenshots:
1. Go to console.cloud.google.com
2. Create project "DaivAI"
3. Enable OAuth consent screen
4. Add authorized redirect URI
5. Copy Client ID and Secret to .env
6. Add allowed emails

### Task 6.3: Oracle Firewall Rules

```bash
# Open ports 80 and 443
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

---

## PHASE 7: TELEGRAM DAILY NOTIFICATIONS (Hours 11-12)

### Task 7.1: Telegram Bot Integration

File: `apps/src/daivai_app/telegram/bot.py` (already planned)

The Telegram bot sends daily guidance at 5:30 AM to registered users.
Uses existing `products/daily/` engine.

### Task 7.2: Cron-based Daily Send

```python
# scripts/send_daily.py
# Runs via cron at 5:30 AM
# For each client with Telegram chat_id:
#   1. compute_daily(chart, date.today())
#   2. format_medium(result)
#   3. send via Telegram bot API
```

Cron: `30 5 * * * /opt/jyotish/.venv/bin/python /opt/jyotish/scripts/send_daily.py`

FREE. No WhatsApp Business API cost. Telegram is unlimited.

---

## FILE STRUCTURE (what gets created tonight)

```
apps/src/daivai_app/web/
+-- app.py                      # FastAPI + auth + middleware
+-- routes.py                   # All route handlers
+-- database.py                 # SQLModel tables + session
+-- auth.py                     # Google OAuth helpers
+-- static/
|   +-- tokens.css              # Generated from design-tokens.json
|   +-- components.css          # All j- component styles
|   +-- app.js                  # Minimal JS (form validation, scroll reveal)
|   +-- cities.json             # Indian cities for autocomplete
+-- templates/
    +-- base.html               # Base template (head, tokens, footer)
    +-- login.html              # Google sign-in page
    +-- dashboard.html          # Client list
    +-- input_form.html         # Hindi input form
    +-- overview.html           # Kundli report page
    +-- dasha.html              # Dasha deep-dive
    +-- ratna.html              # Gemstone page
    +-- components/
        +-- macros.html         # All Jinja2 component macros
        +-- diamond_chart.html  # SVG kundli macro

tests/apps/web/
+-- test_app.py                 # App startup, middleware
+-- test_auth.py                # OAuth flow
+-- test_database.py            # CRUD operations
+-- test_routes.py              # All route handlers
+-- test_overview.py            # Page rendering
+-- test_dasha.py               # Dasha page
+-- test_ratna.py               # Gemstone page
+-- conftest.py                 # Test fixtures (test client, mock auth)

scripts/deploy/
+-- setup_oracle.sh             # Full deployment script
+-- backup.sh                   # Daily DB backup
+-- send_daily.py               # Telegram daily cron

docs/deployment/
+-- oracle-setup.md             # Oracle Cloud guide
+-- google-oauth-setup.md       # OAuth configuration
+-- domain-setup.md             # DNS + SSL
```

---

## TEST COMMANDS

```bash
# After each phase, run:
make test                       # All existing 530+ tests still pass
pytest tests/apps/web/ -v       # New web tests pass

# Full validation:
make all                        # lint + typecheck + test + audit
```

---

## ORDER OF EXECUTION FOR CLAUDE CODE

```
Hour  1: Read architecture docs. Set up web/ directory structure.
Hour  2: database.py (SQLModel tables) + test_database.py
Hour  3: auth.py (Google OAuth) + app.py (FastAPI) + test_auth.py
Hour  4: static/tokens.css + static/components.css (from design tokens)
Hour  5: templates/components/macros.html (all Jinja2 macros)
Hour  6: templates/login.html + templates/dashboard.html
Hour  7: routes.py (form + generate + client routes)
Hour  8: templates/input_form.html + test_routes.py
Hour  9: templates/overview.html + templates/components/diamond_chart.html
Hour 10: templates/dasha.html + templates/ratna.html
Hour 11: scripts/deploy/setup_oracle.sh + docs/deployment/
Hour 12: Final make all. Fix any failures. Commit.
```

---

## WHAT MANISH DOES (one-time, 30 minutes total)

### Before overnight run:
1. Share this plan with Claude Code
2. Make sure daivai repo is on GitHub

### After overnight run:
1. Create Oracle Cloud account (cloud.oracle.com) — 10 min
2. Create Google Cloud OAuth credentials — 10 min
3. Buy domain or set up free DuckDNS subdomain — 5 min
4. SSH into Oracle VM, run setup_oracle.sh — 5 min
5. Open browser, see DaivAI running

### After deployment:
1. Share link with Pandit Ji
2. Add Pandit Ji's email to ALLOWED_EMAILS
3. Pandit Ji clicks "Sign in with Google", starts using
4. Family members do the same

---

## WHAT THIS DOES NOT INCLUDE (Phase 2, later)

- Apple Sign-In (needs $99/year Apple Developer account)
- WhatsApp notifications (needs Meta Business API, costs money)
- PWA push notifications (needs service worker, Phase 2)
- Offline mode (needs service worker cache, Phase 2)
- Multi-language (currently Hindi-English only)
- Payment/subscription (free tool for now)
- Admin panel (Manish manages via SSH/DB for now)
- Image export for WhatsApp sharing (PIL generation, Phase 2)
- D9 Navamsha page (same component, different data — easy to add)
- Compatibility/Muhurta pages (engine exists, just need templates)
