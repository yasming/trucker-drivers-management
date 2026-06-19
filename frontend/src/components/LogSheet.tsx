import type { DutyStatus, LogDay } from '../api'

const ROWS: { key: DutyStatus; label: string }[] = [
  { key: 'off_duty', label: '1. Off Duty' },
  { key: 'sleeper_berth', label: '2. Sleeper Berth' },
  { key: 'driving', label: '3. Driving' },
  { key: 'on_duty_not_driving', label: '4. On Duty (not driving)' },
]
const ROW_INDEX: Record<DutyStatus, number> = {
  off_duty: 0,
  sleeper_berth: 1,
  driving: 2,
  on_duty_not_driving: 3,
}

// SVG layout (viewBox units).
const LEFT = 176
const TOP = 48
const HOUR_W = 30
const ROW_H = 40
const GRID_W = HOUR_W * 24
const RIGHT_W = 66
const W = LEFT + GRID_W + RIGHT_W
const H = TOP + ROW_H * 4 + 22

const X = (h: number) => LEFT + h * HOUR_W
const rowTop = (i: number) => TOP + i * ROW_H
const rowMid = (i: number) => TOP + i * ROW_H + ROW_H / 2

function hhmm(h: number): string {
  const total = Math.round(h * 60)
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`
}

function hourLabel(h: number): string {
  if (h === 0 || h === 24) return 'M'
  if (h === 12) return 'N'
  return String(h % 12 === 0 ? 12 : h % 12)
}

interface Props {
  day: LogDay
  index: number
  from: string
  to: string
}

export default function LogSheet({ day, index, from, to }: Props) {
  const hours = Array.from({ length: 25 }, (_, h) => h)

  // The continuous duty line: two points per segment (start, end) at its row.
  const points = day.segments
    .flatMap((s) => {
      const y = rowMid(ROW_INDEX[s.status])
      return [`${X(s.start_hour)},${y}`, `${X(s.end_hour)},${y}`]
    })
    .join(' ')

  return (
    <article className="logsheet">
      <div className="logsheet__head">
        <div className="logsheet__title">
          <span className="logsheet__no">Log #{index + 1}</span>
          <strong>{day.date}</strong>
        </div>
        <div className="logsheet__route">
          {from} → {to}
        </div>
        <div className="logsheet__miles">
          <span>Total miles driving today</span>
          <strong>{Math.round(day.driving_miles).toLocaleString()}</strong>
        </div>
      </div>

      <svg
        className="logsheet__grid"
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`Daily log grid for ${day.date}`}
      >
        <text x={LEFT + GRID_W / 2} y={16} className="lg-axis">
          Hour of day (home terminal time)
        </text>
        <text x={LEFT + GRID_W + RIGHT_W - 6} y={TOP - 16} className="lg-total-head">
          Total
        </text>
        {hours.map((h) => (
          <text key={`hl${h}`} x={X(h)} y={TOP - 14} className="lg-hour">
            {hourLabel(h)}
          </text>
        ))}

        {/* Rows: zebra background, label, total, and quarter-hour ticks. */}
        {ROWS.map((r, i) => (
          <g key={r.key}>
            <rect
              x={LEFT}
              y={rowTop(i)}
              width={GRID_W}
              height={ROW_H}
              className={`lg-rowbg lg-rowbg--${i % 2}`}
            />
            <text x={LEFT - 10} y={rowMid(i) + 4} className="lg-rowlabel">
              {r.label}
            </text>
            <text x={LEFT + GRID_W + RIGHT_W - 6} y={rowMid(i) + 4} className="lg-total">
              {hhmm(day.totals[r.key])}
            </text>
            {Array.from({ length: 24 }).flatMap((_, h) =>
              [0.25, 0.5, 0.75].map((q) => (
                <line
                  key={`tk${i}-${h}-${q}`}
                  x1={X(h + q)}
                  y1={rowTop(i)}
                  x2={X(h + q)}
                  y2={rowTop(i) + (q === 0.5 ? 12 : 6)}
                  className="lg-tick"
                />
              )),
            )}
          </g>
        ))}

        {/* Hour gridlines + row separators + frame. */}
        {hours.map((h) => (
          <line key={`v${h}`} x1={X(h)} y1={TOP} x2={X(h)} y2={TOP + ROW_H * 4} className="lg-vline" />
        ))}
        {[0, 1, 2, 3, 4].map((i) => (
          <line
            key={`hln${i}`}
            x1={LEFT}
            y1={rowTop(i)}
            x2={LEFT + GRID_W}
            y2={rowTop(i)}
            className="lg-hline"
          />
        ))}
        <rect x={LEFT} y={TOP} width={GRID_W} height={ROW_H * 4} className="lg-frame" />
        <line
          x1={LEFT + GRID_W}
          y1={TOP}
          x2={LEFT + GRID_W}
          y2={TOP + ROW_H * 4}
          className="lg-vline lg-vline--strong"
        />

        {/* The duty-status step line. */}
        <polyline points={points} className="lg-duty" />
      </svg>

      {day.remarks.length > 0 && (
        <div className="logsheet__remarks">
          <h4>Remarks</h4>
          <ul>
            {day.remarks.map((r, i) => (
              <li key={i}>
                <span className="logsheet__time">{r.time}</span> {r.label}
              </li>
            ))}
          </ul>
        </div>
      )}
    </article>
  )
}
