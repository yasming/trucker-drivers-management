# CLAUDE.md

Guidance for working in this repo.

## Project layout

- `backend/` — Django + Django REST Framework API (SQLite, `.venv/`).
- `frontend/` — React + Vite app (runs on http://localhost:5173, proxies `/api`
  to the backend on http://127.0.0.1:8000).

## Guidelines — read before working

Always read the relevant file under `ai/guidelines/` before starting:

- [ai/guidelines/testing.md](ai/guidelines/testing.md) — how to test the API.
  **Read this before writing or running any tests.** In short: never use ad-hoc
  inline `python -c` test-client scripts (they fail with
  `Invalid HTTP_HOST header: 'testserver'`); write tests in
  `backend/drivers/tests.py` and run `manage.py test`.

## Backend conventions

- This API does not use `django.contrib.admin` or `django.contrib.auth` — no
  admin routes, no `User` model, no login/permissions/groups. Don't reintroduce
  them unless asked.
- Run management commands via the venv, e.g.
  `cd backend && .venv/bin/python manage.py <cmd>`.
