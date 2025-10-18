# File tree
.: [from repo root]
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── accounts
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── managers.py
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── models.py
│   ├── urls.py
│   ├── validators.py
│   └── views.py
├── config
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core
│   ├── __init__.py
│   ├── apps.py
│   ├── management
│   │   ├── __init__.py
│   │   └── commands
│   │       ├── __init__.py
│   │       └── seed_baseline.py
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── models.py
│   └── views.py
├── docker-compose.yml
├── manage.py
├── profiles
│   ├── __init__.py
│   ├── apps.py
│   ├── forms.py
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   ├── 0002_profile_utc_offset_minutes.py
│   │   └── __init__.py
│   ├── models.py
│   ├── signals.py
│   ├── templates
│   │   └── profiles
│   │       └── settings.html
│   ├── units.py
│   ├── urls.py
│   └── views.py
├── scripts
│   └── bootstrap-env.sh
├── task_description.txt
├── task_plan.txt
└── templates
    └── accounts
        ├── signin.html
        └── signup.html

# Django apps
accounts
- `accounts/apps.py`: `class AccountsConfig(AppConfig)` auto-configures the app. 【F:accounts/apps.py†L1-L6】
- `accounts/models.py`: `class User(AbstractUser)` drops `username`, makes `email` unique, sets `USERNAME_FIELD="email"`, and registers `UserManager`. 【F:accounts/models.py†L1-L19】
- `accounts/managers.py`: `class UserManager(BaseUserManager)` with `_create_user`, `create_user`, and `create_superuser` enforcing email uniqueness and staff/superuser flags. 【F:accounts/managers.py†L1-L39】
- `accounts/forms.py`: `class SignupForm(forms.Form)` with email uniqueness check, password strength validator (>=8 chars, letter, digit), confirm match; `class EmailAuthenticationForm(AuthenticationForm)` exposes email as username. 【F:accounts/forms.py†L1-L70】
- `accounts/validators.py`: `class LetterNumberPasswordValidator` enforces at least one letter and digit. 【F:accounts/validators.py†L1-L20】
- `accounts/views.py`: `class SignupView(View)` (GET renders form, POST creates user and logs in), `class SigninView(LoginView)` (redirects authenticated users), `class SignoutView(LogoutView)` redirecting to success page. 【F:accounts/views.py†L1-L47】
- `accounts/admin.py`: `class UserAdmin(admin.ModelAdmin)` lists, searches, and manages email-first users. 【F:accounts/admin.py†L1-L20】
- Migrations: `0001_initial.py` creates the custom user model. 【F:accounts/migrations/0001_initial.py†L1-L85】

core
- `core/apps.py`: `class CoreConfig(AppConfig)` registers the app. 【F:core/apps.py†L1-L6】
- `core/models.py`: `class BaselineSeed(models.Model)` with `label`, timestamps, and sentinel constant used to verify seeding. 【F:core/models.py†L1-L21】
- `core/views.py`: `success_view(request)` returns plain text "success"; `health_view(request)` runs DB connectivity, migration checks via `MigrationExecutor`, and looks for the `BaselineSeed` sentinel with optional reasons payload. 【F:core/views.py†L1-L65】
- `core/management/commands/seed_baseline.py`: `class Command(BaseCommand)` ensures the sentinel record exists and logs success. 【F:core/management/commands/seed_baseline.py†L1-L17】
- Migrations: `0001_initial.py` creates `BaselineSeed`. 【F:core/migrations/0001_initial.py†L1-L38】

profiles
- `profiles/apps.py`: `class ProfilesConfig(AppConfig)` imports signals on ready. 【F:profiles/apps.py†L1-L10】
- `profiles/models.py`: `class Profile(models.Model)` stores per-user preferences (`display_name`, `currency`, `distance_unit`, `volume_unit`, `timezone`, `utc_offset_minutes`) with distance/volume unit choices and one-to-one `user`. 【F:profiles/models.py†L1-L47】
- `profiles/forms.py`: `_build_offset_choices()` helper builds UTC offsets; `class ProfileForm(forms.ModelForm)` exposes preference fields with currency/unit validation and overrides `save` to pin timezone to UTC. 【F:profiles/forms.py†L1-L70】
- `profiles/views.py`: `class SettingsView(LoginRequiredMixin, View)` ensures a profile exists, handles GET/POST, updates preferences, flashes success, and builds metric/imperial previews via `profiles.units`. 【F:profiles/views.py†L1-L64】
- `profiles/units.py`: conversion helpers `km_to_miles`, `miles_to_km`, `liters_to_gallons`, `gallons_to_liters`. 【F:profiles/units.py†L1-L31】
- `profiles/signals.py`: `create_user_profile` post-save receiver auto-creates profiles for new users. 【F:profiles/signals.py†L1-L19】
- Templates: `profiles/templates/profiles/settings.html` renders the settings form, messages, and preview. 【F:profiles/templates/profiles/settings.html†L1-L82】
- Migrations: `0001_initial.py` establishes base fields; `0002_profile_utc_offset_minutes.py` adds `utc_offset_minutes`. 【F:profiles/migrations/0001_initial.py†L1-L28】【F:profiles/migrations/0002_profile_utc_offset_minutes.py†L1-L17】

