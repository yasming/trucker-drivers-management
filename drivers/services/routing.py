"""Truck routing via the OpenRouteService Directions API.

Uses the ``driving-hgv`` (heavy goods vehicle) profile so the route reflects
truck-legal roads. Returns the full geometry (for the map polyline) plus
per-leg distance/duration, which the HOS engine consumes.
"""
from __future__ import annotations

from dataclasses import dataclass

import requests
from django.conf import settings

from .hos import Leg

METERS_PER_MILE = 1609.344


class RoutingError(Exception):
    """Raised when a route cannot be computed."""


@dataclass
class RouteResult:
    distance_miles: float
    duration_hours: float
    geometry: list  # list of [lon, lat] pairs
    legs: list[Leg]  # one Leg per consecutive pair of waypoints


def route(waypoints: list[tuple[float, float]]) -> RouteResult:
    """Route through ``waypoints`` (each ``(lat, lon)``) with the truck profile."""
    if not settings.ORS_API_KEY:
        raise RoutingError("ORS_API_KEY is not configured")

    url = f"{settings.ORS_BASE_URL}/v2/directions/driving-hgv/geojson"
    body = {"coordinates": [[lon, lat] for (lat, lon) in waypoints]}
    headers = {
        "Authorization": settings.ORS_API_KEY,
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(url, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RoutingError(f"Routing request failed: {exc}") from exc

    features = (resp.json() or {}).get("features") or []
    if not features:
        raise RoutingError("No route found between the given locations")

    feature = features[0]
    geometry = feature["geometry"]["coordinates"]
    props = feature.get("properties", {})
    summary = props.get("summary", {})
    legs = [
        Leg(
            distance_miles=seg.get("distance", 0.0) / METERS_PER_MILE,
            duration_hours=seg.get("duration", 0.0) / 3600.0,
        )
        for seg in props.get("segments", [])
    ]
    return RouteResult(
        distance_miles=summary.get("distance", 0.0) / METERS_PER_MILE,
        duration_hours=summary.get("duration", 0.0) / 3600.0,
        geometry=geometry,
        legs=legs,
    )
