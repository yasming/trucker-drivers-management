# ELD Trip Planner

A full-stack app for planning truck trips with FMCSA Hours of Service compliance, route maps, and auto-filled daily log sheets.

Built as a **single deployable unit:**
- **Backend:** Python 3.14 · Django 6 · Django REST Framework
- **Frontend:** React 19 · Vite · TypeScript (served by Django)

## Project layout

```
project-root/
├── config/              # Django settings, URLs, WSGI/ASGI
├── drivers/             # Trip planner API + Hours of Service engine
├── src/                 # React app (TypeScript)
├── static/              # Built React SPA + assets (Django serves this)
├── manage.py
├── requirements.txt     # Python dependencies
├── package.json         # Node dependencies
└── vite.config.ts       # Vite build config
```

## Prerequisites

- [asdf](https://asdf-vm.com/) with Python **3.14.4** installed
- Node.js 20+ (22 or 24 recommended)

## Setup

```bash
# Install Python dependencies
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

# Install Node dependencies
npm install
```

Planned trips are kept in process memory. No database setup or migrations are
required; restarting Django clears stored trips.

## Development

```bash
# Terminal 1: Start Django (runs on http://127.0.0.1:8000)
.venv/bin/python manage.py runserver

# Terminal 2: Start Vite dev server (runs on http://localhost:5173)
npm run dev
```

Vite proxies `/api/*` to Django, so the React app can call the API during development.

## Production build

```bash
npm run build        # Builds React into ./static/
```

Django automatically serves the built React app from `static/` for any non-API route,
enabling client-side routing. Deploy the entire project as one Python app.
