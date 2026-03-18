# OVERNIGHT BUILD PLAN — Jyotish AI Web App
## 10-12 Hour Claude Code Execution Plan
## Date: March 19, 2026

---

## CONTEXT FOR CLAUDE CODE

Read these files FIRST (in order):
1. `docs/architecture/OVERVIEW.md` — 3-package architecture
2. `docs/architecture/DECISIONS.md` — ADRs
3. `CLAUDE.md` — Hard rules
4. This file — What to build tonight

The web app lives in `apps/src/jyotish_app/web/`.
It uses FastAPI (already in the stack) + Jinja2 templates + our design tokens.
It is ONE MORE DELIVERY CHANNEL — like CLI and Telegram.
It calls products/ which calls engine/. It NEVER computes directly.

---

## ARCHITECTURE DECISIONS FOR WEB APP

### Auth: Google OAuth 2.0 (free, simple, Pandit Ji has Google account)
- Library: `authlib` (FastAPI integration)
- Flow: "Sign in with Google" button → Google redirect → callback → session
- No password management, no email verification, no SMS OTP
- Session stored in encrypted cookie (no Redis needed)
- First login auto-creates user profile
- Role: `owner` (Manish) | `pandit` (Pandit Ji) | `family` (family members)
- Access control: each user sees ONLY their clients/charts
- Apple Sign-In: skip for v1 (needs Apple Developer account $99/year)

### Database: SQLite (free, zero config, one file)
- `data/jyotish.db` — single file, backs up easily
- Tables: users, clients, charts, gemstones, events, daily_cache
- ORM: SQLModel (Pydantic + SQLAlchemy, already in FastAPI ecosystem)

### Notifications: Telegram Bot (free, works on Oracle)
- Already in your architecture: `apps/telegram/`
- Daily guidance at 5:30 AM via Telegram
- Telegram bot is FREE to run 24/7 on Oracle
- WhatsApp Business API costs money — skip for v1
- Push notifications need PWA service worker — Phase 2

### Hosting: Oracle Cloud Always Free
- 4 ARM CPU, 24GB RAM, 200GB disk
- Caddy reverse proxy (auto SSL, zero config)
- systemd service (auto-start, auto-restart)
- SQLite backup to Google Drive daily (rclone, free)

---

## PHASE 1: WEB APP SKELETON (Hours 1-3)

### Task 1.1: FastAPI App with Auth

File: `apps/src/jyotish_app/web/app.py`

```python
# What to build:
# - FastAPI app with Jinja2 templates
# - Google OAuth 2.0 login/logout
# - Session middleware (encrypted cookies)
# - Static file serving (CSS, JS)
# - Role-based access (owner/pandit/family)
```

Dependencies to add in `apps/pyproject.toml`:
```
authlib>=1.3
httpx>=0.27
itsdangerous>=2.1
python-multipart>=0.0.9
```

Routes:
```
GET  /                    → Login page (if not auth) OR dashboard (if auth)
GET  /auth/google         → Redirect to Google OAuth
GET  /auth/callback       → Google callback, create session
GET  /auth/logout         → Clear session, redirect to /
GET  /dashboard           → Client list for current user
GET  /new                 → New client input form
POST /generate            → Compute chart, save to DB, redirect to report
GET  /client/{id}         → Client overview (kundli page)
GET  /client/{id}/dasha   → Dasha deep-dive
GET  /client/{id}/ratna   → Gemstone recommendations
GET  /client/{id}/pdf     → Download PDF
```

### Task 1.2: Database Schema

File: `apps/src/jyotish_app/web/database.py`

```python
# SQLModel tables:

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    google_id: str = Field(unique=True, index=True)
    email: str
    name: str
    picture_url: str | None = None
    role: str = "family"  # owner | pandit | family
    created_at: datetime
    last_login: datetime

class Client(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str
    name_hi: str | None = None
    dob: str  # DD/MM/YYYY
    tob: str  # HH:MM
    place: str
    place_hi: str | None = None
    lat: float
    lon: float
    gender: str
    chart_json: str  # Full ChartData as JSON string
    dasha_json: str | None = None
    gems_json: str | None = None
    created_at: datetime
    updated_at: datetime

class DailyCache(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="client.id")
    date: str  # YYYY-MM-DD
    guidance_json: str
```

### Task 1.3: Design Tokens CSS

File: `apps/src/jyotish_app/web/static/tokens.css`

Generate from `jyotish-ui/tokens/design-tokens.json`.
This is the ONLY CSS file that defines colors, fonts, spacing.

File: `apps/src/jyotish_app/web/static/components.css`

All component styles using CSS variables from tokens.css.
Every class prefixed with `j-`.

### Tests for Phase 1:
```python
# tests/apps/web/test_app.py
def test_homepage_redirects_to_login_when_unauthenticated()
def test_google_oauth_redirect_url()
def test_dashboard_requires_auth()
def test_client_list_only_shows_own_clients()

# tests/apps/web/test_database.py
def test_create_user()
def test_create_client_with_chart()
def test_client_belongs_to_user()
```

