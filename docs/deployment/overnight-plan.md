# OVERNIGHT BUILD PLAN — DaivAI Web App (Phases 1-4)
## 10-12 Hour Claude Code Execution Plan
## Date: March 19, 2026

> For Phases 5-7, file structure, test commands, and execution order,
> see `overnight-plan-details.md`.

---

## CONTEXT FOR CLAUDE CODE

Read these files FIRST (in order):
1. `docs/architecture/overview.md` — 3-package architecture
2. `docs/architecture/DECISIONS.md` — ADRs
3. `CLAUDE.md` — Hard rules
4. This file — What to build tonight

The web app lives in `apps/src/daivai_app/web/`.
It uses FastAPI (already in the stack) + Jinja2 templates + our design tokens.
It is ONE MORE DELIVERY CHANNEL — like CLI and Telegram.
It calls products/ which calls engine/. It NEVER computes directly.

---

## ARCHITECTURE DECISIONS FOR WEB APP

### Auth: Google OAuth 2.0 (free, simple, Pandit Ji has Google account)
- Library: `authlib` (FastAPI integration)
- Flow: "Sign in with Google" button -> Google redirect -> callback -> session
- No password management, no email verification, no SMS OTP
- Session stored in encrypted cookie (no Redis needed)
- First login auto-creates user profile
- Role: `owner` (Manish) | `pandit` (Pandit Ji) | `family` (family members)
- Access control: each user sees ONLY their clients/charts
- Apple Sign-In: skip for v1 (needs Apple Developer account $99/year)

### Database: SQLite (free, zero config, one file)
- `data/daivai.db` — single file, backs up easily
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

File: `apps/src/daivai_app/web/app.py`

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
GET  /                    -> Login page (if not auth) OR dashboard (if auth)
GET  /auth/google         -> Redirect to Google OAuth
GET  /auth/callback       -> Google callback, create session
GET  /auth/logout         -> Clear session, redirect to /
GET  /dashboard           -> Client list for current user
GET  /new                 -> New client input form
POST /generate            -> Compute chart, save to DB, redirect to report
GET  /client/{id}         -> Client overview (kundli page)
GET  /client/{id}/dasha   -> Dasha deep-dive
GET  /client/{id}/ratna   -> Gemstone recommendations
GET  /client/{id}/pdf     -> Download PDF
```

### Task 1.2: Database Schema

File: `apps/src/daivai_app/web/database.py`

SQLModel tables:
- **User:** google_id (unique), email, name, picture_url, role (owner/pandit/family), created_at, last_login
- **Client:** user_id (FK), name, name_hi, dob, tob, place, lat, lon, gender, chart_json, dasha_json, gems_json, timestamps
- **DailyCache:** client_id (FK), date, guidance_json

### Task 1.3: Design Tokens CSS

File: `apps/src/daivai_app/web/static/tokens.css`

Generate from `jyotish-ui/tokens/design-tokens.json`.
This is the ONLY CSS file that defines colors, fonts, spacing.

File: `apps/src/daivai_app/web/static/components.css`

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

File: `apps/src/daivai_app/web/templates/input_form.html`

- Full Hindi form matching `input_template_hindi.md`
- Uses design system components (j-input, j-radio-row, j-button)
- Sections: मूल जानकारी, व्यक्तिगत, परिवार, स्वास्थ्य, जीवन घटनाएं
- Place autocomplete using a simple Indian cities JSON list
- Client-side validation (required fields)
- POST to /generate

### Task 2.2: Chart Generation Route

File: `apps/src/daivai_app/web/routes.py`

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

File: `apps/src/daivai_app/web/static/cities.json`

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

File: `apps/src/daivai_app/web/templates/overview.html`

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

File: `apps/src/daivai_app/web/templates/components/diamond_chart.html`

Jinja2 macro that generates the North Indian SVG diamond.
Input: planets list, lagna sign number.
Uses graha colors from design tokens (semantic.shubh/ashubh/marak/yoga).

### Task 3.3: Reusable Jinja2 Macros

File: `apps/src/daivai_app/web/templates/components/macros.html`

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

File: `apps/src/daivai_app/web/templates/dashboard.html`

```
+------------------------------+
|  || श्री गणेशाय नमः ||       |
+------------------------------+
|  नमस्ते, [User Name]         |
|                              |
|  [ + नई कुंडली बनाएं ]       |
|                              |
|  -- मेरे ग्राहक (3) --       |
|                              |
|  +------------------------+  |
|  | मनीष चौरसिया            |  |
|  | 13/03/1989 | वाराणसी    |  |
|  | मिथुन लग्न | गुरु>बुध दशा|  |
|  | [कुंडली] [दशा] [रत्न]   |  |
|  +------------------------+  |
|  +------------------------+  |
|  | अभय चौरसिया             |  |
|  | ...                     |  |
|  +------------------------+  |
|                              |
|  शुभम् भवतु                  |
+------------------------------+
```

Shows only clients belonging to the logged-in user.

### Task 4.2: Login Page Template

File: `apps/src/daivai_app/web/templates/login.html`

Sacred-themed login page. Single "Sign in with Google" button.
No email/password fields. Clean, warm, minimal.

### Tests for Phase 4:
```python
def test_dashboard_shows_only_user_clients()
def test_dashboard_new_button_links_to_form()
def test_client_card_shows_lagna_and_dasha()
```
