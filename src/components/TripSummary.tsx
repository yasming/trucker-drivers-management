import type { TripResult } from '../api'

function formatHours(h: number): string {
  const hrs = Math.floor(h)
  const mins = Math.round((h - hrs) * 60)
  return mins ? `${hrs}h ${mins}m` : `${hrs}h`
}

export default function TripSummary({ trip }: { trip: TripResult }) {
  const fuelStops = trip.stops.filter((s) => s.type === 'fuel').length
  const rests = trip.stops.filter((s) => s.type === 'rest').length

  const stats: { label: string; value: string }[] = [
    { label: 'Total distance', value: `${trip.total_distance_miles.toLocaleString()} mi` },
    { label: 'Drive time', value: formatHours(trip.total_drive_hours) },
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
