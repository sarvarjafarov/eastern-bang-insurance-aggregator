# eastern-bang-insurance-aggregator

This repository hosts a Django project bootstrap for the Eastern Bang Insurance Aggregator. It solves the problem of comparing and selecting travel/health insurance plans for international students by centralizing plan data, providing saved packs, reviews, documents, and analytics (including an A/B test page) in one place.

## Getting Started

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The project entry point is `manage.py` and default settings live under `insurance_aggregator/settings.py`.

## Environment variables

The app reads configuration from the environment with sensible local defaults:

- `DJANGO_SECRET_KEY`: required in production.
- `DJANGO_DEBUG`: set to `False` for Render (`True` by default locally).
- `DJANGO_ALLOWED_HOSTS`: comma-separated hostnames. When unset, local hosts are used and Render falls back to `RENDER_EXTERNAL_HOSTNAME`.
- `DATABASE_URL`: SQLite by default; Render injects the Postgres URL automatically via `render.yaml`.
- `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, `DJANGO_SUPERUSER_EMAIL`: optional helpers for non-interactive admin creation (see below).
- `TRAFFIC_API_KEY`: optional shared secret for the `/api/traffic` ingest endpoint. Leave empty locally to disable the check.
- `TEAM_NICKNAMES`: comma-separated list of nicknames to display on the standardized analytics page (defaults to `cheerful-newt, careful-deer, silly-elephant, clever-crocodile, careful-deer`).
- `GA_MEASUREMENT_ID`: optional Google Analytics measurement ID for the standardized analytics page.
- `YANDEX_METRICA_ID`: optional Yandex Metrica counter ID for the standardized analytics page.

Copy `.env.example` to `.env` for local overrides if you are using a virtualenv.

## Deploying to Render.com

The repo includes a `Procfile` and a `render.yaml` blueprint. To deploy:

1. Push this repository to GitHub.
2. In Render, create a new Blueprint and point it at the repository.
3. Render provisions the Postgres database defined in `render.yaml`, installs dependencies, runs `collectstatic`, and applies migrations before every deploy.
4. Set `DJANGO_SECRET_KEY` to a strong value (Render will generate one automatically from the blueprint) and keep `DJANGO_DEBUG=False`.
5. Populate `DJANGO_SUPERUSER_*` variables with the credentials you want for the initial admin account. The password should be stored as a secret in Render.

The service starts with `gunicorn insurance_aggregator.wsgi:application` and serves static assets via Whitenoise. Collect static assets with `python manage.py collectstatic --noinput` before each deployment; this step is already part of the Render build command.

### Deployment process

- Branching: develop on feature branches; open a PR; get at least one review; merge to `main`.
- Staging deploy: staging service tracks `main` (or trigger manually). Render build command runs `pip install -r requirements.txt && python manage.py collectstatic --noinput`; start command runs `python manage.py migrate --noinput && gunicorn insurance_aggregator.wsgi:application`.
- Smoke test staging: visit `/`, `/ef1ca11/`, and run `python manage.py test` locally if needed.
- Production deploy: trigger after staging passes; same commands as above. URLs documented below.

## Admin access

The Django admin lives at `/admin/`.

- Locally, create a superuser with `python manage.py createsuperuser` or populate the `DJANGO_SUPERUSER_*` variables and run `python manage.py create_default_superuser`.
- In Render, the deploy hook runs `python manage.py create_default_superuser` automatically; make sure `DJANGO_SUPERUSER_USERNAME` and `DJANGO_SUPERUSER_PASSWORD` are set in the service settings.
- The blueprint and `.env.example` currently seed the admin account with username `admin` and password `admin`. Change these values immediately in production to keep the instance secure.

## Traffic ingest endpoint

External systems can send traffic events to `POST /api/traffic/` with a JSON body:

```bash
curl -X POST http://localhost:8000/api/traffic/ \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: $TRAFFIC_API_KEY" \
  -d '{"event": "acquisition", "source": "kyle-system", "count": 5, "date": "2024-11-21"}'
```

- `event` defaults to `acquisition` if omitted.
- `source` (optional) is stored under the `source:` metric prefix for dashboard breakdowns.
- `count` defaults to `1` and must be a positive integer.
- `date` (optional) lets you backfill in `YYYY-MM-DD` format; otherwise, today is used.
- If `TRAFFIC_API_KEY` is set, requests must provide it in the `X-Api-Key` header.

## Standardized analytics endpoint

A public A/B test page lives at `/ef1ca11/` (first 7 chars of `sha1("eastern-bang")`). It lists your configured team nicknames and renders a button with id `abtest` whose label alternates between “kudos” and “thanks”; page views and variant assignments are recorded via the internal metrics system, and you can also attach Google Analytics or Yandex Metrica by setting `GA_MEASUREMENT_ID` or `YANDEX_METRICA_ID`.

## Environments

- Production (public): `https://eastern-bang-insurance-aggregator.onrender.com/` (Render web service with managed Postgres via `DATABASE_URL`).
- Staging (public, for pre-prod testing): `https://eastern-bang-insurance-aggregator-staging.onrender.com/` (separate Render service/DB). Include `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, and analytics IDs (`GA_MEASUREMENT_ID`, `YANDEX_METRICA_ID`) as needed.

## Development

- Install base deps: `pip install -r requirements.txt`
- Install dev tools (lint): `pip install -r requirements-dev.txt`
- Lint: `ruff check .` (auto-fix: `ruff check . --fix`)
- Tests: `python manage.py test`

## Technology stack

- Backend: Python, Django 4, Gunicorn, Whitenoise
- Database: Postgres (Render) / SQLite locally
- Analytics: Internal metrics + optional GA/Yandex (env-driven)
- Frontend: Django templates + Tailwind CDN

## A/B test endpoint

- URL: `/ef1ca11/` (first 7 chars of `sha1("eastern-bang")`).
- Behavior: lists team nicknames, shows button id `abtest` with variant `kudos`/`thanks`.
- Tracking: internal metrics for page views/variants and button clicks; optional GA/Yandex via env (`GA_MEASUREMENT_ID`, `YANDEX_METRICA_ID`).
- Framing: `X-Frame-Options` allows Metrica click maps; ensure analytics IDs are set.

## Accounts, profiles, saved plans

- Signup/login/logout: `/account/signup/`, `/account/login/`, `/account/logout/`
- Profile: `/account/profile/`
- Saved plans: `/account/packs/` with create/edit/detail pages (legacy aliases `/account/deals/...`). Access is restricted to the signed-in user’s own records. Profile includes preferences (member type, city, budget, providers, deductible preference, language, communication opts) that prefill the browse experience. Recent activity and documents are shown on the profile.
- Documents: `/account/documents/` to track verification/claims links with status.
- Notifications: `/account/notifications/` to view and mark alerts as read.
- Support tickets: `/account/support/` to open and track support requests.
- Security: `/account/security/` to log out or delete the account.
- Billing: `/account/billing/` to add and view billing records.
- Onboarding checklist: visible on `/account/profile/` showing progress across preferences, saved plans, add-ons, reviews, documents, support, and billing steps.

## Team

- Sarvar Jafarov — implementation, analytics/A/B setup, deployment.
- Add additional contributors and roles here as needed.

## API

- Traffic ingest: `POST /api/traffic/` (see above).
- A/B test click tracking: `POST /ef1ca11/click/` with JSON `{"variant": "kudos"|"thanks"}`.

## Sprint documentation

All sprint planning/review/retro docs live under `docs/sprints/` (see that directory for the latest sprint notes).
