"""Routing via the OpenRouteService Directions API.

Prefers the configured heavy-goods-vehicle profile so the route reflects
truck-legal roads. Some ORS keys/regions return 404 for that profile, so the
service can fall back to a configured profile to keep the planner usable.
Returns the full geometry (for the map polyline) plus per-leg distance/duration,
which the HOS engine consumes.
"""
from __future__ import annotations

from dataclasses import dataclass

import requests
from django.conf import settings

from .hos import Leg

METERS_PER_MILE = 1609.344


class RoutingError(Exception):
    """Raised when a route cannot be computed."""


def _response_detail(resp: requests.Response | None) -> str:
    if resp is None:
        return ""
    try:
        data = resp.json()
    except ValueError:
        return resp.text.strip()

    error = data.get("error") if isinstance(data, dict) else None
    if isinstance(error, dict):
        return str(error.get("message") or error.get("code") or "")
    if isinstance(error, str):
        return error
    return str(data.get("message") or "") if isinstance(data, dict) else ""


def _routing_error(exc: requests.RequestException) -> RoutingError:
    resp = getattr(exc, "response", None)
    detail = _response_detail(resp)
    if getattr(resp, "status_code", None) == 404:
        message = (
            "No route found for one of the selected points. Try choosing a "
            "more specific street address or a city center that is on a public road."
        )
        if detail:
            message = f"{message} ORS detail: {detail}"
        return RoutingError(message)
    if detail:
        return RoutingError(f"Routing request failed: {detail}")
    return RoutingError(f"Routing request failed: {exc}")


@dataclass
class RouteResult:
    distance_miles: float
    duration_hours: float
    geometry: list  # list of [lon, lat] pairs
    legs: list[Leg]  # one Leg per consecutive pair of waypoints


def route(waypoints: list[tuple[float, float]]) -> RouteResult:
    """Route through ``waypoints`` (each ``(lat, lon)``)."""
    if not settings.ORS_API_KEY:
        raise RoutingError("ORS_API_KEY is not configured")

    profiles = [
        settings.ORS_ROUTING_PROFILE,
        *settings.ORS_FALLBACK_ROUTING_PROFILES,
    ]
    profiles = list(dict.fromkeys(profile for profile in profiles if profile))
    body = {"coordinates": [[lon, lat] for (lat, lon) in waypoints]}
    headers = {
        "Authorization": settings.ORS_API_KEY,
        "Content-Type": "application/json",
    }
    last_exc: requests.RequestException | None = None
    resp = None
    for index, profile in enumerate(profiles):
        url = f"{settings.ORS_BASE_URL}/v2/directions/{profile}/geojson"
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=30)
            if resp.status_code == 404 and index < len(profiles) - 1:
                continue
            resp.raise_for_status()
            break
        except requests.RequestException as exc:
            last_exc = exc
            if getattr(getattr(exc, "response", None), "status_code", None) == 404 and index < len(profiles) - 1:
                continue
            raise _routing_error(exc) from exc
    else:
        if last_exc is not None:
            raise _routing_error(last_exc) from last_exc
        raise RoutingError("No routing profiles are configured")

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