---

## PHASE 2: INPUT FORM PAGE (Hours 3-5)

### Task 2.1: Hindi Input Form Template

File: `apps/src/jyotish_app/web/templates/input_form.html`

- Full Hindi form matching `input_template_hindi.md`
- Uses design system components (j-input, j-radio-row, j-button)
- Sections: मूल जानकारी, व्यक्तिगत, परिवार, स्वास्थ्य, जीवन घटनाएं
- Place autocomplete using a simple Indian cities JSON list
- Client-side validation (required fields)
- POST to /generate

### Task 2.2: Chart Generation Route

File: `apps/src/jyotish_app/web/routes.py`

```python
@router.post("/generate")
async def generate_chart(request: Request, db: Session):
    # 1. Parse form data
    # 2. Call engine: compute_chart(name, dob, tob, lat, lon, tz, gender)
    # 3. Call products: compute_dasha, recommend_gems, detect_yogas
    # 4. Serialize all to JSON
    # 5. Save Client record to SQLite
    # 6. Redirect to /client/{id}
```

### Task 2.3: Indian Cities Dataset

File: `apps/src/jyotish_app/web/static/cities.json`

Top 500 Indian cities with lat/lon/state. Used for place autocomplete.
Source: simplified from GeoNames India dataset.

### Tests for Phase 2:
```python
def test_form_renders_with_all_fields()
def test_form_submission_creates_client()
def test_chart_computed_correctly_on_submission()
def test_required_fields_validated()
```

---

## PHASE 3: KUNDLI OVERVIEW PAGE (Hours 5-7)

### Task 3.1: Overview Template

File: `apps/src/jyotish_app/web/templates/overview.html`

This is the MAIN report page. Renders from Client.chart_json.

Sections (scrollable single page):
1. Sacred header (श्री गणेशाय नमः + name + birth details)
2. Birth strip (lagna, rashi, nakshatra, current dasha)
3. North Indian diamond chart (SVG)
4. Planet positions table
5. Active yogas
6. Dasha timeline (current expanded with antardashas)
7. Gemstone recommendations
8. Ashtakvarga summary bars
9. Computation seal
10. Footer (शुभम् भवतु)

All data comes from `client.chart_json` — parsed in the route, passed to template.
ZERO computation in template. Just rendering.

### Task 3.2: SVG Diamond Chart Component

File: `apps/src/jyotish_app/web/templates/components/diamond_chart.html`

Jinja2 macro that generates the North Indian SVG diamond.
Input: planets list, lagna sign number.
Uses graha colors from design tokens (semantic.shubh/ashubh/marak/yoga).

### Task 3.3: Reusable Jinja2 Macros

File: `apps/src/jyotish_app/web/templates/components/macros.html`

```jinja2
{% macro j_header(subject) %} ... {% endmacro %}
{% macro j_strip(items) %} ... {% endmacro %}
{% macro j_tag(label, variant) %} ... {% endmacro %}
{% macro j_graha_icon(planet_id) %} ... {% endmacro %}
{% macro j_divider(variant='dot') %} ... {% endmacro %}
{% macro j_card(title, variant) %} ... {% endmacro %}
{% macro j_timeline_item(dasha, active=false) %} ... {% endmacro %}
{% macro j_gem_card(gem) %} ... {% endmacro %}
{% macro j_yoga_card(yoga) %} ... {% endmacro %}
{% macro j_mantra(text, info) %} ... {% endmacro %}
{% macro j_seal(computation) %} ... {% endmacro %}
{% macro j_footer() %} ... {% endmacro %}
```

Each macro = one component from design system.
Each receives data as parameters.
Each uses only CSS classes from components.css.

### Tests for Phase 3:
```python
def test_overview_page_renders_for_manish()
def test_diamond_chart_has_9_planets()
def test_planet_colors_match_lordship_roles()
def test_prohibited_stones_shown_in_red()
def test_current_dasha_highlighted()
```

---

## PHASE 4: DASHBOARD + CLIENT LIST (Hours 7-8)

### Task 4.1: Dashboard Template

File: `apps/src/jyotish_app/web/templates/dashboard.html`

```
┌──────────────────────────────┐
│  ॥ श्री गणेशाय नमः ॥         │
├──────────────────────────────┤
│  नमस्ते, [User Name]         │
│                              │
│  [ + नई कुंडली बनाएं ]       │
│                              │
│  ── मेरे ग्राहक (3) ──        │
│                              │
│  ┌────────────────────────┐  │
│  │ मनीष चौरसिया            │  │
│  │ 13/03/1989 | वाराणसी    │  │
│  │ मिथुन लग्न | गुरु>बुध दशा│  │
│  │ [कुंडली] [दशा] [रत्न]   │  │
│  └────────────────────────┘  │
│  ┌────────────────────────┐  │
│  │ अभय चौरसिया             │  │
│  │ ...                     │  │
│  └────────────────────────┘  │
│                              │
│  शुभम् भवतु                  │
└──────────────────────────────┘
```