# URL routes
GET / -> core.views.success_view (name `success`). 【F:config/urls.py†L6-L8】【F:core/views.py†L12-L13】
GET /health -> core.views.health_view (name `health`). 【F:config/urls.py†L6-L8】【F:core/views.py†L16-L65】
GET/POST /auth/signup -> accounts.views.SignupView (name `accounts:signup`). 【F:config/urls.py†L6-L10】【F:accounts/urls.py†L5-L11】【F:accounts/views.py†L13-L33】
GET/POST /auth/signin -> accounts.views.SigninView (name `accounts:signin`). 【F:config/urls.py†L6-L10】【F:accounts/urls.py†L5-L11】【F:accounts/views.py†L35-L43】
GET /auth/signout -> accounts.views.SignoutView (name `accounts:signout`). 【F:config/urls.py†L6-L10】【F:accounts/urls.py†L5-L11】【F:accounts/views.py†L45-L47】
GET/POST /settings -> profiles.views.SettingsView (name `profiles:settings`). 【F:config/urls.py†L6-L10】【F:profiles/urls.py†L1-L11】【F:profiles/views.py†L16-L64】
/admin/ -> not configured; Django admin app is not in `INSTALLED_APPS`. 【F:config/settings.py†L20-L38】

# Settings summary
`AUTH_USER_MODEL` -> `accounts.User`. 【F:config/settings.py†L60-L72】
`INSTALLED_APPS` -> `django.contrib.auth`, `django.contrib.contenttypes`, `django.contrib.sessions`, `django.contrib.messages`, `django.contrib.staticfiles`, `accounts.apps.AccountsConfig`, `core`, `profiles.apps.ProfilesConfig`. 【F:config/settings.py†L20-L29】
`MIDDLEWARE` -> `django.middleware.security.SecurityMiddleware`, `django.contrib.sessions.middleware.SessionMiddleware`, `django.middleware.common.CommonMiddleware`, `django.middleware.csrf.CsrfViewMiddleware`, `django.contrib.auth.middleware.AuthenticationMiddleware`, `django.contrib.messages.middleware.MessageMiddleware`. 【F:config/settings.py†L31-L38】
`DEBUG` defaults to false; truthy when `DJANGO_DEBUG` env is 1/true/yes/on. 【F:config/settings.py†L9-L12】
`SECRET_KEY` reads `DJANGO_SECRET_KEY` with fallback `change-me-devonly`. 【F:config/settings.py†L9-L10】
`ALLOWED_HOSTS` from `ALLOWED_HOSTS` env or defaults to `localhost,127.0.0.1,0.0.0.0`. 【F:config/settings.py†L13-L18】
Database: PostgreSQL using env vars `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` with defaults (`app`, `app`, `change-me-devonly`, `db`, `5432`). 【F:config/settings.py†L60-L69】
Session/CSRF/security flags from env: `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT` controlled by `DJANGO_SESSION_COOKIE_SECURE`, `DJANGO_CSRF_COOKIE_SECURE`, `DJANGO_SECURE_SSL_REDIRECT` (true when env equals "true"). 【F:config/settings.py†L100-L104】
Login/redirect URLs route through `/auth/signin` and `/`. 【F:config/settings.py†L95-L99】

# Docker/Compose
`docker-compose.yml` defines `db` (postgres:16-alpine, `.env` env_file, volume `db-data`, healthcheck via `pg_isready`) and `web` (builds local context, waits for db healthy, shares `.env`, exposes 8000). 【F:docker-compose.yml†L1-L27】
`Dockerfile` builds from `python:3.12-slim`, sets `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`, `DJANGO_SETTINGS_MODULE`, installs Django 4.2.11 and psycopg binary, runs as non-root user, and starts by running migrations, `seed_baseline`, then `runserver`. 【F:Dockerfile†L1-L17】
Startup ordering: `web` depends on `db` healthy before running entry command. 【F:docker-compose.yml†L16-L24】
`.env` bootstrap script copies `.env.example` if missing. 【F:scripts/bootstrap-env.sh†L1-L8】

