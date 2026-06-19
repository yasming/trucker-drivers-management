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


def search(query: str, limit: int = 5) -> list[tuple[float, float, str]]:
    """Search for locations matching ``query``, return up to ``limit`` results.

    Each result is ``(lat, lon, label)``.
    """
    if not settings.ORS_API_KEY:
        raise GeocodingError("ORS_API_KEY is not configured")

    url = f"{settings.ORS_BASE_URL}/geocode/search"
    try:
        resp = requests.get(
            url,
            params={"api_key": settings.ORS_API_KEY, "text": query, "size": limit},
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise GeocodingError(f"Geocoding request failed: {exc}") from exc

    features = (resp.json() or {}).get("features") or []
    return [
        (f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0],
         f.get("properties", {}).get("label", query))
        for f in features
    ]


def geocode(query: str) -> tuple[float, float, str]:
    """Resolve ``query`` to ``(lat, lon, label)``.

    ``label`` is the human-readable address ORS matched, useful for the UI.
    Returns the single best result.
    """
    results = search(query, limit=1)
    if not results:
        raise GeocodingError(f"No location found for '{query}'")
    return results[0]
