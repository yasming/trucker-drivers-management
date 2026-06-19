import type { TripResult } from '../api'

function formatHours(h: number): string {
  const hrs = Math.floor(h)
  const mins = Math.round((h - hrs) * 60)
  return mins ? `${hrs}h ${mins}m` : `${hrs}h`
}

function formatDateTime(value: string | null): string {
  if (!value) return 'Not available'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Not available'

  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(date)
}

export default function TripSummary({ trip }: { trip: TripResult }) {
  const fuelStops = trip.stops.filter((s) => s.type === 'fuel').length
  const rests = trip.stops.filter((s) => s.type === 'rest').length
  const dropoff = trip.stops.findLast((s) => s.type === 'dropoff')
  const finalStop = trip.stops.at(-1)
  const estimatedFinish = dropoff?.depart ?? finalStop?.depart ?? finalStop?.arrive ?? null

  const stats: { label: string; value: string }[] = [
    { label: 'Total distance', value: `${trip.total_distance_miles.toLocaleString()} mi` },
    { label: 'Drive time', value: formatHours(trip.total_drive_hours) },
    { label: 'Estimated trip finish', value: formatDateTime(estimatedFinish) },
    { label: 'Days / log sheets', value: String(trip.days.length) },
    { label: 'Fuel stops', value: String(fuelStops) },
    { label: '10-hour rests', value: String(rests) },
    { label: 'Cycle used at start', value: `${trip.current_cycle_used} h` },
  ]

  return (
    <section className="summary" aria-label="Trip summary">
      {stats.map((s) => (
        <div className="stat" key={s.label}>
          <div className="stat__value">{s.value}</div>
          <div className="stat__label">{s.label}</div>
        </div>
      ))}
    </section>
  )
}