# Database schema snapshot
Custom tables from migrations: `accounts_user` (email-unique auth model with Django auth relations). 【F:accounts/migrations/0001_initial.py†L16-L85】
`profiles_profile` with fields `user` (one-to-one), `display_name`, `currency`, `distance_unit`, `volume_unit`, `timezone`, `utc_offset_minutes`. 【F:profiles/migrations/0001_initial.py†L15-L28】【F:profiles/migrations/0002_profile_utc_offset_minutes.py†L9-L17】
`core_baselineseed` sentinel rows with `label`, `created_at`, `updated_at`. 【F:core/migrations/0001_initial.py†L14-L38】
Standard Django contrib apps add supporting tables such as `auth_group`, `auth_permission`, `django_content_type`, `django_session`, and `django_migrations`. 【F:config/settings.py†L20-L29】
No vehicle/fill-up domain tables exist yet; repo migrations only cover users, profiles, and baseline sentinel. 【F:accounts/migrations/0001_initial.py†L16-L85】【F:profiles/migrations/0001_initial.py†L15-L28】【F:core/migrations/0001_initial.py†L14-L38】

# Management commands
`core.management.commands.seed_baseline` ensures the `BaselineSeed` sentinel record exists each run, printing a success message. 【F:core/management/commands/seed_baseline.py†L1-L17】

# Environment variables
Application settings use `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `ALLOWED_HOSTS`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `DJANGO_SESSION_COOKIE_SECURE`, `DJANGO_CSRF_COOKIE_SECURE`, `DJANGO_SECURE_SSL_REDIRECT`. 【F:config/settings.py†L9-L104】
Runtime/Docker also set `DJANGO_SETTINGS_MODULE`, `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`. 【F:Dockerfile†L1-L17】
`.env.example` documents baseline values for local development. 【F:.env.example†L1-L9】

# Pages available
`/` returns plain text `success`, used as a smoke test. 【F:core/views.py†L12-L13】
`/health` returns JSON health with database connection, migration, and seeding status (503 on degraded). 【F:core/views.py†L16-L65】
`/auth/signup` renders signup form and accepts POST to create/log in new users with password policy hints. 【F:accounts/views.py†L13-L33】【F:templates/accounts/signup.html†L1-L54】
`/auth/signin` serves login form and signs users in, redirecting authenticated users. 【F:accounts/views.py†L35-L43】【F:templates/accounts/signin.html†L1-L43】
`/auth/signout` logs out and redirects to `/`. 【F:accounts/views.py†L45-L47】
`/settings` requires login, shows profile form with preview and messages, and persists preferences. 【F:profiles/views.py†L16-L64】【F:profiles/templates/profiles/settings.html†L1-L82】

# Known gaps (from plan)
Upcoming work includes vehicles CRUD, fill-up tracking, history views, metrics, statistics, legal/account tooling, reliability/security hardening, observability, and final polish per `task_plan.txt`. 【F:task_plan.txt†L1-L15】

# Notes
- Admin site is not enabled; enabling it would require adding `django.contrib.admin` and routing `/admin/`. 【F:config/settings.py†L20-L29】
- Health endpoint inspects migrations dynamically, so running without applying migrations will return HTTP 503. 【F:core/views.py†L16-L65】
- Docker entry command chains `migrate`, `seed_baseline`, and `runserver`, so container restarts reapply migrations and seed idempotently. 【F:Dockerfile†L1-L17】
- Compose relies on a shared `.env`; `scripts/bootstrap-env.sh` helps bootstrap local secrets. 【F:scripts/bootstrap-env.sh†L1-L8】
- No static asset pipeline or frontend build step exists yet; templates are minimal HTML only. 【F:templates/accounts/signup.html†L1-L54】【F:profiles/templates/profiles/settings.html†L1-L82】
- Profiles currently force timezone storage to `UTC`, using `utc_offset_minutes` only for future display adjustments. 【F:profiles/forms.py†L25-L70】
- Signals ensure every new user immediately gains a profile record, even before visiting `/settings`. 【F:profiles/signals.py†L1-L19】
- Unit conversion helpers support imperial previews while stored data remains metric. 【F:profiles/units.py†L1-L31】
- Task plan confirms future milestones for vehicles, fill-ups, analytics, and compliance work. 【F:task_plan.txt†L1-L15】

Summary
* Added `docs/project_overview_step03.md` capturing the repository snapshot requested in step 03. 【F:docs/project_overview_step03.md†L1-L156】

Testing
* ⚠️ Tests not run (documentation-only change).
