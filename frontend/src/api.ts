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
