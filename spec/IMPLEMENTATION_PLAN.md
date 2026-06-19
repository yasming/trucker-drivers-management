# ELD Trip Planner — Implementation Plan

## Context

The repo currently holds generic "truck drivers" CRUD scaffolding (Django 6 + DRF,
SQLite, no admin/auth per `CLAUDE.md`; React 19 + Vite + TS with a thin `api.ts`
and a drivers table). The real goal is the **Full Stack Dev Assessment**
(`spec/Full Stack Dev Assessment.docx`):

> Build an app that takes **trip details** as inputs and outputs **route
> instructions** and **draws ELD logs** as outputs.

- **Inputs:** Current location, Pickup location, Dropoff location, Current Cycle
  Used (Hrs).
- **Outputs:**
  1. A **map** showing the route with stops/rests (free map API).
  2. **Daily Log Sheets** drawn and filled out on the ELD grid shown in
     `spec/Blank Paper Log from Google Drive.png` — multiple sheets for longer trips.
- **Assumptions (given):** property-carrying driver, **70 hr / 8 day** cycle, no
  adverse conditions; **fuel at least every 1,000 miles**; **1 hour** each for
  pickup and drop-off.
- **Graded on:** accuracy of output (HOS math) **and** UI/UX quality. Deliverables:
  live hosted app (Vercel), 3–5 min Loom, GitHub repo, $100 reward.

### Confirmed design decisions

| Decision | Choice |
|---|---|
| Map / routing API | **OpenRouteService** (free key — geocoding + directions, `driving-hgv` truck profile) + **react-leaflet** on free OSM tiles for display |
| ELD log rendering | **Recreate the grid as an SVG** React component and draw the duty line + fill fields |
| Backend layout | **Extend the existing `drivers` app** (no new app) |
| Trip persistence | **Persist trips** to SQLite (enables history + re-openable results) |

### Data flow

```
inputs → geocode (ORS) → route (ORS driving-hgv) → HOS engine
       → { route geometry, stops, per-day logs } → persist (SQLite)
       → JSON → React (map + SVG log sheets)
```

---

## Phase 0 — Overview & architecture

- Backend: Django + DRF. Frontend: React + Vite + TypeScript.
- External: OpenRouteService (geocoding + directions), Leaflet/OSM tiles (display).
- The HOS/ELD engine is a pure Python module with no I/O so it can be unit-tested
  directly — accuracy is the most heavily graded part.

## Phase 1 — Backend setup & dependencies

1. Add `requests` to `backend/requirements.txt`; install into `.venv`
   (`cd backend && .venv/bin/python -m pip install -r requirements.txt`).
2. Add `ORS_API_KEY` to `backend/config/settings.py` (read from `os.environ`)
   and to `backend/.env.example`. Document obtaining a free key at
   openrouteservice.org.
3. Keep the `drivers` app; do **not** add admin/auth (per `CLAUDE.md`).

## Phase 2 — Data model: `Trip` (`backend/drivers/models.py`)

Inputs + JSON result fields so one request fully reconstructs the UI:

- `current_location`, `pickup_location`, `dropoff_location` — `CharField`
- `current_cycle_used` — `FloatField` (hours)
- `total_distance_miles`, `total_drive_hours` — `FloatField`
- `route_geometry` — `JSONField` (list of `[lon, lat]` for the map polyline)
- `stops` — `JSONField` (pickup / dropoff / fuel / break / rest markers, each with
  `lat`, `lon`, `type`, `label`, `arrive`/`depart`)
- `days` — `JSONField` (one entry per calendar day = one log sheet)
- `created_at` — auto

Then `makemigrations` + `migrate`.

## Phase 3 — Services (`backend/drivers/services/` package) — pure & testable

- **`geocoding.py`** — `geocode(query) -> (lat, lon, label)` via ORS Pelias
  `/geocode/search`.
- **`routing.py`** — `route([(lat, lon), ...]) -> RouteResult(distance_miles,
  duration_hours, geometry, legs)` via ORS Directions
  `/v2/directions/driving-hgv` (truck profile). Routes `current → pickup → dropoff`
  as two legs.
- **`hos.py` — the HOS / ELD engine** (no I/O; fully unit-tested). Constants at the
  top, sourced from the FMCSA HOS rules + assessment assumptions:

  | Constant | Value | Meaning |
  |---|---|---|
  | `MAX_DRIVE` | 11 h | driving limit per duty window |
  | `MAX_WINDOW` | 14 h | on-duty window after 10 h off |
  | `BREAK_AFTER_DRIVE` | 8 h | driving before a required break |
  | `BREAK` | 0.5 h | 30-minute break |
  | `DAILY_RESET` | 10 h | off-duty reset |
  | `CYCLE_LIMIT` | 70 h | on-duty hours / 8 days |
  | `RESTART` | 34 h | 34-hour restart |
  | `FUEL_INTERVAL` | 1000 mi | distance between fuel stops |
  | `FUEL_STOP` | 0.5 h | on-duty (not driving) |
  | `PICKUP` / `DROPOFF` | 1.0 h each | on-duty (not driving) |

  **Algorithm (timeline simulation):** start the clock at day-1 08:00 home-terminal
  time; initialise the cycle counter from `current_cycle_used`. Walk each driving
  leg in increments, inserting events as limits trigger:
  - 30-min break at 8 h cumulative driving;
  - 10-h rest when the 11-h driving limit **or** the 14-h window is reached;
  - 34-h restart when the 70-h cycle is reached;
  - 1-h pickup at the pickup node, 1-h dropoff at the end;
  - fuel stop every 1,000 miles.

  Emit a continuous list of segments
  `{ status ∈ off_duty | sleeper_berth | driving | on_duty_not_driving, start, end, label }`.
  Interpolate each non-driving stop's lat/lon along the route polyline by
  cumulative distance for map markers.

  **Split into days:** cut the segment timeline at midnight (home-terminal TZ);
  each day becomes `{ date, segments, totals_by_status (sum = 24 h), driving_miles,
  remarks[] }`.

