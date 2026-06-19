"""In-memory storage for planned trips.

The assessment app only needs trips for the lifetime of the running process.
Keeping them here avoids requiring SQLite or migrations for normal use.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import count
from threading import Lock

from django.utils import timezone

_lock = Lock()
_next_id = count(1)
_trips: dict[int, dict] = {}


def create_trip(data: dict) -> dict:
    with _lock:
        trip = {
            "id": next(_next_id),
            "created_at": timezone.now(),
            **deepcopy(data),
        }
        _trips[trip["id"]] = trip
        return deepcopy(trip)


def list_trips() -> list[dict]:
    with _lock:
        return [
            deepcopy(trip)
            for trip in sorted(
                _trips.values(),
                key=lambda item: item["created_at"],
                reverse=True,
            )
        ]


def get_trip(trip_id: int) -> dict | None:
    with _lock:
        trip = _trips.get(trip_id)
        return deepcopy(trip) if trip else None


def delete_trip(trip_id: int) -> bool:
    with _lock:
        return _trips.pop(trip_id, None) is not None


def clear_trips() -> None:
    with _lock:
        _trips.clear()
