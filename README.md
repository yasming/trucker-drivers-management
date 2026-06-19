# Truck Drivers Management

A full-stack application for managing truck drivers, built with:

- **Backend:** Python 3.14 · Django 6 · Django REST Framework
- **Frontend:** React 19 · Vite · TypeScript

## Project layout

```
truck-drivers-managment/
├── .tool-versions        # pins Python 3.14.4 (asdf)
├── backend/              # Django project + DRF API
│   ├── config/           # Django settings, URLs, WSGI/ASGI
│   ├── drivers/          # "drivers" app: Driver model, API, admin
│   ├── manage.py
│   └── requirements.txt
└── frontend/             # React + Vite + TypeScript app
    └── src/
```

## Prerequisites

- [asdf](https://asdf-vm.com/) with Python **3.14.4** installed (`asdf install python 3.14.4`)
- Node.js 20+ (22 or 24 recommended)

## Backend setup

```bash
cd backend
python -m venv .venv                 # uses Python 3.14.4 via .tool-versions
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env                 # optional: customize settings
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser   # optional, for /admin
.venv/bin/python manage.py runserver         # http://127.0.0.1:8000
```

API endpoints:

- `GET /api/health/` — health check
- `GET/POST /api/drivers/` — list / create drivers
- `GET/PUT/PATCH/DELETE /api/drivers/{id}/` — retrieve / update / delete
- `/admin/` — Django admin

## Frontend setup

```bash
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

The Vite dev server proxies `/api/*` to the Django backend on port 8000, so run
both servers during development.

## Build the frontend for production

```bash
cd frontend
npm run build
```
