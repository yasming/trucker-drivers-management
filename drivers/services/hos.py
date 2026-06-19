"""Hours-of-Service (HOS) / ELD log engine.

Given the driving legs of a trip and how many cycle hours the driver has
already used, this module simulates the trip minute-by-minute applying the
FMCSA Hours-of-Service rules for a property-carrying driver on the 70hr/8day
cycle, then emits:

  * a flat list of duty-status ``stops`` (pickup, dropoff, fuel, break, rest)
    with interpolated map coordinates, and
  * ``days`` — one entry per calendar day, ready to draw as a daily log sheet
    (24h x 4 duty rows), with per-status totals that sum to 24h.

The module is pure (no I/O) so the rules can be unit-tested directly.

Rules applied (property-carrying, 70/8, no adverse conditions):
  * 11-hour driving limit per duty window.
  * 14-hour on-duty window after 10 consecutive hours off.
  * 30-minute break required after 8 cumulative hours of driving.
  * 60/70-hour cycle limit (here: 70 hours / 8 days), reset by a 34-hour restart.
Assessment assumptions:
  * Fuel at least once every 1,000 miles.
  * 1 hour each for pickup and drop-off (on-duty, not driving).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# Duty statuses — these match the four rows of the paper ELD grid.
OFF_DUTY = "off_duty"
SLEEPER = "sleeper_berth"
DRIVING = "driving"
ON_DUTY = "on_duty_not_driving"

# --- FMCSA HOS limits (hours) ---
MAX_DRIVE_HOURS = 11.0          # driving limit per duty window
MAX_WINDOW_HOURS = 14.0         # on-duty window after a 10h reset
BREAK_AFTER_DRIVE_HOURS = 8.0   # driving allowed before a 30-min break
BREAK_HOURS = 0.5               # the 30-minute break
DAILY_RESET_HOURS = 10.0        # off-duty reset of the daily limits
CYCLE_LIMIT_HOURS = 70.0        # on-duty hours allowed per 8 days
RESTART_HOURS = 34.0            # 34-hour restart of the cycle

# --- Assessment assumptions ---
FUEL_INTERVAL_MILES = 1000.0    # fuel at least every 1,000 miles
FUEL_HOURS = 0.5                # time spent fueling (on duty, not driving)
PICKUP_HOURS = 1.0
DROPOFF_HOURS = 1.0

EPS = 1e-6
DEFAULT_START_HOUR = 8          # driver comes on duty at 08:00
EARTH_RADIUS_MILES = 3958.7613


@dataclass
class Leg:
    """One driving leg between two consecutive waypoints."""

    distance_miles: float
    duration_hours: float


@dataclass
class _Segment:
    status: str
    start: datetime
    end: datetime
    label: str = ""
    miles: float = 0.0


@dataclass
class _State:
    now: datetime
    cycle_used: float            # on-duty hours used in the 70/8 cycle
    drive_in_window: float = 0.0  # driving hours since last 10h reset (11h limit)
    drive_since_break: float = 0.0  # driving hours since last break (8h rule)
    window_start: datetime | None = None  # start of current 14h window
    miles_since_fuel: float = 0.0
    cumulative_miles: float = 0.0
    segments: list[_Segment] = field(default_factory=list)
    stops: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Geometry helpers — interpolate a stop's coordinates along the route polyline.
# ---------------------------------------------------------------------------
def _haversine(a: list[float], b: list[float]) -> float:
    """Great-circle distance in miles between two [lon, lat] points."""
    lon1, lat1 = a[0], a[1]
    lon2, lat2 = b[0], b[1]
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(h))


def _point_at(geometry: list, miles: float, total_miles: float) -> tuple:
    """Return ``(lat, lon)`` at ``miles`` along ``geometry`` (list of [lon, lat])."""
    if not geometry:
        return None, None
    if len(geometry) == 1:
        lon, lat = geometry[0][:2]
        return round(lat, 5), round(lon, 5)

    fraction = 0.0 if total_miles <= 0 else min(max(miles / total_miles, 0.0), 1.0)
    cumulative = [0.0]
    for i in range(1, len(geometry)):
        cumulative.append(cumulative[-1] + _haversine(geometry[i - 1], geometry[i]))
    target = fraction * cumulative[-1]

    for i in range(1, len(geometry)):
        if cumulative[i] >= target:
            seg_len = cumulative[i] - cumulative[i - 1]
            t = 0.0 if seg_len <= 0 else (target - cumulative[i - 1]) / seg_len
            lon1, lat1 = geometry[i - 1][:2]
            lon2, lat2 = geometry[i][:2]
            return round(lat1 + (lat2 - lat1) * t, 5), round(lon1 + (lon2 - lon1) * t, 5)

    lon, lat = geometry[-1][:2]
    return round(lat, 5), round(lon, 5)


# ---------------------------------------------------------------------------
# State mutators — each appends one segment and advances the clock/counters.
# ---------------------------------------------------------------------------
def _window_used(state: _State) -> float:
    if state.window_start is None:
        return 0.0
    return (state.now - state.window_start).total_seconds() / 3600.0


def _add_stop(state: _State, stop_type: str, label: str, geometry: list, total_miles: float) -> None:
    seg = state.segments[-1]
    lat, lon = _point_at(geometry, state.cumulative_miles, total_miles)
    state.stops.append(
        {
            "type": stop_type,
            "label": label,
            "lat": lat,
            "lon": lon,
            "arrive": seg.start.isoformat(timespec="minutes"),
            "depart": seg.end.isoformat(timespec="minutes"),
        }
    )


def _drive(state: _State, hours: float, miles: float) -> None:
    start = state.now
    end = start + timedelta(hours=hours)
    if state.window_start is None:
        state.window_start = start
    state.segments.append(_Segment(DRIVING, start, end, "Driving", miles))
    state.now = end
    state.drive_in_window += hours
    state.drive_since_break += hours
    state.cycle_used += hours
    state.miles_since_fuel += miles
    state.cumulative_miles += miles


def _on_duty(state: _State, hours: float, label: str, stop_type: str,
             geometry: list, total_miles: float) -> None:
    start = state.now
    end = start + timedelta(hours=hours)
    if state.window_start is None:
        state.window_start = start
    state.segments.append(_Segment(ON_DUTY, start, end, label))
    state.now = end
    state.cycle_used += hours
    # A non-driving period of 30+ min also satisfies the 30-minute break rule.
    if hours >= BREAK_HOURS - EPS:
        state.drive_since_break = 0.0
    _add_stop(state, stop_type, label, geometry, total_miles)


def _take_break(state: _State, geometry: list, total_miles: float) -> None:
    start = state.now
    end = start + timedelta(hours=BREAK_HOURS)
    state.segments.append(_Segment(OFF_DUTY, start, end, "30-minute break"))
    state.now = end
    state.drive_since_break = 0.0  # break does NOT reset the 11h/14h limits
    _add_stop(state, "break", "30-minute break", geometry, total_miles)


def _take_rest(state: _State, geometry: list, total_miles: float) -> None:
    start = state.now
    end = start + timedelta(hours=DAILY_RESET_HOURS)
    state.segments.append(_Segment(SLEEPER, start, end, "10-hour rest"))
    state.now = end
    state.drive_in_window = 0.0
    state.drive_since_break = 0.0
    state.window_start = None  # a fresh 14h window starts on next on-duty activity
    _add_stop(state, "rest", "10-hour rest", geometry, total_miles)


def _take_restart(state: _State, geometry: list, total_miles: float) -> None:
    start = state.now
    end = start + timedelta(hours=RESTART_HOURS)
    state.segments.append(_Segment(OFF_DUTY, start, end, "34-hour restart"))
    state.now = end
    state.cycle_used = 0.0
    state.drive_in_window = 0.0
    state.drive_since_break = 0.0
    state.window_start = None
    _add_stop(state, "restart", "34-hour restart", geometry, total_miles)


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------
def _drive_leg(state: _State, leg: Leg, geometry: list, total_miles: float) -> None:
    """Consume one driving leg, inserting fuel/break/rest/restart as required."""
    remaining = leg.duration_hours
    if remaining <= EPS:
        return
    speed = leg.distance_miles / leg.duration_hours  # mph (constant within a leg)

    while remaining > EPS:
        # 1) Cycle exhausted -> 34-hour restart.
        if state.cycle_used >= CYCLE_LIMIT_HOURS - EPS:
            _take_restart(state, geometry, total_miles)
            continue
        # 2) Due to fuel -> fuel stop.
        if state.miles_since_fuel >= FUEL_INTERVAL_MILES - EPS:
            _on_duty(state, FUEL_HOURS, "Fuel stop", "fuel", geometry, total_miles)
            state.miles_since_fuel = 0.0
            continue
        # 3) Out of driving hours or out of window -> 10-hour rest.
        drive_avail = MAX_DRIVE_HOURS - state.drive_in_window
        window_avail = MAX_WINDOW_HOURS - _window_used(state)
        if drive_avail <= EPS or window_avail <= EPS:
            _take_rest(state, geometry, total_miles)
            continue
        # 4) 8 hours of driving since last break -> 30-minute break.
        break_avail = BREAK_AFTER_DRIVE_HOURS - state.drive_since_break
        if break_avail <= EPS:
            _take_break(state, geometry, total_miles)
            continue

        # Drive until the soonest of: leg end, any limit, or the next fuel point.
        chunk = min(
            remaining,
            drive_avail,
            window_avail,
            break_avail,
            CYCLE_LIMIT_HOURS - state.cycle_used,
        )
        if speed > 0:
            chunk = min(chunk, (FUEL_INTERVAL_MILES - state.miles_since_fuel) / speed)
        if chunk <= EPS:
            _take_rest(state, geometry, total_miles)  # safety valve
            continue

        _drive(state, chunk, chunk * speed)
        remaining -= chunk


def plan_logs(legs: list[Leg], geometry: list, current_cycle_used: float = 0.0,
              start_time: datetime | None = None) -> dict:
    """Simulate the trip and return ``{total_*, stops, days}``.

    ``legs`` are the driving legs in order (current->pickup, pickup->dropoff).
    A 1-hour pickup is inserted after the first leg and a 1-hour dropoff after
    the last leg.
    """
    if start_time is None:
        start_time = datetime.now().replace(
            hour=DEFAULT_START_HOUR, minute=0, second=0, microsecond=0
        )

    total_miles = sum(leg.distance_miles for leg in legs)
    state = _State(now=start_time, cycle_used=float(current_cycle_used))

    last_index = len(legs) - 1
    for i, leg in enumerate(legs):
        _drive_leg(state, leg, geometry, total_miles)
        if i == 0 and len(legs) > 1:
            _on_duty(state, PICKUP_HOURS, "Pickup", "pickup", geometry, total_miles)
        if i == last_index:
            _on_duty(state, DROPOFF_HOURS, "Dropoff", "dropoff", geometry, total_miles)

    return {
        "total_distance_miles": round(total_miles, 1),
        "total_drive_hours": round(sum(leg.duration_hours for leg in legs), 2),
        "stops": state.stops,
        "days": _split_into_days(state.segments),
    }


# ---------------------------------------------------------------------------
# Split the continuous timeline into per-day log sheets.
# ---------------------------------------------------------------------------
def _midnight(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _hour_of(dt: datetime, day: datetime) -> float:
    """Hour-of-day (0..24) of ``dt`` relative to ``day``'s midnight."""
    if dt.date() > day.date():
        return 24.0
    return dt.hour + dt.minute / 60.0 + dt.second / 3600.0


