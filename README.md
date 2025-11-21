# eastern-bang-insurance-aggregator

This repository hosts a Django project bootstrap for the Eastern Bang Insurance Aggregator.

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

Copy `.env.example` to `.env` for local overrides if you are using a virtualenv.

## Deploying to Render.com

The repo includes a `Procfile` and a `render.yaml` blueprint. To deploy:

1. Push this repository to GitHub.
2. In Render, create a new Blueprint and point it at the repository.
3. Render provisions the Postgres database defined in `render.yaml`, installs dependencies, runs `collectstatic`, and applies migrations before every deploy.
4. Set `DJANGO_SECRET_KEY` to a strong value (Render will generate one automatically from the blueprint) and keep `DJANGO_DEBUG=False`.
5. Populate `DJANGO_SUPERUSER_*` variables with the credentials you want for the initial admin account. The password should be stored as a secret in Render.

The service starts with `gunicorn insurance_aggregator.wsgi:application` and serves static assets via Whitenoise. Collect static assets with `python manage.py collectstatic --noinput` before each deployment; this step is already part of the Render build command.

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
