"""Geocoding via the OpenRouteService (Pelias) `/geocode/search` endpoint.

Turns a free-text location string ("Dallas, TX") into coordinates so the
routing engine can build a route. Kept tiny and side-effect free apart from the
HTTP call so it is easy to mock in tests.
"""
from __future__ import annotations

import requests
from django.conf import settings


class GeocodingError(Exception):
    """Raised when a location cannot be resolved to coordinates."""


def geocode(query: str) -> tuple[float, float, str]:
    """Resolve ``query`` to ``(lat, lon, label)``.

    ``label`` is the human-readable address ORS matched, useful for the UI.
    """
    if not settings.ORS_API_KEY:
        raise GeocodingError("ORS_API_KEY is not configured")

    url = f"{settings.ORS_BASE_URL}/geocode/search"
    try:
        resp = requests.get(
            url,
            params={"api_key": settings.ORS_API_KEY, "text": query, "size": 1},
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:  # network/HTTP error
        raise GeocodingError(f"Geocoding request failed: {exc}") from exc

    features = (resp.json() or {}).get("features") or []
    if not features:
        raise GeocodingError(f"No location found for '{query}'")

    lon, lat = features[0]["geometry"]["coordinates"][:2]
    label = features[0].get("properties", {}).get("label", query)
    return (lat, lon, label)
