import { useState } from 'react'
import { planTrip, type TripInput, type TripResult } from './api'
import TripForm from './components/TripForm'
import TripSummary from './components/TripSummary'
import RouteMap from './components/RouteMap'
import LogSheet from './components/LogSheet'
import './App.css'

function App() {
  const [trip, setTrip] = useState<TripResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handlePlan(input: TripInput) {
    setLoading(true)
    setError(null)
    setTrip(null)
    try {
      setTrip(await planTrip(input))
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err))
      setTrip(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="app">
      <header className="app__header">
        <h1>Trucker Driver's Trip Planner</h1>
        <p className="subtitle">
          Enter a trip and get a routed map plus auto-filled FMCSA daily log sheets.
        </p>
      </header>

      <TripForm onPlan={handlePlan} loading={loading} />

      {loading && (
        <section className="planning-state" aria-live="polite" aria-label="Planning trip">
          <div className="planning-state__spinner" />
          <div>
            <strong>Planning trip</strong>
            <p>Calculating the route, required stops, rests, and daily log sheets.</p>
          </div>
        </section>
      )}

      {error && (
        <div className="error">
          <strong>Could not plan trip.</strong> {error}
        </div>
      )}

      {trip && (
        <>
          <TripSummary trip={trip} />
          <RouteMap trip={trip} />
          <section className="logs">
            <h2>Daily log sheets ({trip.days.length})</h2>
            {trip.days.map((day, i) => (
              <LogSheet
                key={`${day.date}-${i}`}
                day={day}
                index={i}
                from={trip.current_location}
                to={trip.dropoff_location}
              />
            ))}
          </section>
        </>
      )}
    </main>
  )
}

export default App
