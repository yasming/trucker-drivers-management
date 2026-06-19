// Thin client for the Django REST API.
// In dev, requests to /api are proxied to the Django server (see vite.config.ts).

export interface Driver {
  id: number
  first_name: string
  last_name: string
  full_name: string
  email: string
  phone: string
  license_number: string
  license_expiry: string | null
  status: 'available' | 'on_trip' | 'off_duty'
  created_at: string
  updated_at: string
}

interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'

export async function fetchDrivers(): Promise<Driver[]> {
  const res = await fetch(`${API_BASE}/drivers/`)
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status} ${res.statusText}`)
  }
  const data: Paginated<Driver> = await res.json()
  return data.results
}

export async function fetchHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/health/`)
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.status}`)
  }
  return res.json()
}

// --- Trip planner ---

export type DutyStatus =
  | 'off_duty'
  | 'sleeper_berth'
  | 'driving'
  | 'on_duty_not_driving'

export type StopType =
  | 'start'
  | 'pickup'
  | 'dropoff'
  | 'fuel'
  | 'break'
  | 'rest'
  | 'restart'

export interface Stop {
  type: StopType
  label: string
  lat: number | null
  lon: number | null
  arrive: string | null
  depart: string | null
}

export interface LogSegment {
  status: DutyStatus
  start_hour: number
  end_hour: number
  label: string
}

export interface LogDay {
  date: string
  segments: LogSegment[]
  totals: Record<DutyStatus, number>
  driving_miles: number
  remarks: { time: string; label: string }[]
}

export interface TripResult {
  id: number
  current_location: string
  pickup_location: string
  dropoff_location: string
  current_cycle_used: number
  total_distance_miles: number
  total_drive_hours: number
  /** Full route as [lon, lat] pairs (GeoJSON order). */
  route_geometry: [number, number][]
  stops: Stop[]
  days: LogDay[]
  created_at: string
}

export interface TripInput {
  current_location: string
  pickup_location: string
  dropoff_location: string
  current_cycle_used: number
}

export async function planTrip(input: TripInput): Promise<TripResult> {
  const res = await fetch(`${API_BASE}/trips/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const data = await res.json()
      detail = data.detail ?? JSON.stringify(data)
    } catch {
      // response body was not JSON; keep the status text
    }
    throw new Error(detail)
  }
  return res.json()
}
