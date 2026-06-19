"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
import os
from django.conf import settings
from django.http import JsonResponse, FileResponse
from django.urls import include, path, re_path
from django.views.static import serve

from drivers.services import geocoding as geocoding_service


def health(request):
    return JsonResponse({"status": "ok"})


def geocode(request):
    query = request.GET.get("query", "").strip()
    if not query:
        return JsonResponse({"results": []})
    try:
        results = geocoding_service.search(query, limit=5)
        return JsonResponse(
            {"results": [{"lat": lat, "lon": lon, "label": label} for lat, lon, label in results]}
        )
    except geocoding_service.GeocodingError as e:
        return JsonResponse({"error": str(e), "results": []}, status=400)


def spa_fallback(request):
    """Serve React's index.html for any non-API route (SPA client-side routing)."""
    index_path = os.path.join(os.path.dirname(__file__), '../static/index.html')
    if os.path.exists(index_path):
        return FileResponse(open(index_path, 'rb'), content_type='text/html')
    return JsonResponse({'error': 'Frontend not built'}, status=404)


urlpatterns = [
    path('api/health/', health, name='health'),
    path('api/geocode/', geocode, name='geocode'),
    path('api/', include('drivers.urls')),
    # Serve the built React assets (works with DEBUG on or off, since this is
    # the single deployable unit that serves its own frontend).
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.FRONTEND_BUILD_DIR}),
    # Catch-all: serve React's index.html for client-side routing (must be last).
    re_path(r'^(?!api|static).*$', spa_fallback, name='spa_fallback'),
]
