import { useState, type FormEvent } from 'react'
import type { TripInput } from '../api'
import LocationPicker from './LocationPicker'

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
    if (!current || !pickup || !dropoff) {
      alert('Please select all three locations')
      return
    }
    onPlan({
      current_location: current,
      pickup_location: pickup,
      dropoff_location: dropoff,
      current_cycle_used: Number(cycle) || 0,
    })
  }

  const allSet = current && pickup && dropoff

  return (
    <form className="trip-form" onSubmit={handleSubmit}>
      <div className="trip-form__grid">
        <LocationPicker
          label="Current location"
          placeholder="e.g. Los Angeles, CA or address"
          value={current}
          onSelect={(loc) => setCurrent(loc.label)}
          disabled={loading}
        />
        <LocationPicker
          label="Pickup location"
          placeholder="e.g. Dallas, TX or address"
          value={pickup}
          onSelect={(loc) => setPickup(loc.label)}
          disabled={loading}
        />
        <LocationPicker
          label="Dropoff location"
          placeholder="e.g. New York, NY or address"
          value={dropoff}
          onSelect={(loc) => setDropoff(loc.label)}
          disabled={loading}
        />
        <label>
          <span>Current cycle used (hrs)</span>
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
      <button type="submit" disabled={loading || !allSet}>
        {loading ? 'Planning…' : 'Plan trip'}
      </button>
    </form>
  )
}
