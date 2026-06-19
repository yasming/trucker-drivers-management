import { useState, type FormEvent } from 'react'
import type { TripInput } from '../api'

interface Props {
  onPlan: (input: TripInput) => void
  loading: boolean
}

export default function TripForm({ onPlan, loading }: Props) {
  const [current, setCurrent] = useState('')
  const [pickup, setPickup] = useState('')
  const [dropoff, setDropoff] = useState('')
  const [cycle, setCycle] = useState('0')

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    onPlan({
      current_location: current.trim(),
      pickup_location: pickup.trim(),
      dropoff_location: dropoff.trim(),
      current_cycle_used: Number(cycle) || 0,
    })
  }

  return (
    <form className="trip-form" onSubmit={handleSubmit}>
      <div className="trip-form__grid">
        <label>
          Current location
          <input
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            placeholder="e.g. Los Angeles, CA"
            required
          />
        </label>
        <label>
          Pickup location
          <input
            value={pickup}
            onChange={(e) => setPickup(e.target.value)}
            placeholder="e.g. Dallas, TX"
            required
          />
        </label>
        <label>
          Dropoff location
          <input
            value={dropoff}
            onChange={(e) => setDropoff(e.target.value)}
            placeholder="e.g. New York, NY"
            required
          />
        </label>
        <label>
          Current cycle used (hrs)
          <input
            type="number"
            min="0"
            max="70"
            step="0.5"
            value={cycle}
            onChange={(e) => setCycle(e.target.value)}
            required
          />
        </label>
      </div>
      <button type="submit" disabled={loading}>
        {loading ? 'Planning…' : 'Plan trip'}
      </button>
    </form>
  )
}
