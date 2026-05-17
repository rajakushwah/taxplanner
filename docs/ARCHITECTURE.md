# Taxplanner — Architecture Documentation

> Indian Income Tax Calculator — compare Old vs New tax regimes, save calculations per user, and recommend the lower-tax option.

**Production domain:** [taxplannerindia.com](https://taxplannerindia.com)  
**Repository:** `rajakushwah/taxplanner`

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Technology Stack](#technology-stack)
3. [High-Level Architecture](#high-level-architecture)
4. [Project Structure](#project-structure)
5. [Django Applications](#django-applications)
6. [Data Model & ER Diagram](#data-model--er-diagram)
7. [URL Routing & Endpoints](#url-routing--endpoints)
8. [API Reference](#api-reference)
9. [Tax Calculation Engine](#tax-calculation-engine)
10. [Request Flows](#request-flows)
11. [Authentication & Authorization](#authentication--authorization)
12. [Frontend & Static Assets](#frontend--static-assets)
13. [Database Configuration](#database-configuration)
14. [Deployment & CI/CD](#deployment--cicd)
15. [Management Commands](#management-commands)
16. [Dependencies](#dependencies)
17. [Known Gaps & Technical Debt](#known-gaps--technical-debt)
18. [Local Development](#local-development)

---

## Executive Summary

Taxplanner is a **monolithic, server-rendered web application** built with **Django 4.2**. Users register with email, enter annual salary and deduction details, and receive a side-by-side comparison of **Old Regime** vs **New Regime** Indian income tax. Results are persisted per user per financial year.

There is **no separate frontend framework** (no React/Vue), **no REST API framework** (no Django REST Framework), and **no background job queue**. A single custom JSON endpoint powers live preview on the calculation form.

---

## Technology Stack

| Layer | Technology | Notes |
|--------|------------|-------|
| **Language** | Python 3 | Implicit; not pinned in repo |
| **Web framework** | Django 4.2 (`Django>=4.2,<5.0`) | Monolithic MVC |
| **Database** | SQLite (`db.sqlite3`) | File-based; same config for dev and deploy in repo |
| **ORM** | Django ORM | Models in `tax_calculator/models.py` |
| **Auth** | Django sessions + custom user | Email login; no JWT/OAuth |
| **Templates** | Django Templates | Server-side HTML rendering |
| **CSS / UI** | Bootstrap 5.3.2 (CDN) | Bootstrap Icons, Google Fonts (Inter) |
| **JavaScript** | Vanilla JS | `static/js/main.js` + inline in templates |
| **API** | One custom JSON view | `POST /api/quick-calculate/` — not REST/DRF |
| **Static files** | Django `staticfiles` | `collectstatic` → `staticfiles/` on deploy |
| **Timezone** | `Asia/Kolkata` | `USE_TZ = True` |
| **Deployment** | GitHub Actions → SSH → VPS | systemd + nginx |
| **WSGI** | `income_tax_project.wsgi` | Standard Django entry |

### Not used in this codebase

- React, Vue, Angular, or SPA build tooling  
- Django REST Framework (DRF)  
- PostgreSQL / MySQL (in settings)  
- Redis, Celery, RabbitMQ  
- Docker / Kubernetes manifests  
- Automated tests  
- Email verification service (field exists, unused)  

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Client (Browser)                              │
│  Bootstrap 5 + Vanilla JS + CSRF token + Session cookie                 │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ HTTP(S)
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         nginx (production VPS)                          │
│                    Reverse proxy → Gunicorn/uWSGI                       │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Django Application (Monolith)                        │
│  ┌─────────────────┐  ┌──────────────┐  ┌─────────────────────────────┐ │
│  │ Views           │  │ Forms        │  │ TaxCalculator (tax_service) │ │
│  │ (views.py)      │→ │ (forms.py)   │→ │ Pure calculation logic      │ │
│  └────────┬────────┘  └──────────────┘  └─────────────────────────────┘ │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐  ┌──────────────┐  ┌─────────────────────────────┐ │
│  │ Django ORM      │→ │ SQLite       │  │ Django Admin + Custom Admin │ │
│  │ (models.py)     │  │ db.sqlite3   │  │ Panel                       │ │
│  └─────────────────┘  └──────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

**Architectural style:** Classic Django layered app — **Presentation** (templates/views) → **Business logic** (`TaxCalculator`) → **Persistence** (models/ORM).

---

## Project Structure

```
taxplanner/
├── manage.py                          # Django CLI entry point
├── requirements.txt                   # Python dependencies (Django only)
├── project.md                         # Empty placeholder
├── docs/
│   └── ARCHITECTURE.md                # This document
├── .github/workflows/
│   └── deploy.yml                     # CI/CD: push main → VPS deploy
├── income_tax_project/                # Django project package
│   ├── settings.py                    # Global configuration
│   ├── urls.py                        # Root URLconf
│   ├── wsgi.py                        # WSGI application
│   └── asgi.py                        # ASGI application
├── tax_calculator/                    # Sole custom Django app
│   ├── models.py                      # Domain models
│   ├── views.py                       # HTTP handlers
│   ├── urls.py                        # App URL routes
│   ├── forms.py                       # Django forms
│   ├── admin.py                       # Django admin registration
│   ├── tax_service.py                 # Tax calculation engine
│   ├── apps.py
│   ├── migrations/
│   ├── management/commands/
│   │   └── setup_initial_data.py      # Seed FY + admin user
│   └── templatetags/
│       └── indian_format.py           # Indian number formatting filter
├── templates/
│   ├── base.html                      # Layout shell
│   └── tax_calculator/                # Page templates + admin/
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── img/favicon.svg
└── (runtime, gitignored)
    ├── db.sqlite3
    ├── venv/
    ├── staticfiles/
    └── media/
```

---

## Django Applications

### `income_tax_project` (project package)

| Responsibility | Location |
|----------------|----------|
| Settings, middleware, installed apps | `settings.py` |
| Root URL routing | `urls.py` |
| WSGI/ASGI entry | `wsgi.py`, `asgi.py` |

**Root URLs:**

| Path | Handler |
|------|---------|
| `/admin/` | Django built-in admin |
| `/*` | Delegated to `tax_calculator.urls` |
| `/static/`, `/media/` | Served directly when `DEBUG=True` |

### `tax_calculator` (sole custom app)

| Module | Purpose |
|--------|---------|
| `models.py` | `CustomUser`, `FinancialYear`, `SalaryDetail`, `TaxCalculation` |
| `views.py` | Page views, auth, tax CRUD, AJAX, staff admin panel |
| `forms.py` | Registration, login, salary input, profile |
| `tax_service.py` | `TaxCalculator` — slabs, deductions, rebate, surcharge, cess |
| `admin.py` | Model registration for Django admin |
| `templatetags/indian_format.py` | `{% indian_comma %}` template filter |

**Built-in Django apps used:** `admin`, `auth`, `contenttypes`, `sessions`, `messages`, `staticfiles`, `humanize`.

---

## Data Model & ER Diagram

### Entity Relationship

```
┌──────────────────┐
│   CustomUser     │
│  (email login)   │
└────────┬─────────┘
         │ 1
         │
         │ *
┌────────▼─────────┐       ┌──────────────────┐
│   SalaryDetail   │───────│  FinancialYear   │
│  (UUID PK)       │  *  1 │                  │
└────────┬─────────┘       └──────────────────┘
         │ 1
         │
         │ 1
┌────────▼─────────┐
│  TaxCalculation  │
│  (UUID PK)       │
└──────────────────┘

Unique constraint: (user, financial_year) on SalaryDetail
```

### `CustomUser`

Extends `AbstractUser`; **no username field** — login is email-based.

| Field | Type | Description |
|-------|------|-------------|
| `email` | EmailField (unique) | `USERNAME_FIELD` |
| `first_name`, `last_name` | CharField | Required on registration |
| `phone_number` | CharField | Optional |
| `pan_number` | CharField | Optional, max 10 |
| `date_of_birth` | DateField | Optional |
| `is_email_verified` | Boolean | **Stored but unused** in views |
| `created_at`, `updated_at` | DateTime | Auto timestamps |

### `FinancialYear`

Reference data for assessment years.

| Field | Type | Description |
|-------|------|-------------|
| `year` | CharField | e.g. `"2025-26"` |
| `start_date`, `end_date` | DateField | FY boundaries (Apr–Mar) |
| `is_active` | Boolean | Shown in salary form dropdown |

Seeded via `python manage.py setup_initial_data` (FY 2025-26, 2026-27).

### `SalaryDetail`

Stores one salary record per user per financial year (UUID primary key).

**Income components:**

| Field | Cap / Notes |
|-------|-------------|
| `basic_salary` | — |
| `hra_received` | HRA component |
| `special_allowance` | — |
| `lta` | Leave Travel Allowance |
| `bonus` | — |
| `other_income` | — |

**HRA inputs:**

| Field | Notes |
|-------|-------|
| `rent_paid` | Annual rent |
| `is_metro_city` | 50% vs 40% of basic for HRA exemption |

**Deductions (primarily Old Regime):**

| Field | Validator cap |
|-------|---------------|
| `deduction_80c` | Max ₹1,50,000 |
| `deduction_80d` | Max ₹1,00,000 |
| `deduction_80e` | No max in model |
| `deduction_80g` | No max in model |
| `home_loan_interest` | Max ₹2,00,000 (Section 24) |
| `nps_contribution` | Max ₹50,000 (80CCD) |
| `employer_nps_contribution` | 80CCD(2) — capped in calculator at 14% of basic |
| `professional_tax` | — |

**Other fields:**

| Field | Notes |
|-------|-------|
| `age_group` | `below_60`, `60_to_80`, `above_80` — **forced to `below_60` on create** |
| `standard_deduction` | Default 75000 on model — **not used by TaxCalculator** |

**Computed properties:** `gross_salary`, `hra_exemption` (logic duplicated in `tax_service.py`).

### `TaxCalculation`

One-to-one with `SalaryDetail`. Persists comparison snapshot.

| Field group | Fields |
|-------------|--------|
| Old regime | `old_regime_gross_income`, `old_regime_total_deductions`, `old_regime_taxable_income`, `old_regime_tax`, `old_regime_cess`, `old_regime_total_tax` |
| New regime | `new_regime_*` (same structure) |
| Recommendation | `recommended_regime` (`'old'` or `'new'`), `tax_savings` |

**Not persisted:** surcharge breakdown, marginal relief line items (only in live `compare_regimes()` dict).

---

## URL Routing & Endpoints

### Root (`income_tax_project/urls.py`)

| Path | Name | Auth | Description |
|------|------|------|-------------|
| `/admin/` | — | Staff | Django admin |
| `/` | `home` | Public | Landing page |
| `/register/` | `register` | Public | User sign-up |
| `/login/` | `login` | Public | Email login |
| `/logout/` | `logout` | Login | Session logout |
| `/dashboard/` | `dashboard` | Login | List user's salary records |
| `/profile/` | `profile` | Login | Edit profile |
| `/calculate/` | `calculate_tax` | Login | Salary form + save + calculate |
| `/result/<uuid>/` | `tax_result` | Login | Results page (owner only) |
| `/edit/<uuid>/` | `edit_salary` | Login | Update salary record |
| `/delete/<uuid>/` | `delete_salary` | Login | Delete confirmation |
| `/api/quick-calculate/` | `quick_calculate` | Login + POST | JSON preview (no DB save) |
| `/admin-panel/` | `admin_dashboard` | Staff | Custom admin dashboard |
| `/admin-panel/user/<id>/` | `admin_user_detail` | Staff | User detail |
| `/admin-panel/calculation/<uuid>/` | `admin_view_calculation` | Staff | View any calculation |

---

## API Reference

There is **no formal REST API**. One AJAX endpoint exists:

### `POST /api/quick-calculate/`

| Property | Value |
|----------|-------|
| **Auth** | `@login_required` |
| **Method** | POST only (`@require_POST`) |
| **CSRF** | Required (standard Django) |
| **Response** | `application/json` |

**Request body (form fields):**

`basic_salary`, `hra_received`, `special_allowance`, `lta`, `bonus`, `other_income`, `rent_paid`, `is_metro_city`, `deduction_80c`, `deduction_80d`, `deduction_80e`, `deduction_80g`, `home_loan_interest`, `nps_contribution`, `employer_nps_contribution`, `professional_tax`, `age_group`, `financial_year`

**Success response:**

```json
{
  "success": true,
  "old_regime_tax": 125000.0,
  "new_regime_tax": 98000.0,
  "recommended": "new",
  "savings": 27000.0,
  "gross_income": 1500000.0
}
```

**Error response:**

```json
{
  "success": false,
  "error": "error message"
}
```

**Behavior:** Builds a temporary in-memory object (not saved to DB), runs `TaxCalculator.compare_regimes()`, returns summary totals. Used by debounced JavaScript on `calculate_tax.html`.

---

## Tax Calculation Engine

**Location:** `tax_calculator/tax_service.py`  
**Class:** `TaxCalculator(salary_detail)`

### Design

- **Stateless service** — takes a `SalaryDetail`-like object (model instance or `TempSalary` for AJAX).
- **No database access** inside the calculator.
- **Returns nested dicts** from `compare_regimes()` for views to persist or display.

### Gross income

```
gross = basic + HRA + special_allowance + LTA + bonus + other_income
```

### Old regime deductions

| Deduction | Rule |
|-----------|------|
| Standard deduction | ₹50,000 (hardcoded `STANDARD_DEDUCTION_OLD`) |
| HRA exemption | Min of: actual HRA, rent − 10% basic, 50%/40% of basic |
| Section 80C | Capped at ₹1,50,000 |
| Section 80D | As entered (model max ₹1L) |
| Section 80E, 80G | As entered |
| Section 24 (home loan) | Capped at ₹2,00,000 |
| 80CCD (NPS self) | Capped at ₹50,000 |
| 80CCD(2) (employer NPS) | Min(employer contribution, 14% of basic) |
| Professional tax | As entered |

### New regime deductions

| Deduction | Rule |
|-----------|------|
| Standard deduction | ₹75,000 (hardcoded `STANDARD_DEDUCTION_NEW`) |
| Employer NPS (80CCD(2)) | Min(employer contribution, 14% of basic) |
| Professional tax | As entered |
| 80C, HRA, 80D, etc. | **Not allowed** in new regime |

### Tax slabs

**Old regime** — varies by `age_group`:

| Age group | Slab key |
|-----------|----------|
| Below 60 | `OLD_REGIME_SLABS` |
| 60–80 | `OLD_REGIME_SLABS_SENIOR` |
| 80+ | `OLD_REGIME_SLABS_SUPER_SENIOR` |

Example (below 60): 0% up to ₹2.5L, 5% ₹2.5–5L, 20% ₹5–10L, 30% above ₹10L.

**New regime** — Budget 2025 style (`NEW_REGIME_SLABS_FY2526`):

0% up to ₹4L → 5% → 10% → 15% → 20% → 25% → 30% above ₹24L.

### Section 87A rebate

| Regime | Condition | Rebate |
|--------|-----------|--------|
| Old | Taxable income ≤ ₹5L | ₹12,500 |
| New | Taxable income ≤ ₹12L | ₹60,000 |

Rebate applied before surcharge. Comment in code: rebate only when no surcharge applies at higher incomes.

### Surcharge

Applied when taxable income > **₹50 lakhs**:

| Income band | New regime | Old regime |
|-------------|------------|------------|
| ₹50L – ₹1Cr | 10% | 10% |
| ₹1Cr – ₹2Cr | 15% | 15% |
| ₹2Cr – ₹5Cr | 25% | 25% |
| Above ₹5Cr | 25% | **37%** |

**Marginal relief** applied at bracket thresholds to cap surcharge spike.

### Health & Education Cess

**4%** on `(tax + surcharge)`.

### Comparison output

```python
{
    'old_regime': { ... full breakdown ... },
    'new_regime': { ... full breakdown ... },
    'recommended_regime': 'old' | 'new',  # lower total_tax wins
    'tax_savings': abs(old_total - new_total),
}
```

---

## Request Flows

### User registration & login

```
GET/POST /register/  → UserRegistrationForm → CustomUser created → redirect /login/
GET/POST /login/     → UserLoginForm (email) → session created
                     → staff → /admin-panel/
                     → user  → /dashboard/
```

### Persisted tax calculation

```
POST /calculate/
  → Ensure active FinancialYear exists (auto-create if none)
  → SalaryDetailForm validation
  → transaction.atomic():
       → Upsert SalaryDetail (user + FY unique; age_group = 'below_60')
       → TaxCalculator(salary_detail).compare_regimes()
       → TaxCalculation.update_or_create(...)
  → redirect /result/<uuid>/
```

### View results

```
GET /result/<uuid>/
  → get SalaryDetail (pk + user=request.user)
  → load TaxCalculation
  → Re-run TaxCalculator for live breakdown in template
```

### Live preview (AJAX)

```
User types in calculate_tax.html
  → debounced POST /api/quick-calculate/ + CSRF
  → TempSalary object built from POST data
  → TaxCalculator(temp).compare_regimes()
  → JSON returned → UI updates totals
```

### Staff admin panel

```
Staff user → /admin-panel/
  → Paginated user list, search
  → /admin-panel/user/<id>/ → user's calculations
  → /admin-panel/calculation/<uuid>/ → any user's result
```

---

## Authentication & Authorization

| Mechanism | Implementation |
|-----------|----------------|
| **User model** | `AUTH_USER_MODEL = 'tax_calculator.CustomUser'` |
| **Login field** | Email (`USERNAME_FIELD = 'email'`) |
| **Session** | Django default session middleware |
| **Session lifetime** | 1 hour (`SESSION_COOKIE_AGE = 3600`) |
| **Browser close** | `SESSION_EXPIRE_AT_BROWSER_CLOSE = True` |
| **Password rules** | Min 8 chars + Django validators |

**Decorators:**

| Decorator | Used on |
|-----------|---------|
| `@login_required` | Dashboard, calculate, profile, AJAX, etc. |
| `@user_passes_test(is_admin)` | Custom admin panel views |

**Object ownership:** `get_object_or_404(SalaryDetail, pk=pk, user=request.user)` on user-facing CRUD.

**Security settings (from `settings.py`):**

| Setting | Value | Production note |
|---------|-------|-----------------|
| `SECRET_KEY` | Hardcoded in repo | **Should be env var** |
| `DEBUG` | `True` | Should be `False` in production |
| `SESSION_COOKIE_SECURE` | `False` | Enable with HTTPS |
| `CSRF_COOKIE_SECURE` | `False` | Enable with HTTPS |
| `CSRF_TRUSTED_ORIGINS` | taxplannerindia.com | Via env override |
| `ALLOWED_HOSTS` | localhost + production domain | Via env override |

---

## Frontend & Static Assets

### Templates

| Template | Purpose |
|----------|---------|
| `templates/base.html` | Nav, messages, Bootstrap CDN, blocks |
| `tax_calculator/home.html` | Marketing landing |
| `tax_calculator/register.html`, `login.html` | Auth |
| `tax_calculator/dashboard.html` | User's saved records |
| `tax_calculator/calculate_tax.html` | Salary form + live preview |
| `tax_calculator/tax_result.html` | Regime comparison UI |
| `tax_calculator/edit_salary.html` | Edit record |
| `tax_calculator/confirm_delete.html` | Delete confirm |
| `tax_calculator/profile.html` | Profile edit |
| `tax_calculator/admin/*.html` | Staff dashboard |

### Static files

| Path | Purpose |
|------|---------|
| `static/css/style.css` | Custom styles |
| `static/js/main.js` | Currency formatting, debounce, AJAX preview |
| `static/img/favicon.svg` | Favicon |

### CDN dependencies (not in `requirements.txt`)

- Bootstrap 5.3.2 CSS/JS  
- Bootstrap Icons  
- Google Fonts — Inter  

### Template tags

`{% load indian_format %}` → `{{ value|indian_comma }}` for Indian numbering (e.g. 12,34,567).

---

## Database Configuration

From `income_tax_project/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

| Setting | Value |
|---------|-------|
| `STATIC_URL` | `static/` |
| `STATICFILES_DIRS` | `BASE_DIR / 'static'` |
| `STATIC_ROOT` | `staticfiles/` |
| `MEDIA_URL` | `media/` |
| `MEDIA_ROOT` | `media/` |

No file upload views are implemented despite `MEDIA_*` configuration.

---

## Deployment & CI/CD

### GitHub Actions (`.github/workflows/deploy.yml`)

**Trigger:** Push to `main`

**Steps:**

1. Checkout repository  
2. Decode SSH key from `secrets.VPS_SSH_KEY_B64`  
3. SSH to VPS (`secrets.VPS_HOST`, `secrets.VPS_USER`)  
4. On server at `/var/www/taxplanner`:
   - `git fetch && git reset --hard origin/main`
   - `pip install -r requirements.txt`
   - `python manage.py migrate`
   - `python manage.py collectstatic --noinput`
   - `systemctl restart taxplanner`
   - `systemctl restart nginx`

### Production stack (inferred, not in repo)

| Component | Notes |
|-----------|-------|
| **App server** | systemd unit `taxplanner` (likely Gunicorn) |
| **Web server** | nginx |
| **App path** | `/var/www/taxplanner` |
| **Virtualenv** | `/var/www/taxplanner/venv` |

**Not in repository:** nginx config, systemd unit file, Gunicorn settings, production `settings` split, `.env.example`.

---

## Management Commands

### `python manage.py setup_initial_data`

| Action | Detail |
|--------|--------|
| Seed financial years | FY 2025-26, 2026-27 (active) |
| Deactivate old FYs | 2024-25, 2023-24, 2022-23 |
| Create superuser | `admin@taxcalculator.com` / `admin123` (**change immediately**) |

---

## Dependencies

### `requirements.txt`

```
Django>=4.2,<5.0
```

Transitive packages (not pinned): `asgiref`, `sqlparse`, etc.

### Frontend (CDN only)

- Bootstrap 5.3.2  
- Bootstrap Icons  
- Google Fonts  

---

## Known Gaps & Technical Debt

| # | Issue | Impact |
|---|-------|--------|
| 1 | `project.md` is empty | No in-repo quick start |
| 2 | `age_group` excluded from `SalaryDetailForm`; hardcoded `below_60` on create | Senior citizen slabs unused in main flow |
| 3 | `edit_salary.html` may reference `form.age_group` but field is excluded | Possible broken edit UI |
| 4 | FY-specific new regime slabs not fully wired | `get_new_regime_slabs_and_rebate()` returns FY 2025-26 slabs for all years |
| 5 | `standard_deduction` model field unused | Calculator uses hardcoded ₹50k / ₹75k |
| 6 | HRA logic duplicated | `SalaryDetail.hra_exemption` and `TaxCalculator.calculate_hra_exemption` |
| 7 | `is_email_verified` unused | No email verification flow |
| 8 | No automated tests | Regression risk on tax logic changes |
| 9 | Minimal `requirements.txt` | No gunicorn, whitenoise, psycopg2 pinned |
| 10 | `SECRET_KEY` in source | Security risk if repo is public |
| 11 | Default admin password in setup command | Security risk if not changed |
| 12 | Surcharge/rebate ordering | Edge cases at ₹50L+ may need professional validation |
| 13 | No media upload features | `MEDIA_*` configured but unused |

### Positive patterns

- Clear separation: **models** (persistence) vs **`TaxCalculator`** (pure logic)  
- **`transaction.atomic()`** on save+calculate paths  
- **Upsert** per user per FY avoids duplicate salary rows  
- **Live preview** via debounced AJAX  
- **Dual admin**: Django admin + custom staff panel  
- **Indian number formatting** in templates and JS  

---

## Local Development

```bash
# Clone
git clone git@github.com:rajakushwah/taxplanner.git
cd taxplanner

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Install
pip install -r requirements.txt

# Database
python manage.py migrate
python manage.py setup_initial_data

# Run
python manage.py runserver
```

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8000/ | Application |
| http://127.0.0.1:8000/admin/ | Django admin |
| Admin login | `admin@taxcalculator.com` / `admin123` (after setup) |

---

## File Reference

| Concern | Path |
|---------|------|
| Settings | `income_tax_project/settings.py` |
| Tax engine | `tax_calculator/tax_service.py` |
| Models | `tax_calculator/models.py` |
| Views | `tax_calculator/views.py` |
| URLs | `tax_calculator/urls.py`, `income_tax_project/urls.py` |
| Forms | `tax_calculator/forms.py` |
| Deploy workflow | `.github/workflows/deploy.yml` |

---

*Last updated: May 2026 — generated from codebase analysis.*