def _split_at_midnight(seg: _Segment) -> list[_Segment]:
    out: list[_Segment] = []
    cursor = seg.start
    total = (seg.end - seg.start).total_seconds()
    while cursor < seg.end:
        next_midnight = _midnight(cursor) + timedelta(days=1)
        end = min(seg.end, next_midnight)
        frac = 1.0 if total <= 0 else (end - cursor).total_seconds() / total
        out.append(_Segment(seg.status, cursor, end, seg.label, seg.miles * frac))
        cursor = end
    return out


def _split_into_days(segments: list[_Segment]) -> list[dict]:
    """Pad to whole days, split at midnight, and group into log-sheet days."""
    if not segments:
        return []

    # Pad the head (midnight -> first activity) and tail (last activity -> midnight)
    # with off-duty so every day sums to a full 24 hours.
    first_start = segments[0].start
    last_end = segments[-1].end
    padded: list[_Segment] = []
    if first_start > _midnight(first_start):
        padded.append(_Segment(OFF_DUTY, _midnight(first_start), first_start))
    padded.extend(segments)
    tail_midnight = _midnight(last_end) + timedelta(days=1)
    if last_end < tail_midnight:
        padded.append(_Segment(OFF_DUTY, last_end, tail_midnight))

    # Split any segment that crosses midnight, then group by calendar day.
    by_day: dict = {}
    order: list = []
    for seg in padded:
        for piece in _split_at_midnight(seg):
            key = piece.start.date()
            if key not in by_day:
                by_day[key] = []
                order.append(key)
            by_day[key].append(piece)

    days = []
    for key in order:
        day_segs = by_day[key]
        day_dt = datetime(key.year, key.month, key.day)
        totals = {OFF_DUTY: 0.0, SLEEPER: 0.0, DRIVING: 0.0, ON_DUTY: 0.0}
        out_segments = []
        remarks = []
        driving_miles = 0.0
        for seg in day_segs:
            hours = (seg.end - seg.start).total_seconds() / 3600.0
            totals[seg.status] += hours
            if seg.status == DRIVING:
                driving_miles += seg.miles
            out_segments.append(
                {
                    "status": seg.status,
                    "start_hour": round(_hour_of(seg.start, day_dt), 4),
                    "end_hour": round(_hour_of(seg.end, day_dt), 4),
                    "label": seg.label,
                }
            )
            if seg.label:
                remarks.append({"time": seg.start.strftime("%H:%M"), "label": seg.label})

        days.append(
            {
                "date": key.isoformat(),
                "segments": out_segments,
                "totals": {k: round(v, 2) for k, v in totals.items()},
                "driving_miles": round(driving_miles, 1),
                "remarks": remarks,
            }
        )
    return days
