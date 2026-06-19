import { useEffect, useState } from 'react'
import { fetchDrivers, type Driver } from './api'
import './App.css'

const STATUS_LABELS: Record<Driver['status'], string> = {
  available: 'Available',
  on_trip: 'On trip',
  off_duty: 'Off duty',
}

function App() {
  const [drivers, setDrivers] = useState<Driver[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDrivers()
      .then(setDrivers)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : String(err)),
      )
      .finally(() => setLoading(false))
  }, [])

  return (
    <main className="app">
      <header>
        <h1>🚚 Truck Drivers Management</h1>
        <p className="subtitle">Django + DRF API · React + Vite frontend</p>
      </header>

      {loading && <p>Loading drivers…</p>}

      {error && (
        <div className="error">
          <p>Could not load drivers: {error}</p>
          <p className="hint">
            Make sure the Django backend is running on port 8000.
          </p>
        </div>
      )}

      {!loading && !error && drivers.length === 0 && (
        <div className="empty">
          <p>No drivers yet.</p>
          <p className="hint">
            Add one via the API at <code>/api/drivers/</code>.
          </p>
        </div>
      )}

      {drivers.length > 0 && (
        <table className="drivers">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>License</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {drivers.map((driver) => (
              <tr key={driver.id}>
                <td>{driver.full_name}</td>
                <td>{driver.email}</td>
                <td>{driver.license_number}</td>
                <td>
                  <span className={`status status--${driver.status}`}>
                    {STATUS_LABELS[driver.status]}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  )
}

export default App
