# Contributing / Workflow

## Branching
- Create a feature branch for each change: `feature/<name>`, `fix/<name>`, `chore/<name>`, `test/<name>`.
- Avoid committing directly to `main`; merge via PR.

## Commits
- Keep commits small and focused.
- Use clear, imperative messages (e.g., `add abtest click tracking endpoint`, `chore: add ruff config`, `test: add analytics unit tests`).
- No secrets in commits; configuration lives in environment variables.

## Pull Requests
- Open a PR for every branch.
- Include what changed, how to test, and any risks.
- Get at least one review before merging.

## Lint & Tests
- Lint: `ruff check .`
- Tests: `python manage.py test` (venv active)

## Ignored files
- `.gitignore` covers venvs, pyc files, `.env`, build artifacts, and local SQLite DBs. Do not add secrets or local env files to git.