## Phase 4 — API (DRF) (`backend/drivers/`)

- `serializers.py`: `TripInputSerializer` (4 inputs) + `TripSerializer` (full result).
- `views.py`: `TripViewSet` (ModelViewSet). `create()` runs the pipeline
  (geocode → route → `plan_logs`), saves a `Trip`, and returns the full serialized
  result. `list` / `retrieve` expose history. ORS failures map to clear 400/502
  responses.
- `urls.py`: register `trips` on the existing `DefaultRouter` →
  `POST/GET /api/trips/` and `GET /api/trips/{id}/`. Keep existing `drivers` routes.

## Phase 5 — Backend tests (`backend/drivers/tests.py`)

Follow `ai/guidelines/testing.md` — write tests in `tests.py`, run with
`manage.py test` (never ad-hoc `python -c` clients). HOS engine unit tests call
`plan_logs` directly (no HTTP):

- short trip → single day; totals sum to 24 h; pickup + dropoff hours present;
- trip crossing 8 h driving → a 30-min break is inserted;
- multi-day trip → ≥2 day sheets, each summing to 24 h, 10-h rests inserted;
- high `current_cycle_used` (e.g. 68 h) → a 34-h restart appears;
- distance > 1,000 mi → fuel stop(s) inserted at the right cadence.

Endpoint test: patch the `geocoding` / `routing` services, `POST /api/trips/`,
assert the response shape and that a `Trip` row is persisted.

## Phase 6 — Frontend deps & API client

1. `npm i leaflet react-leaflet` and `npm i -D @types/leaflet`; import Leaflet CSS.
2. `frontend/src/api.ts`: add `planTrip(input): Promise<TripResult>` plus the
   `TripResult` / `Stop` / `LogDay` types mirroring the serializer.

## Phase 7 — Frontend components (`frontend/src/components/`)

- `TripForm.tsx` — 4 inputs (current, pickup, dropoff, current cycle hrs) + submit;
  loading + error states.
- `RouteMap.tsx` — react-leaflet `MapContainer` + OSM `TileLayer` + `Polyline`
  (route) + typed `Marker`s (pickup, dropoff, fuel, break, rest) with popups;
  fit bounds to the route.
- `TripSummary.tsx` — total distance, total drive time, #days, #fuel stops, #rests.
- `LogSheet.tsx` + an SVG grid — recreate the daily-log grid from the PNG
  (24 h × 4 duty rows), draw the stepped duty line from a day's segments, fill the
  per-status hour totals, driving miles, date header, and remarks. One `LogSheet`
  per day → **multiple sheets render automatically for long trips.**
- `App.tsx` — replace the drivers-table demo with: header, `TripForm`, then on
  success `TripSummary` + `RouteMap` + the list of `LogSheet`s.
- CSS for a clean, aesthetic layout (UI/UX is weighted heavily).

## Phase 8 — Deployment & deliverables

- **Frontend → Vercel:** build `frontend`, set `VITE_API_BASE` to the deployed
  backend URL.
- **Backend → Render / Railway / Fly:** gunicorn + Django; set `ORS_API_KEY`,
  `DJANGO_ALLOWED_HOSTS`, and `DJANGO_CORS_ALLOWED_ORIGINS` (the Vercel domain).
  SQLite is acceptable for the demo (or swap to managed Postgres).
- Deliverables checklist: live URL, 3–5 min Loom (app + code walkthrough), GitHub link.

## Phase 9 — Verification (end-to-end)

- Backend: `cd backend && .venv/bin/python manage.py test` — HOS + endpoint tests pass.
- Run both servers; open `http://localhost:5173`.
- **Short trip** (same metro) → one log sheet, totals = 24 h.
- **Long trip** (e.g. Los Angeles → New York) → route renders, fuel stops every
  ~1,000 mi, 10-h rests, **multiple** log sheets each summing to 24 h.
- Confirm markers/popups and the drawn duty line match the computed stops/times.

---

## Critical files

- **Reference:** `spec/Full Stack Dev Assessment.docx`,
  `spec/Blank Paper Log from Google Drive.png`,
  `spec/FMCSA HOS Drivers Guide Apr 28 2022.pdf`, `ai/guidelines/testing.md`,
  `CLAUDE.md`.
- **Backend (to create/modify):** `backend/drivers/models.py`,
  `backend/drivers/{serializers,views,urls,tests}.py`,
  `backend/drivers/services/{geocoding,routing,hos}.py` (new),
  `backend/config/settings.py`, `backend/requirements.txt`, `backend/.env.example`.
- **Frontend (to create/modify):** `frontend/src/{api.ts,App.tsx}`,
  `frontend/src/components/*`, `frontend/package.json`.
