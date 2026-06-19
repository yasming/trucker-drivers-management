import { useEffect } from 'react'
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { StopType, TripResult } from '../api'

const STOP_STYLE: Record<StopType, { color: string; glyph: string }> = {
  start: { color: '#16a34a', glyph: 'S' },
  pickup: { color: '#2563eb', glyph: 'P' },
  dropoff: { color: '#dc2626', glyph: 'D' },
  fuel: { color: '#f59e0b', glyph: '⛽' },
  break: { color: '#7c3aed', glyph: '☕' },
  rest: { color: '#0ea5e9', glyph: '🛏' },
  restart: { color: '#475569', glyph: '⏸' },
}

function stopIcon(type: StopType): L.DivIcon {
  const s = STOP_STYLE[type]
  return L.divIcon({
    className: 'stop-marker',
    html: `<span style="background:${s.color}">${s.glyph}</span>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
    popupAnchor: [0, -14],
  })
}

function FitBounds({ positions }: { positions: [number, number][] }) {
  const map = useMap()
  useEffect(() => {
    if (positions.length > 1) {
      map.fitBounds(positions, { padding: [30, 30] })
    } else if (positions.length === 1) {
      map.setView(positions[0], 9)
    }
  }, [positions, map])
  return null
}

export default function RouteMap({ trip }: { trip: TripResult }) {
  // Backend geometry is [lon, lat]; Leaflet wants [lat, lng].
  const line: [number, number][] = trip.route_geometry.map(([lon, lat]) => [lat, lon])
  const center: [number, number] = line[0] ?? [39.5, -98.35]

  return (
    <section className="route-map" aria-label="Route map">
      <MapContainer className="route-map__canvas" center={center} zoom={5} scrollWheelZoom>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {line.length > 1 && (
          <Polyline positions={line} pathOptions={{ color: '#aa3bff', weight: 4, opacity: 0.85 }} />
        )}
        {trip.stops
          .filter((s) => s.lat != null && s.lon != null)
          .map((s, i) => (
            <Marker key={i} position={[s.lat as number, s.lon as number]} icon={stopIcon(s.type)}>
              <Popup>
                <strong>{s.label}</strong>
                {s.arrive && (
                  <div>
                    {s.arrive.replace('T', ' ')}
                    {s.depart && s.depart !== s.arrive ? ` → ${s.depart.replace('T', ' ')}` : ''}
                  </div>
                )}
              </Popup>
            </Marker>
          ))}
        <FitBounds positions={line} />
      </MapContainer>
    </section>
  )
}