Shows only clients belonging to the logged-in user.

### Task 4.2: Login Page Template

File: `apps/src/jyotish_app/web/templates/login.html`

Sacred-themed login page. Single "Sign in with Google" button.
No email/password fields. Clean, warm, minimal.

### Tests for Phase 4:
```python
def test_dashboard_shows_only_user_clients()
def test_dashboard_new_button_links_to_form()
def test_client_card_shows_lagna_and_dasha()
```

---

## PHASE 5: ADDITIONAL PAGES (Hours 8-10)

### Task 5.1: Dasha Deep-dive Page

File: `apps/src/jyotish_app/web/templates/dasha.html`

Full vertical timeline with ALL mahadashas.
Current mahadasha expanded to show all antardashas.
Current antardasha has pulsing "अभी" badge.
Golden period highlighted with gold border.
Past events listed if available.

### Task 5.2: Ratna Vidhan Page

File: `apps/src/jyotish_app/web/templates/ratna.html`

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
git clone https://github.com/master12coder/vedic-ai-framework.git /opt/jyotish
cd /opt/jyotish
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e "apps/[web]"

# Environment
cat > /opt/jyotish/.env << EOF
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DATABASE_URL=sqlite:///opt/jyotish/data/jyotish.db
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
Description=Jyotish AI Web App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/jyotish
EnvironmentFile=/opt/jyotish/.env
ExecStart=/opt/jyotish/.venv/bin/gunicorn jyotish_app.web.app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
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
cp /opt/jyotish/data/jyotish.db /opt/jyotish/data/backup-$(date +%Y%m%d).db
rclone copy /opt/jyotish/data/backup-*.db gdrive:jyotish-backups/
find /opt/jyotish/data/backup-*.db -mtime +7 -delete
EOF
chmod +x /opt/jyotish/scripts/backup.sh

# Cron: backup at 3 AM daily
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/jyotish/scripts/backup.sh") | crontab -

echo "✅ Jyotish AI deployed. Visit https://jyotish.yourdomain.com"
```

### Task 6.2: Google OAuth Setup Instructions

File: `docs/deployment/google-oauth-setup.md`

Step-by-step with screenshots:
1. Go to console.cloud.google.com
2. Create project "Jyotish AI"
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

File: `apps/src/jyotish_app/telegram/bot.py` (already planned)

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
apps/src/jyotish_app/web/
├── app.py                      # FastAPI + auth + middleware
├── routes.py                   # All route handlers
├── database.py                 # SQLModel tables + session
├── auth.py                     # Google OAuth helpers
├── static/
│   ├── tokens.css              # Generated from design-tokens.json
│   ├── components.css          # All j- component styles
│   ├── app.js                  # Minimal JS (form validation, scroll reveal)
│   └── cities.json             # Indian cities for autocomplete
├── templates/
│   ├── base.html               # Base template (head, tokens, footer)
│   ├── login.html              # Google sign-in page
│   ├── dashboard.html          # Client list
│   ├── input_form.html         # Hindi input form
│   ├── overview.html           # Kundli report page
│   ├── dasha.html              # Dasha deep-dive
│   ├── ratna.html              # Gemstone page
│   └── components/
│       ├── macros.html         # All Jinja2 component macros
│       └── diamond_chart.html  # SVG kundli macro

tests/apps/web/
├── test_app.py                 # App startup, middleware
├── test_auth.py                # OAuth flow
├── test_database.py            # CRUD operations
├── test_routes.py              # All route handlers
├── test_overview.py            # Page rendering
├── test_dasha.py               # Dasha page
├── test_ratna.py               # Gemstone page
└── conftest.py                 # Test fixtures (test client, mock auth)

scripts/deploy/
├── setup_oracle.sh             # Full deployment script
├── backup.sh                   # Daily DB backup
└── send_daily.py               # Telegram daily cron

docs/deployment/
├── oracle-setup.md             # Oracle Cloud guide
├── google-oauth-setup.md       # OAuth configuration
└── domain-setup.md             # DNS + SSL
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
1. ✅ Share this plan with Claude Code
2. ✅ Make sure vedic-ai-framework repo is on GitHub

### After overnight run:
1. Create Oracle Cloud account (cloud.oracle.com) — 10 min
2. Create Google Cloud OAuth credentials — 10 min
3. Buy domain or set up free DuckDNS subdomain — 5 min
4. SSH into Oracle VM, run setup_oracle.sh — 5 min
5. Open browser → see Jyotish AI running

### After deployment:
1. Share link with Pandit Ji
2. Add Pandit Ji's email to ALLOWED_EMAILS
3. Pandit Ji clicks "Sign in with Google" → starts using
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
